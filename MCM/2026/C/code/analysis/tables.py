# -*- coding: utf-8 -*-
"""论文表格与关键数值：out/tables.md（表 1—23 的数据）与 out/numbers.json。

需先运行 problem1—4。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import json

import numpy as np

from common import dataio as D

DT = D.DT
DATES = ["2025-03-20", "2025-06-21", "2025-09-23", "2025-12-21"]
T_POINTS = [(10, "10:00-10:10"), (12, "12:00-12:10"), (14, "14:00-14:10"),
            (16, "16:00-16:10"), (18, "18:00-18:10"), (20, "20:00-20:10")]
TAGS = {"p2": "问题2", "p3": "问题3", "p4_2": "问题4-2", "p4_3": "问题4-3"}


def f(x, n=2):
    return ("{:,.%df}" % n).format(x)


def load_json(name):
    return json.load(open(D.OUT / name, encoding="utf-8"))


# ---------------- 问题 1 ----------------
def q1_tables():
    z = np.load(D.OUT / "p1.npz")
    g, ch, dis, Q, price = z["g"], z["ch"], z["dis"], z["Q"], z["price"]
    L = ["**表 1  问题 1 指定时段购电量与全天费用**\n",
         "| 时间段 | 购电量/kWh | 时间段 | 购电量/kWh | 时间段 | 购电量/kWh |",
         "|---|---|---|---|---|---|"]
    vals = [g[h * 6] * DT for h, _ in T_POINTS]
    for r in range(2):
        L.append("| " + " | ".join("%s | %s" % (T_POINTS[r * 3 + c][1],
                                                f(vals[r * 3 + c], 4))
                                   for c in range(3)) + " |")
    fee = (g * price * DT).sum()
    L.append("\n全天购电量 = **%s kWh**，全天购电费 = **%s 元**\n" % (f(g.sum() * DT), f(fee)))
    L.append("**表 2  问题 1 储能设备分时充放电量与储电量**\n")
    L.append("| 时间段 | 充电量/kWh | 放电量/kWh | 时段末储电量/kWh |")
    L.append("|---|---|---|---|")
    for k in range(6):
        s = slice(24 * k, 24 * (k + 1))
        L.append("| %s | %s | %s | %s |" % (D.BLOCKS[k], f((ch[s] * DT).sum()),
                                           f((dis[s] * DT).sum()), f(Q[24 * (k + 1)])))
    L.append("\n0:00 储电量 %s kWh，24:00 储电量 %s kWh；全天充电 %s kWh、放电 %s kWh。"
             % (f(Q[0]), f(Q[144]), f((ch * DT).sum()), f((dis * DT).sum())))
    base = (np.maximum(z["load"] - z["pv"], 0) * price * DT).sum()
    L.append("\n> 无储能直接购电 %s 元（购电 %s kWh），储能节省 %s 元（%.2f%%）。\n"
             % (f(base), f(np.maximum(z["load"] - z["pv"], 0).sum() * DT), f(base - fee),
                100 * (base - fee) / base))
    return "\n".join(L)


# ---------------- 全年汇总 ----------------
def summary_table():
    p2, p3, p4 = load_json("p2_summary.json"), load_json("p3_summary.json"), load_json("p4_summary.json")
    rows = [("问题2 两阶段随机规划（0:00 计划）", p2["main"]),
            ("问题2 确定性计划（不作风险对冲）", p2["det"]),
            ("问题2 完美信息（理论下界）", p2["perfect"]),
            ("问题3 仅用 0:00 预报", p3["rev0"]),
            ("问题3 +6:00 调整", p3["rev1"]),
            ("问题3 +6:00、12:00 调整", p3["rev2"]),
            ("问题3 四次预报全用", p3["main"]),
            ("问题4 对应问题2（波动电价）", p4["q4_2"]),
            ("问题4 对应问题3（波动电价）", p4["q4_3"])]
    L = ["| 方案 | 总费用/元 | 计划购电费/元 | 调整附加/元 | 紧急购电费/元 | 紧急电量/kWh | 日均费用/元 |",
         "|---|---|---|---|---|---|---|"]
    for nm, d in rows:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            nm, f(d["total_cost"]), f(d["cost_plan"]), f(d["cost_adjust_extra"]),
            f(d["cost_emergency"]), f(d["energy_add"], 0), f(d["avg_day_cost"])))
    for nm, v in [("基准：无储能、实际光伏（附件1 电价）", p2["base_nostorage"]),
                  ("基准：无储能、实际光伏（附件4 电价）", p4["base_nostorage"])]:
        L.append("| %s | %s | — | — | — | — | %s |" % (nm, f(v), f(v / 334)))
    return "\n".join(L)


def month_table():
    L = []
    for tag, nm in [("p2", "问题2"), ("p3", "问题3"), ("p4_2", "问题4(对应2)"),
                    ("p4_3", "问题4(对应3)")]:
        rec = load_json(f"{tag}_rec.json")
        mon = {}
        for r in rec:
            a = mon.setdefault(int(r["date"][5:7]),
                               dict(c=0.0, add=0.0, plan=0.0, em=0.0, n=0))
            a["c"] += r["cost"]; a["add"] += r["add_kwh"]
            a["plan"] += r["plan_kwh"]; a["em"] += r["cost_em"]; a["n"] += 1
        L.append("**%s 月度结果**\n" % nm)
        L.append("| 月份 | 天数 | 总费用/元 | 计划购电量/kWh | 紧急购电量/kWh | 紧急购电费/元 | 日均费用/元 |")
        L.append("|---|---|---|---|---|---|---|")
        for m in sorted(mon):
            a = mon[m]
            L.append("| %d月 | %d | %s | %s | %s | %s | %s |" % (
                m, a["n"], f(a["c"], 0), f(a["plan"], 0), f(a["add"], 0),
                f(a["em"], 0), f(a["c"] / a["n"])))
        L.append("")
    return "\n".join(L)


# ---------------- 指定日期明细 ----------------
def date_tables(tag, use_adj=False):
    z = np.load(D.OUT / f"{tag}.npz")
    rec = {r["date"]: r for r in load_json(f"{tag}_rec.json")}
    L = []
    for name in DATES:
        i = int((np.datetime64(name) - np.datetime64("2025-01-01")) / np.timedelta64(1, "D")) - 31
        g, ch, dis, ad, Q = (z["plan_g"][i], z["ch"][i], z["dis"][i],
                             z["add"][i], z["q"][i])
        adj = z["adj_g"][i] if "adj_g" in z else g
        r = rec[name]
        L.append("**%s 指定时段购电量（%s，单位 kWh）**\n" % (name, TAGS[tag]))
        L.append("| 时间段 | 计划购电量 | 调整购电量 |" if use_adj
                 else "| 时间段 | 购电量 |")
        L.append("|---|---|---|" if use_adj else "|---|---|")
        for h, lab in T_POINTS:
            if use_adj:
                L.append("| %s | %s | %s |" % (lab, f(g[h * 6] * DT, 4),
                                               f(adj[h * 6] * DT, 4)))
            else:
                L.append("| %s | %s |" % (lab, f(g[h * 6] * DT, 4)))
        L.append("| 全天 | %s | %s |" % (f(r["plan_kwh"]), f(r["adj_kwh"])) if use_adj
                 else "| 全天购电量 | %s |" % f(r["plan_kwh"]))
        L.append("")
        L.append("- 计划购电费 %s 元，紧急购电 %s kWh / %s 元，当日总费用 %s 元"
                 % (f(r["cost_plan"]), f(r["add_kwh"]), f(r["cost_em"]), f(r["cost"])))
        L.append("")
        L.append("| 时间段 | 充电量 | 放电量 | 储电量变化 |")
        L.append("|---|---|---|---|")
        for k in range(6):
            s = slice(24 * k, 24 * (k + 1))
            L.append("| %s | %s | %s | %s → %s |" % (
                D.BLOCKS[k], f((ch[s] * DT).sum()), f((dis[s] * DT).sum()),
                f(Q[24 * k]), f(Q[24 * (k + 1)])))
        L.append("")
        rs = D.runs_of(ad)
        L.append("紧急购电：" + ("；".join("%s（%s kWh）" % (D.seg_label(s, e), f(v))
                                          for s, e, v in rs[:6]) if rs else "无"))
        L.append("")
    return "\n".join(L)


# ---------------- 关键数值（守恒、电价统计） ----------------
def numbers():
    z = np.load(D.OUT / "pred.npz")
    L, P = z["load_actual"][31:365], z["pv_actual"][31:365]
    res = dict(load_energy=float(L.sum() * DT), pv_energy=float(P.sum() * DT),
               net_load=float((L - P).sum() * DT))
    for tag in ("p2", "p3", "p4_2", "p4_3"):
        d = np.load(D.OUT / f"{tag}.npz")
        g, ch, dis, ad, cu = d["adj_g"], d["ch"], d["dis"], d["add"], d["cur"]
        res[tag] = dict(adj=float(g.sum() * DT), ch=float(ch.sum() * DT),
                        dis=float(dis.sum() * DT), add=float(ad.sum() * DT),
                        cur=float(cu.sum() * DT),
                        check=float((P + dis - ch + g + ad - cu - L).sum() * DT))
    price, _, _ = D.load_day_profile()
    C4 = D.load_price_year()[31:365]
    res["price1"] = dict(mean=float(price.mean()), std=float(price.std()),
                         min=float(price.min()), max=float(price.max()),
                         mad=float(np.abs(np.diff(price)).mean()))
    res["price4"] = dict(mean=float(C4.mean()), std=float(C4.std()),
                         min=float(C4.min()), max=float(C4.max()),
                         mad=float(np.abs(np.diff(C4, axis=1)).mean()))
    for tag in ("p2", "p3", "p4_2", "p4_3"):
        s = load_json({"p2": "p2_summary.json", "p3": "p3_summary.json",
                       "p4_2": "p4_summary.json", "p4_3": "p4_summary.json"}[tag])
        key = {"p2": "main", "p3": "main", "p4_2": "q4_2", "p4_3": "q4_3"}[tag]
        res[tag]["cost"] = s[key]["total_cost"]
        res[tag]["cost_plan"] = s[key]["cost_plan"]
        res[tag]["unit"] = s[key]["cost_plan"] / s[key]["energy_plan"]
        rec = load_json(f"{tag}_rec.json")
        mx = max(rec, key=lambda r: r["cost"])
        mn = min(rec, key=lambda r: r["cost"])
        res[tag]["max_day"] = (mx["date"], mx["cost"])
        res[tag]["min_day"] = (mn["date"], mn["cost"])
    with open(D.OUT / "numbers.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    return res


def main():
    with open(D.OUT / "tables.md", "w", encoding="utf-8") as fh:
        fh.write("# 问题1\n\n" + q1_tables() + "\n\n")
        fh.write("# 汇总\n\n" + summary_table() + "\n\n")
        fh.write("# 月度\n\n" + month_table() + "\n\n")
        for tag, adj in [("p2", False), ("p3", True), ("p4_2", False), ("p4_3", True)]:
            fh.write("# %s 指定日期\n\n" % TAGS[tag] + date_tables(tag, adj) + "\n\n")
    num = numbers()
    print("已写出 out/tables.md 与 out/numbers.json")
    print("负载 %.1f 万 kWh，光伏 %.1f 万 kWh，净负荷 %.1f 万 kWh"
          % (num["load_energy"] / 1e4, num["pv_energy"] / 1e4, num["net_load"] / 1e4))
    for tag in ("p2", "p3", "p4_2", "p4_3"):
        d = num[tag]
        print("  %-5s 购电 %9.0f  紧急 %7.0f  富余 %8.0f  守恒残差 %.1e kWh"
              % (tag, d["adj"], d["add"], d["cur"], d["check"]))


if __name__ == "__main__":
    main()
