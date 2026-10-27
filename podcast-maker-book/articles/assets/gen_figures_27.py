# podcast-maker-book/articles/assets/gen_figures_27.py
# 生成 #27《BGM 转译层》两张配图（PNG + SVG），数据来自真实 stub-LLM 实验与 CHANGELOG 真机实测。
# 测量条件：仓的临时副本 / podcast-maker v2.8.0 源码 / 2026-10-22。

import os
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FONT = "C:/Windows/Fonts/simhei.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))


def save(fig, slug, n):
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "%s_fig%d.%s" % (slug, n, ext)),
                    dpi=160, bbox_inches="tight")
    plt.close(fig)


def _node(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.04",
                                linewidth=1.2, edgecolor="#333",
                                facecolor=color))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=9.2, color="#1a1a1a", wrap=True)


def _arrow(ax, x1, y1, x2, y2, color="#444"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.4, color=color))


# ---------------------------------------------------------------- fig1
# CoT 劫持 vs 修复：转译稿怎么被内部 LM 改写、又怎么被四 False 救回。
def fig1():
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.2); ax.axis("off")

    ax.text(5, 6.85, "BGM 转译层：caption 被内部 LM 劫持 vs 四 False 救回",
            ha="center", fontsize=12.5, fontweight="bold")

    # 上轨：劫持（红）
    ax.text(5, 6.0, "—— 劫持路径（thinking=True，真机日志实锤）——",
            ha="center", fontsize=10, color="#a33")
    _node(ax, 0.2, 5.05, 3.0, 0.7, "主程序转译稿\n「低音诡异·无鼓」", "#f0d6d6")
    _node(ax, 3.6, 5.05, 3.0, 0.7, "Phase1 CoT（内部 0.6B LM）\n改写成「energetic\nsynthwave + drum」", "#e7b0b0")
    _node(ax, 7.0, 5.05, 2.8, 0.7, "官方 inference.py:826\n用 LM 覆盖 DiT 输入", "#d98a8a")
    _arrow(ax, 3.2, 5.4, 3.6, 5.4, "#a33")
    _arrow(ax, 6.6, 5.4, 7.0, 5.4, "#a33")
    ax.text(5, 4.55, "→ 生成方向整段被劫持，与用户意图相反", ha="center",
            fontsize=9.5, color="#a33")

    # 下轨：修复（绿）
    ax.text(5, 3.7, "—— 修复路径（thinking=False + use_cot 三连 False）——",
            ha="center", fontsize=10, color="#2c7a2c")
    _node(ax, 0.2, 2.75, 3.0, 0.7, "主程序转译稿\n「低音诡异·无鼓」", "#d6ecd6")
    _node(ax, 3.6, 2.75, 3.0, 0.7, "四 False → 官方判定\nuse_lm=False\nLM 整段跳过", "#aedcaa")
    _node(ax, 7.0, 2.75, 2.8, 0.7, "DiT 直接吃转译稿\n方向保真", "#88c98a")
    _arrow(ax, 3.2, 3.1, 3.6, 3.1, "#2c7a2c")
    _arrow(ax, 6.6, 3.1, 7.0, 3.1, "#2c7a2c")
    ax.text(5, 2.25, "→ 描述理解全由主程序 LLM 转译层完成，DiT 不再被改写",
            ha="center", fontsize=9.5, color="#2c7a2c")

    ax.text(5, 1.2, "副产物：每条生成省掉 tokenizer + LM 加载与 Phase 1/2 约 40 秒",
            ha="center", fontsize=9, color="#555")
    save(fig, "27_bgm", 1)


# ---------------------------------------------------------------- fig2
# 维度归位：中文口语四维 → 英文执行域（实测真实 LLM 同一描述四归位）。
def fig2():
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.text(5, 5.7, "转译层维度归位：中文口语四维 → 英文执行域",
            ha="center", fontsize=12.5, fontweight="bold")
    ax.text(5, 5.15, "示例输入：「温暖但简单，稚嫩而优雅」", ha="center",
            fontsize=10, color="#333")

    rows = [
        ("氛围（整体情绪色调）", "atmosphere / mood", "warm atmosphere", "#bcd3e8"),
        ("形式（编曲繁简）", "arrangement", "simple minimal arrangement", "#cfe3cf"),
        ("音色（什么在发声）", "instrument / timbre", "childlike soft timbre", "#e3d6cf"),
        ("格调（演绎品质）", "melodic / tone 实体", "graceful melodic delivery", "#e3cfdc"),
    ]
    y = 4.3
    for zh, dom, en, col in rows:
        _node(ax, 0.2, y - 0.35, 3.5, 0.7, zh, col)
        _node(ax, 4.0, y - 0.35, 2.7, 0.7, dom, "#ededd6")
        _node(ax, 7.0, y - 0.35, 2.8, 0.7, en, "#d6e3e8")
        _arrow(ax, 3.7, y, 4.0, y, "#555")
        _arrow(ax, 6.7, y, 7.0, y, "#555")
        y -= 1.0

    ax.text(5, 0.4, "禁止跨维打包成无执行实体的抽象短语（反例：simple yet elegant sound changes）",
            ha="center", fontsize=9, color="#a33")
    save(fig, "27_bgm", 2)


if __name__ == "__main__":
    fig1()
    fig2()
    print("OK 27 figures")
