#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 图 1 生成脚本：静态层预烘焙的省时与画质对账（数据来自 CHANGELOG v0.42.0 实测段）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os

# 注册黑体，防中文方框
FONT = "C:/Windows/Fonts/simhei.ttf"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
    plt.rcParams["font.family"] = fm.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 数据（CHANGELOG v0.42.0 实测：一期 25 分钟节目 / 120s 1080p 对账）----
render_before = 17.8   # 分钟，逐帧重算压暗+框
render_after = 4.8     # 分钟，静态层预烘焙后

psnr_before_box = 83.78   # 框出现前候选 vs 完全不画框（几乎逐字节相同）
psnr_after_box = 54.68    # 框出现后 vs 现状
psnr_old_vs_none = 27.53  # 现状框出现前 vs 不画框（空框肉眼可见差异）

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

# 面板一：出片耗时
bars1 = ax1.bar(["逐帧重算", "静态层预烘焙"], [render_before, render_after],
                color=["#c0504d", "#4f81bd"], width=0.55)
ax1.set_ylabel("出片耗时（分钟）")
ax1.set_title("一期 25 分钟节目：横竖两版合计耗时")
for b, v in zip(bars1, [render_before, render_after]):
    ax1.text(b.get_x() + b.get_width() / 2, v + 0.4, "%.1f" % v,
             ha="center", va="bottom", fontsize=11)
ax1.set_ylim(0, render_before * 1.18)
ax1.text(0.5, render_before * 0.62, "-73%", ha="center",
         color="#2e5b2e", fontsize=13, fontweight="bold")

# 面板二：PSNR 对账（dB，越高越接近真值画面）
labels2 = ["框出现前\n候选 vs 不画框", "框出现后\n候选 vs 现状", "现状框前\nvs 不画框"]
vals2 = [psnr_before_box, psnr_after_box, psnr_old_vs_none]
colors2 = ["#4f81bd", "#4f81bd", "#c0504d"]
bars2 = ax2.bar(labels2, vals2, color=colors2, width=0.6)
ax2.set_ylabel("PSNR（dB，越高质量越接近真值）")
ax2.set_title("画质对账：候选画面 vs 无损真值")
for b, v in zip(bars2, vals2):
    ax2.text(b.get_x() + b.get_width() / 2, v + 1.2, "%.2f" % v,
             ha="center", va="bottom", fontsize=11)
ax2.axhline(40, color="#888", ls="--", lw=0.8)
ax2.text(2.4, 41, "40 dB 视觉无差阈值", fontsize=8, color="#888", ha="right")
ax2.set_ylim(0, 100)

fig.tight_layout()
png = os.path.join(HERE, "35_静态层预烘焙_fig1.png")
svg = os.path.join(HERE, "35_静态层预烘焙_fig1.svg")
fig.savefig(png, dpi=150)
fig.savefig(svg)
print("written:", png, svg)
