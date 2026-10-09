# -*- coding: utf-8 -*-
# 图：同源一次生成（正确） vs 反解链（错路）
# 数据源 podcast-maker · CHANGELOG.md · v0.46.0（四份同源、不从产物反解）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont(r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.2, 3.8), dpi=150)
for ax in (axL, axR):
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(-0.12, 1.0)

src = dict(boxstyle="round,pad=0.4", fc="#1f6feb", ec="#1f6feb")
out = dict(boxstyle="round,pad=0.4", fc="#dbeafe", ec="#1f6feb")
bad = dict(boxstyle="round,pad=0.4", fc="#fde2e2", ec="#d33")

# 左：同源一次生成
axL.set_title("同源一次生成（正确）", fontsize=12)
axL.text(0.5, 0.86, "同一份源\nscript / timings", ha="center", va="center",
         color="white", bbox=src, fontsize=10)
for x, l in zip([0.12, 0.38, 0.64, 0.88], ["SRT", "LRC", "TXT", "洁版 TXT"]):
    axL.annotate("", xy=(x, 0.34), xytext=(0.5, 0.74),
                 arrowprops=dict(arrowstyle="->", color="#1f6feb", lw=1.5))
    axL.text(x, 0.2, l, ha="center", va="center", bbox=out, fontsize=9)
axL.text(0.5, 0.0, "四份互不反解，顺序无关", ha="center", fontsize=8, color="#444")

# 右：反解链
axR.set_title("反解链（错路）", fontsize=12)
axR.text(0.5, 0.86, "同一份源", ha="center", va="center",
         color="white", bbox=src, fontsize=10)
axR.annotate("", xy=(0.5, 0.5), xytext=(0.5, 0.74),
             arrowprops=dict(arrowstyle="->", color="#1f6feb", lw=1.5))
axR.text(0.5, 0.42, "TXT（先写盘）", ha="center", va="center", bbox=bad, fontsize=9)
axR.annotate("", xy=(0.5, 0.16), xytext=(0.5, 0.32),
             arrowprops=dict(arrowstyle="->", color="#d33", lw=1.8))
axR.text(0.5, 0.08, "洁版 TXT\n（读 .txt 反解）", ha="center", va="center", bbox=bad, fontsize=9)
axR.text(0.5, -0.08, "↯ 旧 .txt 静默产错 / 顺序依赖", ha="center", fontsize=8, color="#d33")

fig.text(0.01, -0.02, "数据源：podcast-maker · CHANGELOG.md · v0.46.0（四份同源、不从产物反解）[1][2]",
         fontsize=7, color="#666")
fig.tight_layout()
fig.savefig("articles/assets/22_字幕_fig1.png", bbox_inches="tight")
fig.savefig("articles/assets/22_字幕_fig1.svg", bbox_inches="tight")
print("OK 22_字幕_fig1 png+svg")
