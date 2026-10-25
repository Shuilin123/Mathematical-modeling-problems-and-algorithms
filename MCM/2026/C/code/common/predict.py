# -*- coding: utf-8 -*-
"""负荷/光伏预测：9 个候选模型 + 滚动回测选型 + 全年预计算。

所有模型只使用第 i 天之前（不含第 i 天）的实际数据——计划在每天 0:00 制定。
选型结论（表 2）：负荷用梯度提升树 gbdt，光伏用气候学型 ma7_ratio。
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

N_DAY = 365
REL_H = [0, 6, 12, 18]      # 附件3 的 4 个预报发布时刻
W_FC = 0.358                # 附件3 预报的最优融合权重


# ---------------- 候选模型（返回第 i 天的 144 点预测） ----------------
def m_persist(Y, i, **kw):
    return Y[i - 1].copy()


def m_ma3(Y, i, **kw):
    return Y[i - 3:i].mean(0)


def m_ma7(Y, i, **kw):
    return Y[i - 7:i].mean(0)


def m_week(Y, i, **kw):
    """同星期几前 4 周均值。"""
    return Y[[i - 7 * k for k in (1, 2, 3, 4)]].mean(0)


def m_es(Y, i, alpha=0.6, **kw):
    """对同一时段的历史序列做一次指数平滑。"""
    s = Y[0].copy()
    for j in range(1, i):
        s = alpha * Y[j] + (1 - alpha) * s
    return s


def m_ma7_shape(Y, i, **kw):
    """7 日平均 + 日电量归一化形状。"""
    win = Y[i - 7:i]
    tot = win.sum(1)
    tot[tot <= 0] = 1.0
    return (win / tot[:, None]).mean(0) * tot.mean()


def m_ma7_ratio(Y, i, **kw):
    """7 日均值 x 近 3 日/近 7 日电量比（截断于 [0.85,1.15]）——光伏最优模型。"""
    base = m_ma7(Y, i)
    r3 = Y[i - 3:i].sum(1).mean()
    r7 = Y[i - 7:i].sum(1).mean()
    return base * np.clip(r3 / max(r7, 1e-6), 0.85, 1.15)


def _feat(Y, j):
    """第 j 天的特征矩阵（144 x 12）：时刻编码 + 年/星期编码 + 滞后 1/2/3/7 日。"""
    tt = np.arange(144)
    doy = 2 * np.pi * j / 365.0
    return np.vstack([tt / 144.0, np.sin(2 * np.pi * tt / 144),
                      np.cos(2 * np.pi * tt / 144),
                      np.full(144, np.sin(doy)), np.full(144, np.cos(doy)),
                      np.full(144, (j % 7) / 7.0),
                      np.full(144, Y[j - 1].mean()),
                      np.full(144, Y[max(0, j - 7):j].mean()),
                      Y[j - 1], Y[j - 2], Y[j - 3], Y[j - 7]]).T


def m_gbdt(Y, i, model_cache=None, **kw):
    """梯度提升树，每 30 天滚动重训一次——负荷最优模型。"""
    bucket = (i - 3) // 30
    if model_cache is not None and bucket in model_cache:
        mdl = model_cache[bucket]
    else:
        X = np.vstack([_feat(Y, j) for j in range(3, i)])
        y = np.concatenate([Y[j] for j in range(3, i)])
        mdl = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08,
                                            max_depth=6, min_samples_leaf=40,
                                            random_state=0).fit(X, y)
        if model_cache is not None:
            model_cache[bucket] = mdl
    return np.maximum(mdl.predict(_feat(Y, i)), 0.0)


def m_combo(Y, i, **kw):
    """统计模型与 GBDT 的等权组合。"""
    return 0.5 * m_ma7_shape(Y, i) + 0.5 * m_gbdt(Y, i, **kw)


CANDIDATES = {"persist": m_persist, "ma3": m_ma3, "ma7": m_ma7, "week": m_week,
              "es": m_es, "ma7_shape": m_ma7_shape, "ma7_ratio": m_ma7_ratio,
              "gbdt": m_gbdt, "combo": m_combo}


# ---------------- 回测选型 ----------------
def backtest(Y, names=None, start=31, mask=None):
    """滚动回测，返回 {模型: (MAE, MAPE, RMSE)}。

    MAE  : 时段平均绝对误差 / kW
    MAPE : 逐日 (Σ|误差| / Σ实际) 的平均值
    RMSE : 时段均方根误差 / kW
    """
    out = {}
    for nm in names or list(CANDIDATES):
        cache = {}
        ae = se = ape = 0.0
        n = nd = 0
        for i in range(start, N_DAY):
            pred = np.maximum(CANDIDATES[nm](Y, i, model_cache=cache), 0.0)
            m = np.ones(144, bool) if mask is None else mask(Y[i])
            if m.sum() == 0:
                continue
            d = pred[m] - Y[i][m]
            ae += np.abs(d).sum()
            se += (d ** 2).sum()
            ape += np.abs(d).sum() / max(Y[i][m].sum(), 1e-6)
            n += m.sum()
            nd += 1
        out[nm] = (ae / n, ape / nd, np.sqrt(se / n))
    return out


# ---------------- 附件3 预报的时钟对齐与降尺度 ----------------
def ds_release(fh, h0):
    """发布时刻 h0 的 24 个整点预报 -> 144 个 10min 序列（按时钟线性插值）。

    fh[k] 对应时刻 (h0+k+1):00；0:00 取 0。附件3 的 `预报k小时` 经校验为整点点值。
    """
    xs = np.concatenate([[0.0], [(h0 + k + 1) * 60.0 for k in range(24)]])
    ys = np.concatenate([[0.0], fh])
    return np.interp(np.arange(1, 145) * 10.0, xs, ys)


def build_all(force=False):
    """全年预测量：负荷预测、光伏历史统计预测、附件3 降尺度预报（带缓存）。"""
    from common import dataio as D
    import json

    path = D.OUT / "pred.npz"
    if path.exists() and not force:
        z = np.load(path)
        return dict(load_pred=z["load_pred"], pv_hist=z["pv_hist"],
                    pv_fc=z["pv_fc"], load_actual=z["load_actual"],
                    pv_actual=z["pv_actual"])

    L, P = D.load_year()
    F = D.load_pv_forecast()

    print("[预测] 负荷回测（2025-02-01 起 334 天）…")
    rl = backtest(L)
    print("       最优：%s（MAE %.1f kW）" % (min(rl, key=lambda k: rl[k][0]),
                                             min(v[0] for v in rl.values())))
    print("[预测] 光伏回测（白天时段）…")
    rp = backtest(P, mask=lambda a: a > 0.05 * P.mean())
    print("       最优：%s（MAE %.1f kW）" % (min(rp, key=lambda k: rp[k][0]),
                                             min(v[0] for v in rp.values())))

    load_pred = np.zeros((N_DAY, 144))
    cache = {}
    for i in range(N_DAY):
        if i < 8:
            load_pred[i] = L[max(0, i - 3):i].mean(0) if i > 0 else L[0]
        else:
            load_pred[i] = np.maximum(m_gbdt(L, i, model_cache=cache), 0.0)
    pv_hist = np.zeros((N_DAY, 144))
    for i in range(N_DAY):
        pv_hist[i] = (np.maximum(m_ma7_ratio(P, i), 0.0) if i >= 8
                      else P[i - 1 if i > 0 else 0])
    pv_fc = np.zeros((N_DAY, 4, 144))
    for i in range(N_DAY):
        for k in range(4):
            pv_fc[i, k] = np.maximum(ds_release(F[i, k], REL_H[k]), 0.0)

    np.savez(path, load_pred=load_pred, pv_hist=pv_hist, pv_fc=pv_fc,
             load_actual=L, pv_actual=P)
    json.dump({k: list(v) for k, v in rl.items()},
              open(D.OUT / "backtest_load.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({k: list(v) for k, v in rp.items()},
              open(D.OUT / "backtest_pv.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return dict(load_pred=load_pred, pv_hist=pv_hist, pv_fc=pv_fc,
                load_actual=L, pv_actual=P)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # 使 code/ 可导入
    from common import dataio as D
    L, P = D.load_year()
    print("=== 负荷回测 ===")
    for k, v in sorted(backtest(L).items(), key=lambda x: x[1][0]):
        print("  %-10s MAE=%7.1f kW  MAPE=%6.2f%%  RMSE=%7.1f" % (k, v[0], v[1] * 100, v[2]))
    print("=== 光伏回测（白天）===")
    for k, v in sorted(backtest(P, mask=lambda a: a > 0.05 * P.mean()).items(),
                       key=lambda x: x[1][0]):
        print("  %-10s MAE=%7.1f kW  MAPE=%6.2f%%  RMSE=%7.1f" % (k, v[0], v[1] * 100, v[2]))
