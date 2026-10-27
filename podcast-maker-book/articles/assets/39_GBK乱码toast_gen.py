# -*- coding: utf-8 -*-
"""《我写故我播》#39 配图生成（matplotlib + 黑体，PNG+SVG 双格式）。
图内文字全部来自真实项目实证；落 articles/assets/ 供 md 相对路径引用。
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc"]
for fp in FONTS:
    if os.path.exists(fp):
        try:
            fm.fontManager.addfont(fp)
        except Exception as e:
            print("warn: addfont failed for %s: %s" % (fp, e))
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _box(ax, x, y, w, h, text, fc, tc="white", fs=11):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fc,
                               edgecolor="#333333", lw=1.0, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, zorder=3, wrap=True)


def _arrow(ax, x1, y1, x2, y2, color="#1f5fa8"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6), zorder=1)


def fig39():
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 95, "GBK 乱码进 toast：子进程环境的两个出口", ha="center",
            fontsize=13, fontweight="bold", color="#222222")

    ax.text(25, 86, "修复前（无 PYTHONIOENCODING）", ha="center", fontsize=11,
            color="#a83232", fontweight="bold")
    _box(ax, 6, 70, 38, 9, "子进程 stdout\n按 GBK / cp936 写中文", "#a83232")
    _arrow(ax, 25, 70, 25, 59)
    _box(ax, 6, 50, 38, 9, "父进程按 UTF-8 解码\n(errors=replace)", "#c08040")
    _arrow(ax, 25, 50, 25, 39)
    _box(ax, 6, 30, 38, 9, "toast 显示乱码\n（问号 / 方块）", "#7a2020")

    ax.text(75, 86, "修复后（注入 utf-8）", ha="center", fontsize=11,
            color="#2f7d32", fontweight="bold")
    _box(ax, 56, 70, 38, 9, "子进程注入\nPYTHONIOENCODING=utf-8", "#2f7d32")
    _arrow(ax, 75, 70, 75, 59)
    _box(ax, 56, 50, 38, 9, "stdout 即 UTF-8\n字节流", "#3a8a3c")
    _arrow(ax, 75, 50, 75, 39)
    _box(ax, 56, 30, 38, 9, "父进程解出原中文\ntoast 正常", "#20591f")

    ax.text(50, 18, "同一句报错：「换嗓失败：B角音色认领未通过…」→ GBK 47 字节 / UTF-8 70 字节",
            ha="center", fontsize=10, color="#444444")
    ax.text(50, 11, "错配根因：子进程写 GBK、父进程解 UTF-8，编解码链路两端不一致",
            ha="center", fontsize=10, color="#444444")
    fig.tight_layout()
    out_p = os.path.join(HERE, "39_GBK乱码toast_fig1")
    fig.savefig(out_p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(out_p + ".svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig39()
    print("OK: 39 figure generated")
