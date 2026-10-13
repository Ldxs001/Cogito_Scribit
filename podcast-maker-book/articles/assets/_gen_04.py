# -*- coding: utf-8 -*-
"""《我写故我播》#04 配图生成脚本（与成稿同源，留档复核）。
fig1：MODE_SPEC 接驳表双语义示意（一处定义 -> 界面语义 + 管线语义两路消费）
数据来自 podcast-maker · CHANGELOG.md（v0.41.0 · 接驳表两种语义）
与 podcast_maker/config_manager.py:MODE_SPEC L282；详见 articles/4_MODE_SPEC双语义.md。
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FONT = r"C:/Windows/Fonts/simhei.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.dirname(os.path.abspath(__file__))


def _box(ax, x, y, w, h, text, fc, ec="#333", fs=10, weight="normal"):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.04",
                         fc=fc, ec=ec, lw=1.2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fs, weight=weight, color="#1a1a1a")


def fig1():
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    _box(ax, 3.4, 9.6, 3.2, 1.3,
         "MODE_SPEC（一处定义）\n同一批配置，两种语义",
         fc="#dbe4f0", fs=11, weight="bold")
    _box(ax, 0.4, 5.6, 3.6, 2.4,
         "界面语义（人读）\nlabel 给下拉框显示\n\n"
         "single：单行滚动\nlyric：歌词\nanimation：静止/缓推/波形/频谱\nbgm：15 档中文名",
         fc="#e7f0e7", fs=9.5)
    _box(ax, 6.0, 5.6, 3.6, 2.4,
         "管线语义（引擎消费）\noptions 子值直接送渲染/合成\n\n"
         "single.axis=x, window=1\nlyric.axis=y（框高=行数×行距）\n"
         "background.bg_top/bg_bottom/accent\nllm.backend.default_base_url",
         fc="#f0e7e7", fs=9.5)

    ax.add_patch(FancyArrowPatch((5.0, 9.6), (2.2, 8.0),
                 arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4))
    ax.add_patch(FancyArrowPatch((5.0, 9.6), (7.8, 8.0),
                 arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4))

    ax.text(5.0, 4.7, "接驳表：同一批配置两种语义（v0.41.0 字幕档）",
            ha="center", va="center", fontsize=10, weight="bold", color="#333")
    rows = [
        "margin_lr      单双行=文字距左右    | 歌词=框宽（兼折行容量）",
        "margin_v       单双行=文字距底边    | 歌词=框底距底边",
        "bg_alpha       单双行=每行填充块    | 歌词=整块框透明度",
        "outline        单双行=填充块内边距   | 歌词=不适用（仅单双行生效）",
        "lyric_max_rows 歌词=框高=行数×行距",
    ]
    y = 4.1
    for r in rows:
        ax.text(0.2, y, r, ha="left", va="center", fontsize=8.4)
        y -= 0.52

    ax.set_title("MODE_SPEC：一处定义、双语义接驳（界面 与 管线）",
                 fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "4_MODE_SPEC双语义_fig1.png"), dpi=150)
    fig.savefig(os.path.join(OUT, "4_MODE_SPEC双语义_fig1.svg"))
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    print("OK: 4 fig1 generated")
