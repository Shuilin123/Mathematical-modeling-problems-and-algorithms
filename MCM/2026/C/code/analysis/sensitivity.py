# -*- coding: utf-8 -*-
"""灵敏度分析（基于问题 2 的模型）：紧急购电倍率、储能效率、初始储电量、
误差场景窗口、末端储电量约束。

输出：out/sens.json（论文表 23、图 5）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import json

import numpy as np

from common import dataio as D
from common import model as M
from common import scheduler as S


def run(tag, **kw):
    price, _, _ = D.load_day_profile()
    price_mat = np.tile(price, (365, 1))
    res = S.simulate(price_mat, mode="hist", revisions=(0,), **kw)
    tot = sum(r["cost"] for r in res["rec"])
    em = sum(r["cost_em"] for r in res["rec"])
    ekwh = sum(r["add_kwh"] for r in res["rec"])
    print("  %-18s 总费用 %12.0f 元  紧急费用 %10.0f 元  紧急电量 %9.0f kWh"
          % (tag, tot, em, ekwh))
    return dict(tag=tag, total=tot, emergency=em, em_kwh=ekwh)


def main():
    out = {}
    print("== 紧急购电电价倍率 k ==")
    for k in (2.0, 3.0, 5.0, 8.0, 10.0):
        out["k_add=%.0f" % k] = run("k_add=%.0f" % k, k_add=k)

    print("== 充放电效率 eta ==")
    for e in (0.80, 0.85, 0.90, 0.95, 1.00):
        M.ETA = D.ETA = e
        out["eta=%.2f" % e] = run("eta=%.2f" % e)
    M.ETA = D.ETA = 0.90

    print("== 初始储电量 Q0 ==")
    for q0 in (1200, 3600, 6000, 8400, 10800):
        out["Q0=%d" % q0] = run("Q0=%d" % q0, Q_init=q0)

    print("== 误差场景窗口 ==")
    for w in (7, 14, 21, 35, 60):
        out["win=%d" % w] = run("win=%d" % w, win=w)

    print("== 末端储电量约束 ==")
    out["末端=Q0"] = run("末端 Q144>=Q0", term="ge")
    out["末端自由"] = run("末端自由", term="free")

    json.dump(out, open(D.OUT / "sens.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n已写出 out/sens.json")


if __name__ == "__main__":
    main()
