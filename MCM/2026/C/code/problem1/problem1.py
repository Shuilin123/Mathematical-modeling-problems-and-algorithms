# -*- coding: utf-8 -*-
"""问题 1：单日计划购电策略（电价、负载每天相同，光伏预测已知）。

模型：以全天购电费最小为目标的 MILP（0-1 充放电互斥 + 储能电量递推），
      Q_0 = Q_144 = 6000 kWh。
求解：HiGHS。先解 LP 松弛、再解 MILP，二者目标值相同即验证松弛精确性。
输出：result1.xlsx（144 段购电量；6 个 4h 时段充放电量与 0:00/24:00 储电量）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import numpy as np

from common import dataio as D
from common import model as M


def main():
    price, load, pv = D.load_day_profile()
    Q0 = D.E_INIT

    # ---------- 求解：LP 松弛 与 MILP ----------
    lp = M.solve_horizon(price, load, pv, Q0, E_end_min=Q0, E_end_eq=True, k_add=D.K_ADD)
    milp = M.solve_horizon_milp(price, load, pv, Q0, E_end_min=Q0, E_end_eq=True,
                                k_add=D.K_ADD)
    g, ch, dis, Q = lp["g"], lp["ch"], lp["dis"], lp["Q"]

    print("=" * 68)
    print("问题 1：单日最优购电策略")
    print("=" * 68)
    print("LP 松弛目标值 = %.4f 元；MILP 目标值 = %.4f 元（差 %.2e）"
          % (lp["cost"], milp["cost"], abs(lp["cost"] - milp["cost"])))
    print("同时充放电最大功率 = %.6f kW（LP）/ %.6f kW（MILP）"
          % (np.max(np.minimum(lp["ch"], lp["dis"])),
             np.max(np.minimum(milp["ch"], milp["dis"]))))
    print("能量校验：购电 %.2f = 净负荷 %.2f + 储能损耗 %.2f kWh"
          % (g.sum() * D.DT,
             (load.sum() - pv.sum()) * D.DT,
             (ch.sum() - dis.sum()) * D.DT))
    print("弃光电量 %.2f kWh；Q_0 = %.2f，Q_144 = %.2f kWh"
          % (lp["cur"].sum() * D.DT, Q[0], Q[144]))

    # ---------- 表 1：指定时段购电量 ----------
    print("\n表 1  指定时段购电量")
    for h in (10, 12, 14, 16, 18, 20):
        t = h * 6
        print("  %2d:00-%2d:10  %8.4f kWh" % (h, h, g[t] * D.DT))
    print("  全天购电量 %8.2f kWh，全天购电费 %8.2f 元"
          % (g.sum() * D.DT, (g * price * D.DT).sum()))

    # ---------- 表 2：储能分时充放电量 ----------
    print("\n表 2  储能分时充放电量与储电量")
    for k in range(6):
        s = slice(24 * k, 24 * (k + 1))
        print("  %-12s 充电 %8.2f  放电 %8.2f  时段末储电量 %8.2f"
              % (D.BLOCKS[k], (ch[s] * D.DT).sum(), (dis[s] * D.DT).sum(),
                 Q[24 * (k + 1)]))
    print("  0:00 储电量 %.2f，24:00 储电量 %.2f kWh" % (Q[0], Q[144]))

    base = (np.maximum(load - pv, 0) * price * D.DT).sum()
    print("\n经济性：无储能直接购电 %.2f 元 → 本文 %.2f 元，节省 %.2f 元（%.2f%%）"
          % (base, (g * price * D.DT).sum(), base - (g * price * D.DT).sum(),
             100 * (base - (g * price * D.DT).sum()) / base))

    # ---------- 保存 ----------
    np.savez(D.OUT / "p1.npz", g=g, ch=ch, dis=dis, cur=lp["cur"], Q=Q,
             price=price, load=load, pv=pv)
    D.write_result1(g, ch, dis, Q, price)


if __name__ == "__main__":
    main()
