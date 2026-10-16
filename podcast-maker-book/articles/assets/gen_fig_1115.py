# -*- coding: utf-8 -*-
"""#15 配图：生产修复链在「已点名女声区」句上的真男声命中率（2026-10-07 探针样本 8 句）。
真实数据取自本仓 timbre_repair 修复链实测（经验刻画，引用见成稿）。白底深字、simhei 防方框。
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
fm.fontManager.addfont(r"C:\Windows\Fonts\simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

methods = ["基线\n(原种子)", "换种子 +1", "换种子 +2", "换种子 +3", "保底\n(复用)"]
hits = [4, 3, 6, 2, 3]
total = 8
rates = [h / total * 100 for h in hits]

fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=150)
bars = ax.bar(methods, rates, color=["#9aa6b2", "#7a94b2", "#7e9e8a", "#b29a8a", "#9aa6b2"],
              edgecolor="#333", linewidth=0.8, width=0.62)
for b, h, r in zip(bars, hits, rates):
    ax.text(b.get_x() + b.get_width() / 2, r + 1.5, "%d/%d\n%.0f%%" % (h, total, r),
            ha="center", va="bottom", fontsize=11, color="#222")
ax.set_ylim(0, 95)
ax.set_ylabel("真男声命中率 (%)", fontsize=12, color="#222")
ax.set_xlabel("修复手段（按 timbre_repair 链路顺序：+1→+2→+3→保底）", fontsize=11, color="#222")
ax.set_title("生产修复链在「已点名女声区」句上的真男声命中率（样本 8 句）", fontsize=12.5, color="#222")
ax.axhline(50, color="#888", ls="--", lw=0.8)
ax.text(4.4, 52, "基线 4/8 = 50%", fontsize=9, color="#666", ha="right")
ax.grid(axis="y", ls=":", alpha=0.4)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()

out_png = os.path.join(HERE, "15_种子确定性派生_fig1.png")
out_svg = os.path.join(HERE, "15_种子确定性派生_fig1.svg")
fig.savefig(out_png, bbox_inches="tight")
fig.savefig(out_svg, bbox_inches="tight")
print("written:", out_png, out_svg)
