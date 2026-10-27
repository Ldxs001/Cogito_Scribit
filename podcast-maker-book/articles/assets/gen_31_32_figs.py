# -*- coding: utf-8 -*-
# 配图脚本：#31 字幕三份同源 / #32 单行字幕横滚
# 真实数据口径见 CHANGELOG v0.39.0 / v0.42.0 / v0.46.0 与 tests/test_subtitle_*.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrow
import os

FONT = "C:/Windows/Fonts/simhei.ttf"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ #31 fig1
def fig31():
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.set_xlim(2.40, 2.62)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylim(0, 3.2)
    # 百分秒网格（每 0.10s = 10 个百分秒）
    for s in [2.40, 2.45, 2.50, 2.55, 2.60]:
        ax.axvline(s, color="#cccccc", lw=0.8)
        ax.text(s, 2.95, "%.2f" % s, ha="center", va="center", fontsize=9, color="#666666")
    # 整秒边界：2.50 是「四舍五入」进位线
    ax.axvline(2.50, color="#C0392B", lw=2.2)
    ax.text(2.50, 2.5, "四舍五入进位线\n(.50 → 进到第 3 秒)", ha="center", va="center",
            fontsize=9, color="#C0392B", fontweight="bold")
    # 两个采样点：共用同一颗「百分秒」整数，落点相同
    # s=2.49 → LRC 00:00.49 / TXT 00:00
    ax.plot([2.49, 2.49], [0.5, 1.6], color="#2E86C1", lw=2)
    ax.scatter([2.49], [1.6], color="#2E86C1", zorder=5)
    ax.text(2.43, 1.15, "LRC [00:00.49]\nTXT 00:00", ha="center", va="center",
            fontsize=9, color="#2E86C1")
    # s=2.50 → LRC 00:00.50 / TXT 00:01（越过红线进位）
    ax.plot([2.50, 2.50], [0.5, 1.6], color="#27AE60", lw=2)
    ax.scatter([2.50], [1.6], color="#27AE60", zorder=5)
    ax.text(2.56, 1.15, "LRC [00:00.50]\nTXT 00:01", ha="center", va="center",
            fontsize=9, color="#27AE60")
    # 底部解释：同一整数半加
    ax.text(2.51, 0.25,
            "LRC 与 TXT 共用 int(round(s*100)) 这一颗百分秒整数；\n"
            "TXT 走 +50//100 整数半加进位，与 LRC 落在同一根数轴，永不岔开。",
            ha="left", va="center", fontsize=8.5, color="#333333")
    ax.set_title("图 1 同源律：LRC 与整秒 TXT 共用同一颗百分秒（取自 v0.46.0 同源律与 v0.39.0 LRC 同源同生成）",
                 fontsize=11, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xticks([])
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "31_字幕三份同源_fig1." + ext), dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ #32 fig1
def fig32():
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.4)
    ax.set_yticks([])
    ax.set_xticks([])
    # 显示框 x in [3.0, 7.0]，文字条宽 9.0（宽于框）
    frame_x0, frame_x1 = 3.0, 7.0
    ax.add_patch(Rectangle((frame_x0, 1.0), frame_x1 - frame_x0, 1.4,
                           facecolor="#FDEBD0", edgecolor="#B9770E", lw=2,
                           hatch="////", zorder=1))
    ax.text((frame_x0 + frame_x1) / 2, 2.7, "显示框（框宽 = 文字宽 - 位移）",
            ha="center", va="center", fontsize=9, color="#B9770E")
    # 三段：句首静止 / 匀速左移 / 句尾静止
    snapshots = [
        (0.5, "#C0392B", "① 句首静止：文字左缘贴框左，先读开头"),
        (3.0, "#2E86C1", "② 匀速左移：位移 = 文字宽 − 框宽，只滚溢出那截"),
        (5.5, "#27AE60", "③ 句尾静止：文字右缘贴框右，结尾留在框内"),
    ]
    for cx, col, label in snapshots:
        # 文字条：中心 cx，宽 9 → 左 2，右 11（溢出到框外）
        ax.add_patch(Rectangle((cx - 4.5, 1.0), 9.0, 1.4,
                               facecolor=col, alpha=0.25, edgecolor=col, lw=1.5, zorder=2))
        ax.text(cx - 4.5 + 0.1, 1.7, "「上期《骨架叙事切分…刚性同步机制。」",
                ha="left", va="center", fontsize=8, color="#333333")
        ax.text(cx, 0.45, label, ha="center", va="center", fontsize=8.2, color=col)
    # 位移箭头（句首→句尾 整体左移）
    ax.add_patch(FancyArrow(0.5, 0.75, 5.0, 0, width=0.04,
                            head_width=0.22, head_length=0.35,
                            fc="#555555", ec="#555555", zorder=3))
    ax.text(2.8, 0.05, "位移方向（左移）  速度 = 文字宽 ÷ 句时长，与朗读同速",
            ha="center", va="center", fontsize=8, color="#555555")
    # 真实样本标注
    ax.text(9.9, 3.0, "真实样本（79 字）：\n\\move(1668,955,252,955,\n14942,27100)\n句首静止 14.94s + 滚动 12.16s = 句长 27.10s",
            ha="right", va="top", fontsize=8, color="#333333",
            bbox=dict(boxstyle="round", fc="#EBF5FB", ec="#2E86C1"))
    ax.set_title("图 1 单行横滚三段式：不折行、不裁字，装不下就滚过框口（取自 v0.42.0）",
                 fontsize=11, fontweight="bold")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "32_单行字幕横滚_fig1." + ext), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig31()
    fig32()
    print("figures written")
