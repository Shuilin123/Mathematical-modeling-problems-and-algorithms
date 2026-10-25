# -*- coding: utf-8 -*-
"""问题 2：5 倍紧急购电价下的日滚动两阶段随机规划。

模型：第一阶段决定计划购电与充放电（所有误差场景共享），第二阶段在每个
      误差场景下决定紧急购电；场景取近 21 天的日级预测误差向量。
对照：确定性计划（不做风险对冲）、完美信息（理论下界）、无储能基准。
输出：result2.xlsx（334 天计划购电量、充放电量、紧急购电量）。
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
    print("问题 2：日滚动两阶段随机规划（2025-02-01 — 12-31，334 天）")
    print("=" * 68)
    print("[1/4] 两阶段随机规划（本文模型）…")
    res = S.simulate(price1_mat, mode="hist", revisions=(0,))
    main_sum = S.summarize(res, "问题2 随机规划")
    S.save(res, "p2")
    S.print_key_dates(res)

    print("\n[2/4] 对照：确定性计划（按点预测，不作风险对冲）…")
    det = S.simulate(price1_mat, mode="hist", revisions=(0,), hedge=False)
    det_sum = S.summarize(det, "对照-确定性")

    print("\n[3/4] 基准：完美信息（负荷与光伏均已知）…")
    per = S.simulate(price1_mat, mode="hist", revisions=(0,), perfect=True)
    per_sum = S.summarize(per, "基准-完美信息")

    z = np.load(D.OUT / "pred.npz")
    L, P = z["load_actual"][31:365], z["pv_actual"][31:365]
    base = float(sum((np.maximum(L[i] - P[i], 0.0) * price1).sum() * D.DT
                     for i in range(334)))
    print("\n[4/4] 基准：无储能 + 实际光伏      总费用 %.2f 元" % base)

    print("\n费用对比（元）")
    print("  两阶段随机规划 %.2f | 确定性 %.2f | 无储能 %.2f | 完美信息 %.2f"
          % (main_sum["total_cost"], det_sum["total_cost"], base,
             per_sum["total_cost"]))
    print("  相对确定性节省 %.2f（%.2f%%），相对无储能节省 %.2f（%.2f%%）"
          % (det_sum["total_cost"] - main_sum["total_cost"],
             100 * (det_sum["total_cost"] - main_sum["total_cost"]) / det_sum["total_cost"],
             base - main_sum["total_cost"],
             100 * (base - main_sum["total_cost"]) / base))

    json.dump(dict(main=main_sum, det=det_sum, perfect=per_sum,
                   base_nostorage=base),
              open(D.OUT / "p2_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    D.write_multi("result2.xlsx", res["plan_g"], res["ch"], res["dis"],
                  res["q"], res["add"])


if __name__ == "__main__":
    main()
