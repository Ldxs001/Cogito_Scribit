# -*- coding: utf-8 -*-
"""《我写故我播》#40 配图生成（matplotlib + 黑体，PNG+SVG 双格式）。
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


def fig40():
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 96, "show_if 显隐：配置变更后界面如何跟着变", ha="center",
            fontsize=13, fontweight="bold", color="#222222")

    _box(ax, 4, 82, 30, 9, "配置值变更\n或卡片重建", "#1f5fa8")
    _arrow(ax, 34, 86, 42, 86)
    _box(ax, 42, 82, 30, 9, "applyShowIf()\n遍历登记表 REG", "#1f5fa8")
    _arrow(ax, 72, 86, 78, 86)
    _box(ax, 78, 82, 19, 9, "逐行取\nspec.show_if", "#1f5fa8")

    _arrow(ax, 87, 82, 87, 72)
    _box(ax, 66, 62, 30, 10, "showIfMatch：依赖键取值\n∈ 许可列表 ?", "#b5701f")
    _arrow(ax, 74, 62, 54, 57, color="#2f7d32")
    _box(ax, 44, 48, 16, 9, "否→ 隐藏", "#7a2020")
    _arrow(ax, 90, 62, 82, 57, color="#a83232")
    _box(ax, 74, 48, 16, 9, "是→ 显示", "#20591f")

    ax.text(50, 42, "bgm.mode 三个取值下，三组依赖行 display 实测（移植算法实跑）",
            ha="center", fontsize=10.5, color="#333333")
    rows = [
        ("依赖行 \\ 来源", "内置合成\nbuiltin", "AI 音乐库\nlibrary", "自备文件\nfile"),
        ("档位 bgm.level", "显示", "隐藏", "隐藏"),
        ("曲目 bgm.track", "隐藏", "显示", "隐藏"),
        ("自备文件 bgm.file", "隐藏", "隐藏", "显示"),
    ]
    x0, y0, cw, rh = 18, 8, 18, 7
    for j, head in enumerate(rows[0]):
        _box(ax, x0 + j * cw, y0 + 3 * rh, cw, rh, head, "#444444", fs=10)
    for i, r in enumerate(rows[1:], start=1):
        for j, cell in enumerate(r):
            col = "#20591f" if cell == "显示" else "#7a2020"
            _box(ax, x0 + j * cw, y0 + (3 - i) * rh, cw, rh, cell, col, fs=10)

    ax.text(50, 4, "任意键落值都重算一遍登记表（applyShowIf() 调用点 ≥ 3 处）",
            ha="center", fontsize=9.5, color="#666666")
    fig.tight_layout()
    out_p = os.path.join(HERE, "40_配置项显隐_fig1")
    fig.savefig(out_p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(out_p + ".svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig40()
    print("OK: 40 figure generated")
