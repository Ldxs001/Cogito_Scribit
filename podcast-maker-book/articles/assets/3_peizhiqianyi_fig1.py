#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图1+图2：存量配置自动搬迁——搬迁必须跑在白名单过滤之前。

数据来源（真实实验，仓的临时副本 test_config_keys.TestConfigMigration，2026-10-12 实测）：
  - 正确顺序：5 个用例全 PASS（0.017s）
  - 注入「过滤先于搬迁」缺陷后：5 个用例中 2 个 FAIL，
    subtitle.window 取值从用户配置值 5 回落到默认值 3
字体：注册 C:/Windows/Fonts/simhei.ttf，防方框。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FONT = "C:/Windows/Fonts/simhei.ttf"
import matplotlib.font_manager as fm
fm.fontManager.addfont(FONT)
prop = fm.FontProperties(fname=FONT)
plt.rcParams["font.family"] = prop.get_name()
plt.rcParams["axes.unicode_minus"] = False

OUT = "articles/assets"

# ---------- 图1：加载顺序对比 ----------
fig, ax = plt.subplots(figsize=(11.2, 4.8))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

def box(ax, x, y, w, h, text, fc, tc="white", fs=12):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.6,rounding_size=2",
                 linewidth=1.2, edgecolor="#444", facecolor=fc))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            color=tc, fontsize=fs, fontproperties=prop, wrap=True)

def arrow(ax, x1, y1, x2, y2, color="#1f6fb2"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                 arrowstyle="-|>", mutation_scale=14,
                 linewidth=1.6, color=color))

# 标题
ax.text(50, 96, "配置加载：搬迁(_migrate) 与 白名单过滤 的顺序", ha="center",
        va="center", fontsize=14, fontweight="bold", fontproperties=prop)

# 上排：正确顺序
ax.text(2, 89, "正确顺序（搬迁 → 白名单过滤）", ha="left", va="center",
        fontsize=12, color="#1a7a3a", fontproperties=prop, fontweight="bold")
box(ax, 2, 71, 26, 13, "存档\nlyric_window = 5", "#5a7fb0")
arrow(ax, 28, 77.5, 38, 77.5)
box(ax, 38, 71, 30, 13, "_migrate 改名\n→ window = 5", "#2f8f4e")
arrow(ax, 68, 77.5, 78, 77.5)
box(ax, 78, 71, 20, 13, "白名单\n在表内", "#2f8f4e")
arrow(ax, 88, 71, 88, 65, "#1a7a3a")
box(ax, 70, 54, 28, 11, "取值 = 5（保留）", "#2f8f4e")

# 下排：错误顺序
ax.text(2, 42, "注入缺陷（白名单过滤 → 搬迁）", ha="left", va="center",
        fontsize=12, color="#b03030", fontproperties=prop, fontweight="bold")
box(ax, 2, 25, 26, 13, "存档\nlyric_window = 5", "#5a7fb0")
arrow(ax, 28, 31.5, 38, 31.5)
box(ax, 38, 25, 30, 13, "白名单\n不在表内", "#b03030")
arrow(ax, 68, 31.5, 78, 31.5)
box(ax, 78, 25, 20, 13, "丢弃", "#b03030")
arrow(ax, 88, 25, 88, 19, "#b03030")
box(ax, 64, 8, 34, 11, "window = 默认 3（值丢）", "#b03030")

fig.tight_layout()
fig.savefig(f"{OUT}/3_peizhiqianyi_fig1.png", dpi=150, bbox_inches="tight")
fig.savefig(f"{OUT}/3_peizhiqianyi_fig1.svg", bbox_inches="tight")
plt.close(fig)

# ---------- 图2：实测取值对比 ----------
fig2, ax2 = plt.subplots(figsize=(5.6, 4.2))
labels = ["正确顺序\n(搬迁先于过滤)", "注入缺陷\n(过滤先于搬迁)"]
vals = [5, 3]
colors = ["#2f8f4e", "#b03030"]
bars = ax2.bar(labels, vals, color=colors, width=0.55)
ax2.axhline(5, color="#1a7a3a", linestyle="--", linewidth=1.4)
ax2.text(1.5, 5.15, "用户原配置值 = 5", color="#1a7a3a", fontsize=10,
         ha="right", fontproperties=prop)
for b, v in zip(bars, vals):
    ax2.text(b.get_x()+b.get_width()/2, v+0.12, str(v),
             ha="center", fontsize=12, fontweight="bold", fontproperties=prop)
ax2.set_ylabel("subtitle.window 取值", fontproperties=prop, fontsize=11)
ax2.set_title("改名键取值：顺序反转即回落默认值", fontproperties=prop, fontsize=12, fontweight="bold")
ax2.set_ylim(0, 6)
ax2.tick_params(axis="x", labelsize=10)
for tick in ax2.get_xticklabels():
    tick.set_fontproperties(prop)
plt.tight_layout()
fig2.savefig(f"{OUT}/3_peizhiqianyi_fig2.png", dpi=150, bbox_inches="tight")
fig2.savefig(f"{OUT}/3_peizhiqianyi_fig2.svg", bbox_inches="tight")
plt.close(fig2)

print("OK: wrote 3_peizhiqianyi_fig1.png/.svg and 3_peizhiqianyi_fig2.png/.svg")
