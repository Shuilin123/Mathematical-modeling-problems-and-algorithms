# -*- coding: utf-8 -*-
"""微网调度核心优化模型（混合整数线性规划，HiGHS 求解）。

统一记号：
    t = 1..144  第 t 个 10min 时段，dt = 1/6 h
    P_grid  计划购电功率 kW    P_ch 充电功率 kW    P_dis 放电功率 kW
    P_add   紧急购电功率 kW    P_cur 弃光功率 kW    Q   储电量 kWh
    eta = 0.90 充/放电效率

基础模型：
    min  sum_t C_t * dt * (P_grid,t + k_add * P_add,t)
    s.t. P_pv,t - P_cur,t + P_dis,t - P_ch,t + P_grid,t + P_add,t = P_load,t
         Q_t = Q_{t-1} + (eta*P_ch,t - P_dis,t/eta) * dt
         0 <= P_ch,t <= Pmax*x_t ,  0 <= P_dis,t <= Pmax*(1-x_t),  x_t in {0,1}
         0 <= P_cur,t <= P_pv,t ,  P_grid,t >= 0 ,  P_add,t >= 0
         Emin <= Q_t <= Emax ,  Q_0 给定 ,  Q_144 >= Q_0 (可持续)
问题3 的调整模型把 P_grid,t 的线性计价换成对计划量的分段计价。
"""
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog, milp, LinearConstraint, Bounds

DT = 1.0 / 6.0
P_MAX = 5000.0
E_MIN = 1200.0
E_CAP = 10800.0
ETA = 0.90
EPS = 1e-4          # 充放电量正则项（仅用于消除多重最优解，元/kWh）

BLK = ("lo", "hi", "ch", "dis", "add", "cur", "Q")


def _idx(n):
    return dict(lo=0, hi=n, ch=2 * n, dis=3 * n, add=4 * n, cur=5 * n, Q=6 * n)


def _build(n, Q_start, price, load, pv, plan, E_end_min, k_add,
           k_lo=1.0, k_hi=1.0, E_end_eq=False):
    I = _idx(n)
    nv = 6 * n + (n + 1)
    c = np.zeros(nv)
    c[I["lo"]:I["lo"] + n] = price * DT * k_lo
    c[I["hi"]:I["hi"] + n] = price * DT * k_hi
    c[I["add"]:I["add"] + n] = price * DT * k_add

    rows, cols, vals = [], [], []
    for t in range(n):
        # 功率平衡
        r = t
        for j, v in ((I["ch"], -1.0), (I["dis"], 1.0), (I["lo"], 1.0),
                     (I["hi"], 1.0), (I["add"], 1.0), (I["cur"], -1.0)):
            rows.append(r); cols.append(j + t); vals.append(v)
        # 电量递推
        r = n + t
        for j, v in ((I["Q"] + t + 1, 1.0), (I["Q"] + t, -1.0),
                     (I["ch"] + t, -ETA * DT), (I["dis"] + t, DT / ETA)):
            rows.append(r); cols.append(j); vals.append(v)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(2 * n, nv))
    b = np.concatenate([load - pv, np.zeros(n)])

    lb = np.zeros(nv)
    ub = np.full(nv, np.inf)
    ub[I["lo"]:I["lo"] + n] = np.inf if plan is None else plan
    if plan is None:
        ub[I["hi"]:I["hi"] + n] = 0.0
    ub[I["ch"]:I["ch"] + n] = P_MAX
    ub[I["dis"]:I["dis"] + n] = P_MAX
    ub[I["cur"]:I["cur"] + n] = np.maximum(pv, 0.0)
    lb[I["Q"]:I["Q"] + n + 1] = E_MIN
    ub[I["Q"]:I["Q"] + n + 1] = E_CAP
    lb[I["Q"]] = ub[I["Q"]] = Q_start
    if E_end_min is not None:
        lb[I["Q"] + n] = max(E_MIN, E_end_min)
        if E_end_eq:
            ub[I["Q"] + n] = max(E_MIN, E_end_min)
    return c, A, b, lb, ub, I


def _pack(x, start, n, I):
    out = {}
    for k in ("ch", "dis", "add", "cur"):
        a = np.full(144, np.nan); a[start:] = x[I[k]:I[k] + n]; out[k] = a
    g = np.full(144, np.nan); g[start:] = x[I["lo"]:I["lo"] + n] + x[I["hi"]:I["hi"] + n]
    Q = np.full(145, np.nan); Q[start:] = x[I["Q"]:I["Q"] + n + 1]
    out["g"] = g
    out["Q"] = Q
    return out


def solve_horizon(price, load, pv, Q_start, start=0, plan=None,
                  E_end_min=None, k_add=5.0, E_end_eq=False):
    """在时段 [start,144) 上求解 LP 松弛。plan 给出时按 0.5/1.5 倍分段计价。"""
    n = 144 - start
    pr = np.asarray(price, float)[start:]
    ld = np.asarray(load, float)[start:]
    pvv = np.asarray(pv, float)[start:]
    pl = None if plan is None else np.asarray(plan, float)[start:]
    k_lo, k_hi = (1.0, 0.0) if plan is None else (0.5, 1.5)
    c, A, b, lb, ub, I = _build(n, Q_start, pr, ld, pvv, pl,
                                E_end_min, k_add, k_lo, k_hi, E_end_eq)
    res = linprog(c, A_eq=A, b_eq=b, bounds=list(zip(lb, ub)), method="highs")
    if not res.success:
        raise RuntimeError("LP infeasible: " + res.message)
    out = _pack(res.x, start, n, I)
    out["cost"] = res.fun
    return out


def solve_horizon_milp(price, load, pv, Q_start, start=0, plan=None,
                       E_end_min=None, k_add=5.0, E_end_eq=False):
    """带 0-1 充放电互斥变量的 MILP（用于检验 LP 松弛的精确性）。"""
    n = 144 - start
    pr = np.asarray(price, float)[start:]
    ld = np.asarray(load, float)[start:]
    pvv = np.asarray(pv, float)[start:]
    pl = None if plan is None else np.asarray(plan, float)[start:]
    k_lo, k_hi = (1.0, 0.0) if plan is None else (0.5, 1.5)
    c, A, b, lb, ub, I = _build(n, Q_start, pr, ld, pvv, pl,
                                E_end_min, k_add, k_lo, k_hi, E_end_eq)
    nv = len(c)
    rows, cols, vals = [], [], []
    for t in range(n):
        rows += [t, t]; cols += [I["ch"] + t, nv + t]; vals += [1.0, -P_MAX]
        rows += [n + t, n + t]; cols += [I["dis"] + t, nv + t]; vals += [1.0, P_MAX]
    A_ub = sp.csr_matrix((vals, (rows, cols)), shape=(2 * n, nv + n))
    A_all = sp.vstack([sp.hstack([A, sp.csr_matrix((2 * n, n))]).tocsr(), A_ub]).tocsr()
    lower = np.concatenate([b, np.full(2 * n, -np.inf)])
    upper = np.concatenate([b, np.zeros(n), np.full(n, P_MAX)])
    lb2 = np.concatenate([lb, np.zeros(n)])
    ub2 = np.concatenate([ub, np.ones(n)])
    integ = np.zeros(nv + n); integ[nv:] = 1
    res = milp(np.concatenate([c, np.zeros(n)]), constraints=LinearConstraint(A_all, lower, upper),
               integrality=integ, bounds=Bounds(lb2, ub2))
    if not res.success:
        raise RuntimeError("MILP infeasible: " + res.message)
    out = _pack(res.x, start, n, I)
    out["cost"] = res.fun
    out["x"] = res.x[nv:]
    return out


# ===================== 两阶段随机规划（问题2/3/4 的正式模型） =====================
def solve_scen(price, load, pv, Q_start, scen_dl, scen_dpv, start=0, plan=None,
               E_end_min=None, k_add=5.0):
    """两阶段随机规划。

    第一阶段（日前计划，所有场景共享）：购电量 g、充放电功率 ch/dis、储电量 Q。
    第二阶段（每个误差场景 s 的应急调度）：紧急购电 add_s、弃光 cur_s。

        min  sum_t C_t dt (g_t + k_add * sum_s w_s add_{s,t})
        s.t. Q_t = Q_{t-1} + (eta ch_t - dis_t/eta) dt ,  Emin<=Q_t<=Emax ,  Q_0 给定
             P_hat_t + dpv_{s,t} - cur_{s,t} + dis_t - ch_t + g_t + add_{s,t}
                 = L_hat_t + dl_{s,t}          for all s,t
             0<=ch,dis<=Pmax , 0<=cur_{s,t}<=P_hat_t+dpv_{s,t} , add>=0 , g>=0
    若给出 plan，则 g 按“低于计划 0.5 倍、超出计划 1.5 倍”分段计价（问题3）。
    """
    n = 144 - start
    S = scen_dl.shape[0]
    pr = np.asarray(price, float)[start:]
    ld = np.asarray(load, float)[start:]
    pvv = np.asarray(pv, float)[start:]
    pl = None if plan is None else np.asarray(plan, float)[start:]
    dl = np.asarray(scen_dl, float)[:, start:]
    dp = np.asarray(scen_dpv, float)[:, start:]

    i_lo, i_hi, i_ch, i_dis = 0, n, 2 * n, 3 * n
    i_Q = 4 * n
    i_sc = 5 * n + 1                    # 场景变量起点（每个场景 n 个 add）
    nv = i_sc + S * n
    c = np.zeros(nv)
    if plan is None:
        c[i_lo:i_lo + n] = pr * DT
    else:
        c[i_lo:i_lo + n] = 0.5 * pr * DT
        c[i_hi:i_hi + n] = 1.5 * pr * DT
    for s in range(S):
        c[i_sc + s * n: i_sc + s * n + n] = pr * DT * k_add / S

    rows, cols, vals, b = [], [], [], []
    # 电量递推（与场景无关）
    for t in range(n):
        r = t
        for j, v in ((i_Q + t + 1, 1.0), (i_Q + t, -1.0),
                     (i_ch + t, -ETA * DT), (i_dis + t, DT / ETA)):
            rows.append(r); cols.append(j); vals.append(v)
        b.append(0.0)
    # 各场景：供给能力（含可弃掉的富余购电）不小于需求 -- 不等式约束
    for s in range(S):
        base = i_sc + s * n
        for t in range(n):
            r = n + s * n + t
            for j, v in ((i_ch + t, -1.0), (i_dis + t, 1.0), (i_lo + t, 1.0),
                         (i_hi + t, 1.0), (base + t, 1.0)):
                rows.append(r); cols.append(j); vals.append(v)
            b.append(ld[t] - pvv[t] + dl[s, t] - dp[s, t])
    A = sp.csr_matrix((vals, (rows, cols)), shape=(n + S * n, nv))

    lb = np.zeros(nv); ub = np.full(nv, np.inf)
    ub[i_lo:i_lo + n] = np.inf if plan is None else pl
    if plan is None:
        ub[i_hi:i_hi + n] = 0.0
    ub[i_ch:i_ch + n] = P_MAX
    ub[i_dis:i_dis + n] = P_MAX
    lb[i_Q:i_Q + n + 1] = E_MIN
    ub[i_Q:i_Q + n + 1] = E_CAP
    lb[i_Q] = ub[i_Q] = Q_start
    if E_end_min is not None:
        lb[i_Q + n] = max(E_MIN, E_end_min)
    res = linprog(c, A_ub=-A[n:], b_ub=-np.array(b[n:]),
                  A_eq=A[:n], b_eq=np.array(b[:n]),
                  bounds=list(zip(lb, ub)), method="highs")
    if not res.success:
        raise RuntimeError("scenario LP infeasible: " + res.message)
    x = res.x
    out = {}
    for k, off in (("ch", i_ch), ("dis", i_dis)):
        a = np.full(144, np.nan); a[start:] = x[off:off + n]; out[k] = a
    g = np.full(144, np.nan); g[start:] = x[i_lo:i_lo + n] + x[i_hi:i_hi + n]
    out["g"] = g
    Q = np.full(145, np.nan); Q[start:] = x[i_Q:i_Q + n + 1]; out["Q"] = Q
    addm = np.zeros(n)
    for s in range(S):
        addm += x[i_sc + s * n: i_sc + s * n + n] / S
    a = np.full(144, np.nan); a[start:] = addm; out["add"] = a
    out["cur"] = np.zeros(144)
    out["cost"] = res.fun
    return out
