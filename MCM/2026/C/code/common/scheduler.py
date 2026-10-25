# -*- coding: utf-8 -*-
"""日滚动调度框架：预测 → 两阶段随机规划 → 执行结算 → 结转储电量。

problem2（0:00 一次计划）、problem3（0:00 + 6/12/18 时修正）、
problem4（波动电价下重算问题 2、3）都调用本模块的 simulate()。
"""
import json

import numpy as np

from common import dataio as D
from common import model as M

DT = D.DT
DAY0, NDAY = 31, 365          # 2025-02-01 起，共 334 天
REL_H = [0, 6, 12, 18]
WIN = 21                      # 误差场景窗口（天）
SCALE = [1.0, 0.70, 0.50, 0.32]   # 各发布时刻光伏误差场景的缩放


def pv_used(P, i, k, mode, pv_hist=None, pv_fc=None):
    """第 i 天、第 k 次发布时采用的光伏预测。

    mode='hist'：仅用附件2 的历史统计预测（问题2）；
    mode='fc'  ：附件3 预报与历史统计按 w=0.358 融合（问题3/4）。
    """
    if mode == "hist":
        return pv_hist[i].copy()
    base = pv_hist[i]
    out = 0.358 * pv_fc[i, k] + (1 - 0.358) * base
    if k > 0:                              # 发布时刻以前沿用 0:00 的融合值
        h0 = REL_H[k] * 6
        out[:h0] = (0.358 * pv_fc[i, 0] + (1 - 0.358) * base)[:h0]
    return out


def simulate(price_mat, mode="hist", revisions=(0,), hedge=True, k_add=5.0,
             days=range(DAY0, NDAY), perfect=False, win=WIN, Q_init=None,
             term="ge"):
    """全年滚动仿真。term='ge' 要求 Q_144>=Q_0（可持续），'free' 为不约束末端。

    返回 rec（逐日明细）与各决策量的 (天数,144) 数组。
    """
    z = np.load(D.OUT / "pred.npz") if (D.OUT / "pred.npz").exists() else None
    if z is None:
        from common import predict as P
        d = P.build_all()
        load_pred, pv_hist, pv_fc = d["load_pred"], d["pv_hist"], d["pv_fc"]
        L, P_act = d["load_actual"], d["pv_actual"]
    else:
        load_pred, pv_hist, pv_fc = z["load_pred"], z["pv_hist"], z["pv_fc"]
        L, P_act = z["load_actual"], z["pv_actual"]

    el = L - load_pred                                       # 负荷预测误差样本
    if mode == "hist":
        ep = P_act - pv_hist
    else:
        ep = P_act - np.array([pv_used(P_act, i, 0, mode, pv_hist, pv_fc)
                               for i in range(NDAY)])

    days = list(days)
    nd = len(days)
    plan_g = np.zeros((nd, 144))
    adj_g = np.zeros((nd, 144))
    ch_out = np.zeros((nd, 144))
    dis_out = np.zeros((nd, 144))
    add_out = np.zeros((nd, 144))
    cur_out = np.zeros((nd, 144))
    q_out = np.zeros((nd, 145))
    Q = D.E_INIT if Q_init is None else float(Q_init)
    rec = []

    for idx, i in enumerate(days):
        price = price_mat[i]
        Q0 = Q
        end = Q0 if term == "ge" else None
        lp = (L[i] if perfect else load_pred[i]).copy()
        pv = P_act[i] if perfect else pv_used(P_act, i, 0, mode, pv_hist, pv_fc)
        if perfect or not hedge:
            scene = (np.zeros((1, 144)), np.zeros((1, 144)))
        else:
            a = max(0, i - win)
            scene = (el[a:i], ep[a:i])

        # ---- 0:00 计划（两阶段随机规划） ----
        r0 = M.solve_scen(price, lp, pv, Q0, scene[0], scene[1], start=0,
                          E_end_min=end, k_add=k_add)
        gp = r0["g"].copy()
        cur_g, cur_ch, cur_dis = gp.copy(), r0["ch"].copy(), r0["dis"].copy()

        # ---- 6:00 / 12:00 / 18:00 滚动修正 ----
        for k in revisions[1:]:
            t0 = REL_H[k] * 6
            if t0 >= 144:
                continue
            kk = float(np.clip(L[i, :t0].sum() / max(lp[:t0].sum(), 1e-6), 0.85, 1.15))
            lp2 = lp.copy()
            lp2[t0:] = lp[t0:] * kk                          # 负荷误差修正
            pv2 = (P_act[i] if perfect
                   else pv_used(P_act, i, k, mode, pv_hist, pv_fc))
            QQ = Q0 + ((D.ETA * cur_ch[:t0] - cur_dis[:t0] / D.ETA) * DT).sum()
            s_l = scene[0] - scene[0].mean()                  # 去均值
            s_p = (scene[1] - scene[1].mean()) * SCALE[k]     # 按预报精度缩放
            r = M.solve_scen(price, lp2, pv2, QQ, s_l, s_p, start=t0,
                             plan=gp, E_end_min=end, k_add=k_add)
            cur_g[t0:] = r["g"][t0:]
            cur_ch[t0:] = r["ch"][t0:]
            cur_dis[t0:] = r["dis"][t0:]

        # ---- 执行与结算 ----
        Qs = np.zeros(145)
        Qs[0] = Q0
        for t in range(144):
            Qs[t + 1] = Qs[t] + (D.ETA * cur_ch[t] - cur_dis[t] / D.ETA) * DT
        Q = Qs[144]
        sup = P_act[i] + cur_dis - cur_ch + cur_g
        add = np.maximum(L[i] - sup, 0.0)                    # 紧急购电
        cur = np.maximum(sup - L[i], 0.0)                    # 富余（弃用）
        low = np.minimum(cur_g, gp)
        high = np.maximum(cur_g - gp, 0.0)
        cost_pur = (price * low + 0.5 * price * (gp - low)
                    + 1.5 * price * high).sum() * DT         # 分段电价
        cost_plan = (price * gp).sum() * DT
        cost_em = (k_add * price * add).sum() * DT

        plan_g[idx], adj_g[idx] = gp, cur_g
        ch_out[idx], dis_out[idx] = cur_ch, cur_dis
        add_out[idx], cur_out[idx], q_out[idx] = add, cur, Qs
        rec.append(dict(idx=idx, day=int(i),
                        date=str(np.datetime64("2025-01-01")
                                 + np.timedelta64(int(i), "D")),
                        plan_kwh=float(gp.sum() * DT),
                        adj_kwh=float(cur_g.sum() * DT),
                        ch_kwh=float(cur_ch.sum() * DT),
                        dis_kwh=float(cur_dis.sum() * DT),
                        add_kwh=float(add.sum() * DT),
                        cur_kwh=float(cur.sum() * DT),
                        cost_plan=float(cost_plan), cost_pur=float(cost_pur),
                        cost_em=float(cost_em), cost=float(cost_pur + cost_em),
                        q0=float(Q0), q24=float(Q)))
        if idx % 60 == 0:
            print("    %s  当日费用 %.0f 元，紧急购电 %.0f kWh"
                  % (rec[-1]["date"], rec[-1]["cost"], rec[-1]["add_kwh"]))

    return dict(rec=rec, plan_g=plan_g, adj_g=adj_g, ch=ch_out, dis=dis_out,
                add=add_out, cur=cur_out, q=q_out, days=np.array(days))


def summarize(res, tag=""):
    """汇总全年指标并打印。"""
    rec = res["rec"]
    nd = len(rec)
    tot = sum(r["cost"] for r in rec)
    cp = sum(r["cost_plan"] for r in rec)
    cpur = sum(r["cost_pur"] for r in rec)
    cem = sum(r["cost_em"] for r in rec)
    out = dict(tag=tag, days=nd, total_cost=tot, cost_plan=cp,
               cost_adjust_extra=cpur - cp, cost_purchase=cpur,
               cost_emergency=cem,
               energy_plan=sum(r["plan_kwh"] for r in rec),
               energy_adj=sum(r["adj_kwh"] for r in rec),
               energy_add=sum(r["add_kwh"] for r in rec),
               energy_cur=sum(r["cur_kwh"] for r in rec),
               energy_ch=sum(r["ch_kwh"] for r in rec),
               energy_dis=sum(r["dis_kwh"] for r in rec),
               avg_day_cost=tot / nd)
    if tag:
        print("[%s] %d 天：总费用 %.2f 元 = 计划 %.2f + 调整附加 %.2f + 紧急 %.2f"
              % (tag, nd, tot, cp, cpur - cp, cem))
        print("        计划购电 %.0f kWh，紧急 %.0f kWh，富余 %.0f kWh，充电 %.0f，"
              "放电 %.0f，日均 %.2f 元"
              % (out["energy_plan"], out["energy_add"], out["energy_cur"],
                 out["energy_ch"], out["energy_dis"], tot / nd))
    return out


def save(res, name):
    """把决策量存入 out/<name>.npz、逐日明细存入 out/<name>_rec.json。"""
    np.savez(D.OUT / f"{name}.npz",
             plan_g=res["plan_g"], adj_g=res["adj_g"], ch=res["ch"],
             dis=res["dis"], add=res["add"], cur=res["cur"], q=res["q"])
    with open(D.OUT / f"{name}_rec.json", "w", encoding="utf-8") as f:
        json.dump(res["rec"], f, ensure_ascii=False)


KEY_DATES = ["2025-03-20", "2025-06-21", "2025-09-23", "2025-12-21"]


def print_key_dates(res, use_adj=False):
    """打印题目要求列出的 4 个日期的主要结果。"""
    rec = {r["date"]: r for r in res["rec"]}
    print("\n指定日期的结果：")
    for d in KEY_DATES:
        r = rec[d]
        extra = ("，执行购电 %.1f kWh，调整附加 %.1f 元"
                 % (r["adj_kwh"], r["cost_pur"] - r["cost_plan"])) if use_adj else ""
        print("  %s  计划购电 %8.1f kWh，紧急购电 %7.1f kWh，当日费用 %9.2f 元%s"
              % (d, r["plan_kwh"], r["add_kwh"], r["cost"], extra))
