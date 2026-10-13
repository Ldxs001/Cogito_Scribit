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
            fontsize=8.0, color="#16213a", weight="bold")


def _arrow(ax, x1, y1, x2, y2, color="#2b3a55"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                 arrowstyle="-|>", mutation_scale=14,
                 lw=1.6, color=color))


# ---------------------------------------------------------------- Fig #1
def fig_pipeline():
    steps = [
        ("1 脚本", "取定稿稿\n(合成不写稿)", 0.05, "#dbe7ff"),
        ("2 背景/封面\n音乐", "静帧预烘焙+\nBGM生成", 0.15, "#cfeede"),
        ("3 语音合成", "edge-tts /\nQwen3-TTS", 0.30, "#ffe9cf"),
        ("4 音频后处理", "拼接/降噪/\n响度归一", 0.45, "#ffd6d6"),
        ("5 导出音频", "ffmpeg 编码\n落盘", 0.55, "#e8d6ff"),
        ("6 字幕", "四级断行\nSRT/ASS", 0.62, "#d6f0ff"),
        ("7 合成视频", "横屏+竖屏\n烧录字幕", 0.70, "#fff3c4"),
        ("8 文章与清单", "公众号图文\n+产物清单", 0.95, "#d3f0e0"),
        ("9 完成", "记账+\n校验报告", 1.00, "#c9e8ff"),
    ]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12.2, 6.4),
                                   gridspec_kw={"height_ratios": [3.0, 1.4]})
    ax1.axis("off")
    ax2.axis("off")
    n = len(steps)
    w = 1.14
    gap = 0.34                                   # 缝宽必须 > 箭头头长(~0.14u)，否则箭头被盒边吞掉
    total_w = n * w + (n - 1) * gap
    x0 = (13.6 - total_w) / 2
    y0 = 1.55
    h = 1.05
    for i, (title, sub, prog, fc) in enumerate(steps):
        x = x0 + i * (w + gap)
        _box(ax1, x, y0, w, h, title, fc)
        ax1.text(x + w / 2, y0 - 0.18, sub, ha="center", va="top",
                 fontsize=7.6, color="#33415c")
        if i < n - 1:
            _arrow(ax1, x + w + 0.03, y0 + h / 2, x + w + gap - 0.03, y0 + h / 2)
        # progress weight axis
        ax2.add_patch(plt.Rectangle((x, 0.2), w, 0.55, fc=fc, ec="#2b3a55"))
        ax2.text(x + w / 2, 0.475, "%.2f" % prog, ha="center", va="center",
                 fontsize=7.8, color="#16213a")
    ax2.plot([x0, x0 + total_w], [0.95, 0.95], color="#2b3a55", lw=1.0, ls="--")
    ax2.text(x0, 1.02, "进度权重（累积到 1.0，第 9 步收口）", fontsize=8, color="#33415c")
    ax1.set_xlim(0, 13.6)
    ax1.set_ylim(0.55, 3.2)                      # 底收至 0.55：副注最低行 ~0.95，消除死空带
    ax2.set_xlim(0, 13.6)
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

    # 顶层守门注（挂画布顶，两行，中轴对齐）
    ax.text(6.2, 6.7, "一处定义 → 界面与管线两处消费，通道键单列且不得同时是配置点位",
            ha="center", fontsize=9, weight="bold", color="#16213a")
    ax.text(6.2, 6.35, "（test_config_keys / test_project_store 对账守卫）",
            ha="center", fontsize=7.8, color="#33415c")

    # 第一层：一处定义（字段清单收进盒内分行，不悬空盒外）
    _box(ax, 4.2, 4.35, 4.0, 1.5, "", "#ffe9cf")
    ax.text(6.2, 5.52, "PARAM_SPEC（一处定义）", ha="center", va="center",
            fontsize=9, color="#16213a", weight="bold")
    ax.text(6.2, 5.10, "type / min / max / step\ndefault / label / views / group",
            ha="center", va="top", fontsize=7.6, color="#33415c")

    # 第二层：两处消费（垂直箭头、水平标签走净带，起点落点都落在元素上）
    _box(ax, 1.3, 2.0, 3.6, 1.5, "界面\nui_payload / coerce /\n_views_of / section_of", "#dbe7ff")
    _box(ax, 7.5, 2.0, 3.6, 1.5, "管线\nget / set / apply_to_config\n/ default_config", "#d3f0e0")
    _arrow(ax, 4.6, 4.35, 4.6, 3.55)
    _arrow(ax, 7.8, 4.35, 7.8, 3.55)
    ax.text(4.75, 3.95, "读同一份", ha="left", va="center", fontsize=8, color="#33415c")
    ax.text(7.95, 3.95, "读同一份", ha="left", va="center", fontsize=8, color="#33415c")

    # 第三层：通道键（斜向短箭头有明确落点——指向两消费盒底边）
    _box(ax, 4.45, 0.55, 3.5, 1.0,
         "CONFIG_PASS_THROUGH\n（通道键：项目设定→配置副本）", "#e8d6ff")
    _arrow(ax, 5.1, 1.55, 4.1, 1.95, color="#7a4fb0")
    _arrow(ax, 7.3, 1.55, 8.3, 1.95, color="#7a4fb0")
    ax.text(6.2, 0.35, "只送不配：不是配置点位", ha="center", va="top",
            fontsize=7.6, color="#5a3a8a")          # 注挂盒正下方，不漂浮

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
