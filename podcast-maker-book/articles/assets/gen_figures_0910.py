# -*- coding: utf-8 -*-
"""#9 / #10 配图生成（simhei 注册，PNG+SVG 双格式，遵循 STYLE_GUIDE §十二）。

落盘：articles/assets/{9,10}_*_fig1.{png,svg}
白底深字；盒内标题占首行、body 每行独占一行（行列账本），行高 ≥ 字号×1.9。
核心修正：竖向堆叠用「上盒底 - 间隔 - 下盒高」定新底，消除下盒高于上盒时的叠压。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fm.fontManager.addfont(r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

INK = "#222222"
SUB = "#555555"
RULE = "#444444"
ROW = 0.30           # 一行预算 0.30 英寸
GAP_V = 0.22         # 盒间竖向净距（英寸）
GAP_H = 0.22         # 列/行间距


def _box_height(n_body):
    return 0.18 + (1 + n_body) * ROW + 0.18


def draw_box(ax, x, y, w, h, title, body, fc="#f4f6f8", ec=RULE, tcol=INK, bcol=SUB):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.06",
                         linewidth=1.2, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.18 - ROW / 2, title,
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=tcol, zorder=3)
    for i, line in enumerate(body):
        ay = y + h - 0.18 - ROW * (1.5 + i)
        ax.text(x + w / 2, ay, line, ha="center", va="center",
                fontsize=10, color=bcol, zorder=3)


def arrow(ax, x1, y1, x2, y2, color=RULE, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                 arrowstyle="-|>", mutation_scale=22, linewidth=1.6,
                 edgecolor=color, facecolor=color, zorder=4,
                 connectionstyle="arc3,rad=%s" % rad))


def annotate(ax, x, y, text, color=INK, size=10, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=color,
            zorder=5)


def stack_bottoms(first_y, heights, gap=GAP_V):
    """给定首盒底 y 与盒高列表，返回每个盒的底 y（保持 gap 净距，不叠压）。"""
    ys = [first_y]
    y = first_y
    for h in heights[1:]:
        y -= h + gap
        ys.append(y)
    return ys


# =========================================================================
# 图 1：#9 段循环查重工序——修复前 vs 修复后
# =========================================================================
def fig9():
    fig, ax = plt.subplots(figsize=(11, 8.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8.0); ax.axis("off")

    col_a_x, col_b_x = 0.55, 6.05
    w = 4.55

    A = [
        ("段循环按段生成", ["写本段时前几段已定稿"]),
        ("首轮填充出稿", ["喂全篇已写正文", "首轮即可跨段复读"]),
        ("进容差即 break", ["收工；下一道工序开始"]),
        ("仅兜底删句", ["dedupe_script 删整段重复"]),
    ]
    B = [
        ("段循环按段生成", ["写本段时前几段已定稿"]),
        ("首段填充出稿", ["喂全篇已写正文"]),
        ("每段收口无条件查重", ["含首轮；本地比对", "查到才发一次替换"]),
        ("兜底零触发", ["正常期数不到这刀；", "整篇路另挂整篇自查"]),
    ]
    h_a = [_box_height(len(b)) for _, b in A]
    h_b = [_box_height(len(b)) for _, b in B]

    ys_a = stack_bottoms(7.05, h_a)
    ys_b = stack_bottoms(7.05, h_b)

    # 列标题（放在首盒上方，独立位置）
    annotate(ax, col_a_x + w / 2, ys_a[0] + h_a[0] + 0.35,
             "修复前：查重嵌在修正轮内",
             color="#9a3b3b", size=12, ha="center")
    annotate(ax, col_b_x + w / 2, ys_b[0] + h_b[0] + 0.35,
             "修复后：每段收口无条件",
             color="#2f6b3b", size=12, ha="center")

    for (xa, ya, a, h) in zip([col_a_x] * 4, ys_a, A, h_a):
        draw_box(ax, xa, ya, w, h, a[0], a[1])
    for (xb, yb, b, h) in zip([col_b_x] * 4, ys_b, B, h_b):
        draw_box(ax, xb, yb, w, h, b[0], b[1], fc="#eef3ee")

    # 列内竖向箭头
    for cx, hs, ys in [(col_a_x + w / 2, h_a, ys_a), (col_b_x + w / 2, h_b, ys_b)]:
        for i in range(len(hs) - 1):
            arrow(ax, cx, ys[i] - 0.02, cx, ys[i + 1] + hs[i + 1] + 0.02)

    # 修复点横向箭头：A2 → B2
    ya = ys_a[1] + h_a[1] / 2
    yb = ys_b[2] + h_b[2] / 2
    arrow(ax, col_a_x + w + 0.06, ya, col_b_x - 0.06, yb,
          color="#1f5fae", rad=0.12)
    annotate(ax, (col_a_x + w + col_b_x) / 2, max(ya, yb) + 0.45,
             "修复点：查重工序从修正轮内提到收口处（每段无条件，含首轮）",
             color="#1f5fae", size=10, ha="center")
    annotate(ax, (col_a_x + w + col_b_x) / 2, ys_b[3] - 0.35,
             "首轮进容差即 break → 复读原样漏到成片（仅兜底删句）",
             color="#9a3b3b", size=9.5, ha="center")

    fig.savefig("articles/assets/9_首轮复读绕过查重_fig1.png", dpi=150,
                bbox_inches="tight", facecolor="white")
    fig.savefig("articles/assets/9_首轮复读绕过查重_fig1.svg",
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig9 done")


# =========================================================================
# 图 1：#10 八张素材卡 → voice_of → 提示词（各自说话）
# =========================================================================
def fig10():
    fig, ax = plt.subplots(figsize=(11, 8.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8.0); ax.axis("off")

    cards = ["方法论", "叙事", "访谈", "散文", "论文", "教程", "编年", "auto(入口)"]
    cw = 2.40
    ch = _box_height(1)
    xs = [0.35 + i * (cw + 0.14) for i in range(4)]
    row1_y = 6.95
    row2_y = row1_y - ch - GAP_V
    for i, name in enumerate(cards[:4]):
        draw_box(ax, xs[i], row1_y, cw, ch, name, ["素材卡 · 文体块"], fc="#eef3ee")
    for i, name in enumerate(cards[4:]):
        draw_box(ax, xs[i], row2_y, cw, ch, name, ["素材卡 · 文体块"], fc="#eef3ee")

    # 八卡 → voice_of（单一合流箭头）
    mh = _box_height(2)
    mw = 7.2
    merge_y = row2_y - mh - GAP_V  # 关键修正：下盒顶 = 上盒底 - gap
    ax.add_patch(FancyArrowPatch(
        (5.5, row2_y - 0.02), (5.5, merge_y + mh + 0.02),
        arrowstyle="-|>", mutation_scale=26, linewidth=2.0,
        edgecolor=RULE, facecolor=RULE, zorder=4,
        connectionstyle="arc3,rad=0.0"))
    # 标签放在 arrow 正中间（gap 内），不顶下盒
    annotate(ax, 5.5, (row2_y + merge_y + mh) / 2,
             "八卡各自 voice 块", color=SUB, size=10, ha="center")

    draw_box(ax, 5.5 - mw / 2, merge_y, mw, mh,
             "voice_of：卡.voice 逐键合并 DEFAULT_VOICE",
             ["缺键落默认；读卡不改卡", "duty / cover / mapping / vocab 各自不同"],
             fc="#fdf6e3")

    # → script_engine 提示词
    ph = _box_height(2)
    pw = 8.0
    prompt_y = merge_y - ph - GAP_V
    arrow(ax, 5.5, merge_y - 0.02, 5.5, prompt_y + ph + 0.02)
    draw_box(ax, 5.5 - pw / 2, prompt_y, pw, ph,
             "script_engine 提示词：每卡文体四件套不同",
             ["讲解体卡 = 原讲解文案（逐字一致）",
              "小说卡 = 评书块；demo/demo_bad 各归各卡"],
             fc="#f4f6f8")

    # resolve_form 三级链
    rw = 2.8
    rh = _box_height(2)
    rxs = [0.35, 4.1, 7.85]
    labels = ["① 人选项目", "② 卡默认 form", "③ DEFAULT_FORM"]
    sublabels = [
        ["script.dialogue_form", "非空且认得"],
        ["card['form']", "认得才用"],
        ["qa（兜底）", "不让没选落空值"],
    ]
    resolve_y = prompt_y - rh - GAP_V
    for x, title, body in zip(rxs, labels, sublabels):
        draw_box(ax, x, resolve_y, rw, rh, title, body, fc="#eef3ee")
    arrow(ax, rxs[0] + rw + 0.03, resolve_y + rh / 2,
          rxs[1] - 0.03, resolve_y + rh / 2, color="#1f5fae")
    arrow(ax, rxs[1] + rw + 0.03, resolve_y + rh / 2,
          rxs[2] - 0.03, resolve_y + rh / 2, color="#1f5fae")
    annotate(ax, 5.5, resolve_y - 0.35,
             "resolve_form 三级顺序（取值只有这一处，门禁与提示词同源）",
             color="#1f5fae", size=9.5, ha="center")

    # 站位/节奏 注解
    annotate(ax, 5.5, 0.55,
             "站位归卡、节奏归对话形式：形式选了也顶不掉卡上站位，卡与卡各说各话",
             color=SUB, size=9.5, ha="center")

    fig.savefig("articles/assets/10_文体块分卡_fig1.png", dpi=150,
                bbox_inches="tight", facecolor="white")
    fig.savefig("articles/assets/10_文体块分卡_fig1.svg",
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("fig10 done")


if __name__ == "__main__":
    fig9()
    fig10()
