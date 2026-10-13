# -*- coding: utf-8 -*-
"""#1 九步管线 与 #2 配置总表驱动 两篇配图。
matplotlib + 文泉/黑体，输出 PNG + SVG 到 articles/assets/。
字体回退：先试 simhei，缺失则用系统可用中文 ttf，再缺失则纯英文标签。
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = [
    r"C:/Windows/Fonts/simhei.ttf",
    r"C:/Windows/Fonts/msyh.ttc",
    r"C:/Windows/Fonts/simfang.ttf",
]


def setup_font():
    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            try:
                matplotlib.font_manager.fontManager.addfont(fp)
                name = matplotlib.font_manager.FontProperties(fname=fp).get_name()
                plt.rcParams["font.sans-serif"] = [name]
                plt.rcParams["axes.unicode_minus"] = False
                return name
            except Exception:
                continue
    return None


FONT = setup_font()
print("font:", FONT)


def _box(ax, x, y, w, h, text, fc, ec="#2b3a55"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.03",
                                fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=9.5, color="#16213a", weight="bold")


def _arrow(ax, x1, y1, x2, y2, color="#2b3a55"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                 arrowstyle="-|>", mutation_scale=14,
                 lw=1.6, color=color))


# ---------------------------------------------------------------- Fig #1
def fig_pipeline():
    steps = [
        ("1 脚本", "取定稿稿\n(合成不写稿)", 0.05, "#dbe7ff"),
        ("2 背景/封面/音乐", "静帧预烘焙+\nBGM生成", 0.15, "#cfeede"),
        ("3 语音合成", "edge-tts /\nQwen3-TTS", 0.30, "#ffe9cf"),
        ("4 音频后处理", "拼接/降噪/\n响度归一", 0.45, "#ffd6d6"),
        ("5 导出音频", "ffmpeg 编码\n落盘", 0.55, "#e8d6ff"),
        ("6 字幕", "四级断行\nSRT/ASS", 0.62, "#d6f0ff"),
        ("7 合成视频", "横屏+竖屏\n烧录字幕", 0.70, "#fff3c4"),
        ("8 文章与清单", "公众号图文\n+产物清单", 0.95, "#d3f0e0"),
        ("9 完成", "记账+\n校验报告", 1.00, "#c9e8ff"),
    ]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.2, 6.4),
                                   gridspec_kw={"height_ratios": [3.0, 1.4]})
    ax1.axis("off")
    ax2.axis("off")
    n = len(steps)
    w = 1.06
    gap = 0.18
    total_w = n * w + (n - 1) * gap
    x0 = (12.4 - total_w) / 2
    y0 = 1.55
    h = 1.05
    for i, (title, sub, prog, fc) in enumerate(steps):
        x = x0 + i * (w + gap)
        _box(ax1, x, y0, w, h, title, fc)
        ax1.text(x + w / 2, y0 - 0.18, sub, ha="center", va="top",
                 fontsize=7.6, color="#33415c")
        if i < n - 1:
            _arrow(ax1, x + w + 0.01, y0 + h / 2, x + w + gap - 0.01, y0 + h / 2)
        # progress weight axis
        ax2.add_patch(plt.Rectangle((x, 0.2), w, 0.55, fc=fc, ec="#2b3a55"))
        ax2.text(x + w / 2, 0.475, "%.2f" % prog, ha="center", va="center",
                 fontsize=7.8, color="#16213a")
    ax2.plot([x0, x0 + total_w], [0.95, 0.95], color="#2b3a55", lw=1.0, ls="--")
    ax2.text(x0, 1.02, "进度权重（累积到 1.0，第 9 步收口）", fontsize=8, color="#33415c")
    ax1.set_xlim(0, 12.4)
    ax1.set_ylim(0, 3.2)
    ax2.set_xlim(0, 12.4)
    ax2.set_ylim(0, 1.3)
    fig.suptitle("图 1 · 九步管线：脚本→声音→字幕→画面→产物（pipeline._run_episode）",
                 fontsize=11, weight="bold", color="#16213a")
    out_png = os.path.join(HERE, "1_九步管线_fig1.png")
    out_svg = os.path.join(HERE, "1_九步管线_fig1.svg")
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_png, out_svg)


# ---------------------------------------------------------------- Fig #2
def fig_config_chain():
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax.axis("off")
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 7.2)
    # central definition
    _box(ax, 4.6, 4.4, 3.2, 1.5, "PARAM_SPEC\n(一处定义)", "#ffe9cf")
    ax.text(6.2, 4.2, "type / min / max / step /\ndefault / label / views / group",
            ha="center", va="top", fontsize=7.6, color="#33415c")
    # UI consumer
    _box(ax, 0.7, 1.4, 3.4, 1.5, "界面\nui_payload / coerce /\n_views_of / section_of", "#dbe7ff")
    # pipeline consumer
    _box(ax, 8.3, 1.4, 3.4, 1.5, "管线\nget / set / apply_to_config\n/ default_config", "#d3f0e0")
    _arrow(ax, 4.6, 4.4, 1.7, 2.9)
    _arrow(ax, 7.8, 4.4, 10.3, 2.9)
    ax.text(2.5, 3.5, "读同一份", fontsize=8, color="#33415c", rotation=58)
    ax.text(9.9, 3.5, "读同一份", fontsize=8, color="#33415c", rotation=-58)
    # CONFIG_PASS_THROUGH channel
    _box(ax, 4.6, 0.5, 3.2, 1.1,
         "CONFIG_PASS_THROUGH\n(通道键：项目设定→配置副本)", "#e8d6ff")
    _arrow(ax, 4.6, 1.6, 4.6, 2.55, color="#7a4fb0")
    _arrow(ax, 6.2, 1.6, 6.2, 2.55, color="#7a4fb0")
    ax.text(8.0, 1.05, "只送不配：不是配置点位", fontsize=7.6, color="#5a3a8a")
    # guard note
    ax.text(6.2, 6.7, "一处定义 → 界面与管线两处消费，通道键单列且不得同时是配置点位",
            ha="center", fontsize=9, weight="bold", color="#16213a")
    ax.text(6.2, 6.35, "（test_config_keys / test_project_store 对账守卫）",
            ha="center", fontsize=7.8, color="#33415c")
    fig.suptitle("图 1 · 配置总表一处定义，界面与管线读同一份数据",
                 fontsize=11, weight="bold", color="#16213a")
    out_png = os.path.join(HERE, "2_配置总表驱动_fig1.png")
    out_svg = os.path.join(HERE, "2_配置总表驱动_fig1.svg")
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_png, out_svg)


if __name__ == "__main__":
    fig_pipeline()
    fig_config_chain()
