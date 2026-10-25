# -*- coding: utf-8 -*-
"""论文插图（9 张，输出到 fig/）。

数据来源：out/p1.npz（问题1）、out/p2.npz、out/p3.npz、out/p4_3.npz、
out/pred.npz（预测与实测）、out/backtest_*.json、out/sens.json。
需先运行 problem1—4 与 analysis/sensitivity.py。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # 使 code/ 可导入

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import dataio as D

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 130

DT = D.DT
HRS = (np.arange(144) + 0.5) / 6.0
DATES = {"2025-03-20": 78, "2025-06-21": 171, "2025-09-23": 265, "2025-12-21": 354}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(D.FIG / name, bbox_inches="tight")
    plt.close(fig)
    print("  已生成 fig/" + name)


def hourly(x):
    """144 个 10min 值 -> 24 个小时均值（仅用于作图展示）。"""
    return np.nanmean(np.asarray(x, float).reshape(24, 6), axis=1)


def fig_profile():
    price, load, pv = D.load_day_profile()
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(HRS, load, color="#c0392b", lw=1.4, label="小区负载")
    ax.plot(HRS, pv, color="#e67e22", lw=1.4, label="光伏预测功率")
    ax.set_xlabel("时刻/h")
    ax.set_ylabel("功率/kW")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 4))
    ax.grid(alpha=.3)
    ax2 = ax.twinx()
    ax2.plot(HRS, price, color="#2c3e50", ls="--", lw=1.2, label="电价")
    ax2.set_ylabel("电价/(元/kWh)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    ax.set_title("附件1 的典型日负荷、光伏与电价曲线")
    save(fig, "fig1_profile.png")


def fig_q1():
    z = np.load(D.OUT / "p1.npz")
    g, ch, dis, Q, price = z["g"], z["ch"], z["dis"], z["Q"], z["price"]
    hh = np.arange(24) + 0.5
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.8), sharex=True,
                             gridspec_kw=dict(height_ratios=[2, 1.3]))
    ax = axes[0]
    ax.plot(hh, hourly(z["load"]), color="#7f8c8d", lw=1.2, label="负载")
    ax.plot(hh, hourly(z["pv"]), color="#e67e22", lw=1.2, label="光伏")
    ax.plot(hh, hourly(g), color="#2980b9", lw=1.6, label="计划购电")
    ax.plot(hh, hourly(dis), color="#27ae60", lw=1.2, label="放电")
    ax.plot(hh, -hourly(ch), color="#8e44ad", lw=1.2, label="充电（取负）")
    ax.axhline(0, color="k", lw=.6)
    ax.set_ylabel("功率/kW（小时均值）")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, ncol=3)
    ax.set_title("问题1 最优计划购电与储能充放电（0:00 与 24:00 储电量均为 6000 kWh）")
    ax = axes[1]
    ax.plot(HRS, Q[1:], color="#c0392b", lw=1.5, label="储电量")
    ax.axhline(1200, color="k", ls=":", lw=.8)
    ax.axhline(10800, color="k", ls=":", lw=.8)
    ax.set_ylabel("储电量/kWh")
    ax.grid(alpha=.3)
    ax2 = ax.twinx()
    ax2.plot(HRS, price, color="#2c3e50", ls="--", lw=1.0, label="电价")
    ax2.set_ylabel("电价/(元/kWh)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower left")
    ax.set_xlabel("时刻/h")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    save(fig, "fig2_q1.png")


def fig_pred():
    rl = json.load(open(D.OUT / "backtest_load.json", encoding="utf-8"))
    rp = json.load(open(D.OUT / "backtest_pv.json", encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
    for ax, d, title in [(axes[0], rl, "负荷"), (axes[1], rp, "光伏")]:
        names = list(d)
        vals = [d[k][0] for k in names]
        idx = np.argsort(vals)[::-1]
        ax.barh([names[i] for i in idx], [vals[i] for i in idx], color="#2980b9")
        ax.set_xlabel("平均绝对误差/kW")
        ax.set_title("%s预测模型回测（2025-02-01 起）" % title)
        ax.grid(axis="x", alpha=.3)
    save(fig, "fig3_pred.png")


def fig_month():
    r2 = json.load(open(D.OUT / "p2_rec.json", encoding="utf-8"))
    r3 = json.load(open(D.OUT / "p3_rec.json", encoding="utf-8"))
    mon = {}
    for tag, rs in (("q2", r2), ("q3", r3)):
        for r in rs:
            m = int(r["date"][5:7])
            mon.setdefault(m, {}).setdefault(tag, [0, 0])
            mon[m][tag][0] += r["cost"]
            mon[m][tag][1] += r["add_kwh"]
    ms = sorted(mon)
    x = np.arange(len(ms))
    w = .38
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.bar(x - w / 2, [mon[m]["q2"][0] / 1e4 for m in ms], w,
           label="问题2 总费用", color="#2980b9")
    ax.bar(x + w / 2, [mon[m]["q3"][0] / 1e4 for m in ms], w,
           label="问题3 总费用", color="#27ae60")
    ax.set_xticks(x)
    ax.set_xticklabels(["%d月" % m for m in ms])
    ax.set_ylabel("月度总费用/万元")
    ax.grid(axis="y", alpha=.3)
    ax2 = ax.twinx()
    ax2.plot(x, [mon[m]["q2"][1] / 1e3 for m in ms], "o--", color="#c0392b", lw=1.2,
             label="问题2 紧急购电量")
    ax2.set_ylabel("紧急购电量/(MWh)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8)
    ax.set_title("全年逐月费用与紧急购电量")
    save(fig, "fig4_month.png")


def fig_day(tag, date, name, title, use_adj=False):
    z = np.load(D.OUT / f"{tag}.npz")
    zz = np.load(D.OUT / "pred.npz")
    i = DATES[date] - 31
    g, ch, dis, ad = z["plan_g"][i], z["ch"][i], z["dis"][i], z["add"][i]
    adj = z["adj_g"][i] if "adj_g" in z else g
    L, P = zz["load_actual"][i], zz["pv_actual"][i]
    price, _, _ = D.load_day_profile()
    rec = {r["date"]: r for r in json.load(open(D.OUT / f"{tag}_rec.json",
                                                encoding="utf-8"))}
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.0), sharex=True,
                             gridspec_kw=dict(height_ratios=[2.2, 1]))
    ax = axes[0]
    hh = np.arange(24) + 0.5
    ax.plot(hh, hourly(P), color="#e67e22", lw=1.4, label="光伏实际")
    ax.plot(hh, hourly(L), color="#7f8c8d", lw=1.4, label="负载实际")
    ax.plot(hh, hourly(dis), color="#27ae60", lw=1.2, label="放电")
    ax.plot(hh, -hourly(ch), color="#8e44ad", lw=1.2, label="充电（取负）")
    ax.plot(hh, hourly(g), color="#2980b9", lw=1.6, label="计划购电")
    if use_adj:
        ax.plot(hh, hourly(adj), color="#e74c3c", ls="--", lw=1.2, label="调整后购电")
    ax.bar(hh, hourly(ad), width=.55, color="#c0392b", alpha=.45, label="紧急购电")
    ax.axhline(0, color="k", lw=.6)
    ax.set_ylabel("功率/kW（小时均值）")
    ax.grid(alpha=.3)
    ax.legend(fontsize=7, ncol=3)
    ax.set_title(title + "\n当日总费用 %s 元，紧急购电 %s kWh"
                 % ("{:,.0f}".format(rec[date]["cost"]),
                    "{:,.0f}".format(rec[date]["add_kwh"])), fontsize=10)
    ax2 = axes[1]
    ax2.plot(HRS, price, color="#2c3e50", lw=1.2)
    ax2.set_ylabel("电价")
    ax2.set_xlabel("时刻/h")
    ax2.grid(alpha=.3)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(range(0, 25, 2))
    save(fig, name)


def fig_sens():
    S = json.load(open(D.OUT / "sens.json", encoding="utf-8"))
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 5.4))

    def pick(pref):
        ks = [k for k in S if k.startswith(pref)]
        xs = [float(k.split("=")[1]) for k in ks]
        ys = [S[k]["total"] / 1e4 for k in ks]
        es = [S[k]["em_kwh"] / 1e3 for k in ks]
        o = np.argsort(xs)
        return np.array(xs)[o], np.array(ys)[o], np.array(es)[o]

    for ax, pref, xl, ttl in [(axes[0, 0], "k_add=", "紧急购电电价倍率", "紧急购电倍率的影响"),
                              (axes[0, 1], "eta=", "充放电效率", "储能效率的影响"),
                              (axes[1, 0], "Q0=", "初始储电量/kWh", "初始储电量的影响"),
                              (axes[1, 1], "win=", "误差场景窗口/天", "场景窗口的影响")]:
        x, y, e = pick(pref)
        ax.plot(x, y, "o-", color="#2980b9", label="全年总费用")
        ax.set_xlabel(xl)
        ax.set_ylabel("总费用/万元")
        ax.set_title(ttl, fontsize=10)
        ax.grid(alpha=.3)
        ax2 = ax.twinx()
        ax2.plot(x, e, "s--", color="#c0392b", label="紧急购电量")
        ax2.set_ylabel("紧急购电量/MWh")
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="best")
    save(fig, "fig5_sens.png")


def fig_price():
    C = D.load_price_year()
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    im = ax.imshow(C[31:365].T, aspect="auto", origin="lower", cmap="viridis",
                   extent=[32, 365, 0, 24])
    ax.set_xlabel("2025 年第几天")
    ax.set_ylabel("时刻/h")
    ax.set_title("附件4 全年实时电价分布")
    fig.colorbar(im, ax=ax, label="元/kWh")
    save(fig, "fig6_price.png")


def main():
    print("生成论文插图…")
    fig_profile()
    fig_q1()
    fig_pred()
    fig_month()
    fig_day("p2", "2025-06-21", "fig7_q2day.png", "问题2 2025-06-21 调度结果")
    fig_day("p3", "2025-09-23", "fig8_q3day.png", "问题3 2025-09-23 计划/调整与调度",
            use_adj=True)
    fig_day("p4_3", "2025-12-21", "fig9_q4day.png", "问题4 2025-12-21 波动电价下的调度",
            use_adj=True)
    fig_sens()
    fig_price()


if __name__ == "__main__":
    main()
