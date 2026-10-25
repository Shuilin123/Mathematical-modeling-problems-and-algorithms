# -*- coding: utf-8 -*-
"""问题 4：实时波动电价下重算问题 2 与问题 3。

模型：与问题 2、3 完全相同，只把电价序列由附件1 换成附件4 的逐日实时电价
      C_{d,t}（视为日前出清价，0:00 已知当日曲线），紧急购电按 5 倍实时电价。
输出：result4-2.xlsx（对应问题 2）、result4-3.xlsx（对应问题 3）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import json

import numpy as np

from common import dataio as D
from common import scheduler as S


def main():
    price4 = D.load_price_year()

    print("=" * 68)
    print("问题 4：波动电价下的购电策略（334 天）")
    print("=" * 68)
    print("[1/3] 对应问题 2（0:00 一次计划）…")
    r2 = S.simulate(price4, mode="hist", revisions=(0,))
    s2 = S.summarize(r2, "问题4-2")
    S.save(r2, "p4_2")
    S.print_key_dates(r2)

    print("\n[2/3] 对应问题 3（0:00 + 6/12/18 时修正）…")
    r3 = S.simulate(price4, mode="fc", revisions=(0, 1, 2, 3))
    s3 = S.summarize(r3, "问题4-3")
    S.save(r3, "p4_3")
    S.print_key_dates(r3, use_adj=True)

    z = np.load(D.OUT / "pred.npz")
    L, P = z["load_actual"][31:365], z["pv_actual"][31:365]
    base = float(sum((np.maximum(L[i] - P[i], 0.0) * price4[31 + i]).sum() * D.DT
                     for i in range(334)))
    print("\n[3/3] 基准：无储能 + 实际光伏（附件4 电价）  总费用 %.2f 元" % base)

    print("\n与固定电价（问题 2、3）的对比")
    for tag, file in [("问题4-2", "p2_summary.json"), ("问题4-3", "p3_summary.json")]:
        s = s2 if tag == "问题4-2" else s3
        if (D.OUT / file).exists():
            old = json.load(open(D.OUT / file, encoding="utf-8"))["main"]["total_cost"]
            print("  %s %.2f 元；固定电价 %.2f 元；变化 %+.2f 元（%+.2f%%）"
                  % (tag, s["total_cost"], old, s["total_cost"] - old,
                     100 * (s["total_cost"] - old) / old))
        else:
            print("  %s %.2f 元" % (tag, s["total_cost"]))
    print("  无储能基准 %.2f 元；储能节省 %.2f 元（%.2f%%）"
          % (base, base - s2["total_cost"],
             100 * (base - s2["total_cost"]) / base))

    json.dump(dict(q4_2=s2, q4_3=s3, base_nostorage=base),
              open(D.OUT / "p4_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    D.write_multi("result4-2.xlsx", r2["plan_g"], r2["ch"], r2["dis"],
                  r2["q"], r2["add"])
    D.write_multi("result4-3.xlsx", r3["plan_g"], r3["ch"], r3["dis"],
                  r3["q"], r3["add"], adj=r3["adj_g"])


if __name__ == "__main__":
    main()
