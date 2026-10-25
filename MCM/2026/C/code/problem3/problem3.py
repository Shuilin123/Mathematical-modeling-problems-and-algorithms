# -*- coding: utf-8 -*-
"""问题 3：多时刻光伏预报下的滚动修正策略。

模型：以 0:00 计划量 g_plan 为基准，购电量低于计划的部分按 0.5 倍电价、
      超出部分按 1.5 倍电价（分段线性凸费用，用 u/v 分解精确线性化）；
      在 6:00 / 12:00 / 18:00 用新预报（附件3 与历史统计融合，w=0.358）
      与已实现负荷的误差修正系数更新预测，在剩余时段重解随机规划。
输出：result3.xlsx（计划购电量、调整购电量、充放电量、紧急购电量），
      并给出"是否需要引入其他时刻预报"的方案对比。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import json

import numpy as np

from common import dataio as D
from common import scheduler as S


def main():
    price1, _, _ = D.load_day_profile()
    price1_mat = np.tile(price1, (365, 1))

    print("=" * 68)
    print("问题 3：0:00 计划 + 6/12/18 时滚动修正（334 天）")
    print("=" * 68)
    print("[1/4] 四次预报全用（本文方案）…")
    res = S.simulate(price1_mat, mode="fc", revisions=(0, 1, 2, 3))
    main_sum = S.summarize(res, "问题3 四次修正")
    S.save(res, "p3")
    S.print_key_dates(res, use_adj=True)

    print("\n[2/4] 仅用 0:00 预报（不调整）…")
    r0 = S.simulate(price1_mat, mode="fc", revisions=(0,))
    s0 = S.summarize(r0, "仅 0:00")

    print("\n[3/4] 0:00 + 6:00 调整…")
    r1 = S.simulate(price1_mat, mode="fc", revisions=(0, 1))
    s1 = S.summarize(r1, "0:00+6:00")

    print("\n[4/4] 0:00 + 6:00 + 12:00 调整…")
    r2 = S.simulate(price1_mat, mode="fc", revisions=(0, 1, 2))
    s2 = S.summarize(r2, "0:00+6+12")

    print("\n是否引入其他时刻预报（全年总费用，元）")
    for tag, s in [("仅 0:00 预报", s0), ("+6:00", s1), ("+6:00+12:00", s2),
                   ("四次全用", main_sum)]:
        print("  %-14s %12.2f  相对仅 0:00 %+11.2f 元" %
              (tag, s["total_cost"], s["total_cost"] - s0["total_cost"]))

    json.dump(dict(main=main_sum, rev0=s0, rev1=s1, rev2=s2),
              open(D.OUT / "p3_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    D.write_multi("result3.xlsx", res["plan_g"], res["ch"], res["dis"],
                  res["q"], res["add"], adj=res["adj_g"])


if __name__ == "__main__":
    main()
