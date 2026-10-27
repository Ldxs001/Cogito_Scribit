# -*- coding: utf-8 -*-
"""生成 #33 / #34 配图（真实实验数据，matplotlib + simhei）。
稿面引用：articles/assets/33_字幕断词_fig1.* / 34_ASS配色陷阱_fig1.*
测量条件：podcast-maker v2.12.0b1 临时副本（只读调用），2026-10-25。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.font_manager import FontProperties
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")
plt.rcParams["font.family"] = FONT.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.sans-serif"] = [FONT.get_name()]

# ---------------------------------------------------------------------------
# 图 1（#33）：断词率对照 + 行长度均衡对照
# ---------------------------------------------------------------------------
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.6))

# 左：断词处数（旧 42 / 新 0，分母 393 处折行）
bars = axL.bar(["旧·逐字符硬切", "新·四级判定+均衡"], [42, 0],
               color=["#c0392b", "#27ae60"], width=0.55, edgecolor="#333", linewidth=0.8)
axL.set_ylabel("断在词中间的折行处数", fontproperties=FONT, fontsize=12)
axL.set_title("断词率：393 处折行，旧式 42 处断词（11.1%）→ 现 0 处",
              fontproperties=FONT, fontsize=12)
for b, v in zip(bars, [42, 0]):
    axL.text(b.get_x() + b.get_width() / 2, v + 1.0, str(v),
             ha="center", va="bottom", fontproperties=FONT, fontsize=12)
axL.set_ylim(0, 52)
axL.grid(axis="y", linestyle=":", alpha=0.4)

# 右：行长度均衡对照（RAGAssistant 样本，每行容量 33 字）
labels = ["行 1", "行 2"]
x = range(len(labels))
greedy = [33, 15]   # 旧式填充满：头重脚轻
balanced = [24, 24]  # 现均衡折行
w = 0.36
axR.bar([i - w / 2 for i in x], greedy, w, label="贪心填充满", color="#e67e22", edgecolor="#333")
axR.bar([i + w / 2 for i in x], balanced, w, label="均衡折行", color="#2980b9", edgecolor="#333")
axR.set_xticks(list(x))
axR.set_xticklabels(labels, fontproperties=FONT, fontsize=12)
axR.set_ylabel("该行字数", fontproperties=FONT, fontsize=12)
axR.set_title("行长度：贪心 33+15（头重脚轻）vs 均衡 24+24", fontproperties=FONT, fontsize=12)
for i, (g, b) in enumerate(zip(greedy, balanced)):
    axR.text(i - w / 2, g + 0.5, str(g), ha="center", fontproperties=FONT, fontsize=10)
    axR.text(i + w / 2, b + 0.5, str(b), ha="center", fontproperties=FONT, fontsize=10)
axR.legend(prop=FONT, fontsize=10, loc="upper right")
axR.set_ylim(0, 40)
axR.grid(axis="y", linestyle=":", alpha=0.4)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "33_字幕断词_fig1.png"), dpi=150, bbox_inches="tight")
fig.savefig(os.path.join(HERE, "33_字幕断词_fig1.svg"), bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# 图 2（#34）：ASS 配色字节序陷阱
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

def box(x, y, w, h, fc, text, tc="#000", fs=11, bold=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor="#333", linewidth=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontproperties=FONT, fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal")

def arrow(x1, y1, x2, y2, color="#333", style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                mutation_scale=14, color=color, lw=1.6, linestyle=ls))

# 起点：ASS 值（绿，BGR 字节序）
box(2, 40, 26, 20, "#00FF00", "ASS 值\n&H00FF00\n（绿·字节序 BGR）", tc="#003300", fs=10)
# 正确路径：cssColor 反转字节序
arrow(28, 55, 46, 55, color="#27ae60")
ax.text(37, 60, "cssColor：反转字节序\nBGR → RGB", ha="center", fontproperties=FONT, fontsize=10, color="#1e7d46")
# 终点：CSS（绿）
box(46, 40, 26, 20, "#00FF00", "CSS\n#00FF00\n（绿·字节序 RGB）", tc="#003300", fs=10)
# 陷阱分支：直接喂 SVG
arrow(15, 40, 15, 20, color="#c0392b", ls="--")
ax.text(15, 30, "直接喂 SVG\nfill='&H00FF00'\n（无 #·字节序错）", ha="center",
        fontproperties=FONT, fontsize=9, color="#c0392b")
# 陷阱终点：浏览器丢弃→黑
box(2, 4, 26, 14, "#000000", "浏览器丢弃非法值\n字变黑", tc="#ffffff", fs=10)
arrow(15, 18, 15, 18.5, color="#c0392b", style="-|>")

# 字节序说明框
box(74, 38, 24, 28, "#ecf0f1",
    "&HBBGGRR 拆开看：\nB=00 G=FF R=00\n→ 绿\n\nCSS #RRGGBB 要：\nR=00 G=FF B=00\n→ 绿\n\n不反转 = 红蓝互换 / 非法", tc="#222", fs=9)
ax.text(86, 70, "字节序是陷阱核心", ha="center", fontproperties=FONT, fontsize=10, color="#c0392b")

ax.set_title("ASS 配色陷阱：&HAABBGGRR 是 BGR 字节序，直接喂 CSS 即黑",
             fontproperties=FONT, fontsize=12, loc="left")

fig.tight_layout()
fig.savefig(os.path.join(HERE, "34_ASS配色陷阱_fig1.png"), dpi=150, bbox_inches="tight")
fig.savefig(os.path.join(HERE, "34_ASS配色陷阱_fig1.svg"), bbox_inches="tight")
plt.close(fig)
print("figures written:",
      os.path.join(HERE, "33_字幕断词_fig1.png"),
      os.path.join(HERE, "34_ASS配色陷阱_fig1.png"))
