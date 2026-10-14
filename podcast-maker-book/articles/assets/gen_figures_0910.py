# -*- coding: utf-8 -*-
"""#9 / #10 配图生成（simhei 注册，PNG+SVG 双格式，遵循 STYLE_GUIDE §十二）。

落盘：articles/assets/{9,10}_*_fig1.{png,svg}
白底深字；盒内标题占首行、body 每行独占一行（行列账本 §1）。
关键合规：盒间缝宽 GAP_V=0.40 > 箭头头占宽(≈0.22)，箭头带杆可见（§2）；
注释与箭头/盒净距 ≥ 0.6 行高（§3）；动线正交、落点落盒缘（§7）。
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
GAP_V = 0.40         # 盒间竖向净距（> 箭头头占宽，保证带杆可见）
MUT = 14             # 箭头头 mutation_scale（缩小，避免吞缝）


def _box_height(n_body):
    return 0.18 + (1 + n_body) * ROW + 0.18


def stack_bottoms(first_y, heights, gap=GAP_V):
    """给定首盒底 y 与盒高列表，返回每个盒的底 y（保持 gap 净距，不叠压）。"""
    ys = [first_y]
    y = first_y
    for h in heights[1:]:
        y -= h + gap
        ys.append(y)
    return ys


# -------------------------------------------------------------------------
# 元素构造（供绘制与验证共用，避免几何漂移）
# -------------------------------------------------------------------------
def build_fig9():
    elements = {"boxes": [], "arrows": [], "texts": []}
    col_a_x, col_b_x = 0.55, 6.05
    w = 4.55
    first_y = 7.3
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
    ys_a = stack_bottoms(first_y, h_a)
    ys_b = stack_bottoms(first_y, h_b)

    for (xa, ya, (title, b), h) in zip([col_a_x] * 4, ys_a, A, h_a):
        elements["boxes"].append({"x": xa, "y": ya, "w": w, "h": h, "title": title, "body": b, "fc": "#f4f6f8"})
    for (xb, yb, (title, b), h) in zip([col_b_x] * 4, ys_b, B, h_b):
        elements["boxes"].append({"x": xb, "y": yb, "w": w, "h": h, "title": title, "body": b, "fc": "#eef3ee"})

    # 列标题
    elements["texts"].append({"x": col_a_x + w / 2, "y": ys_a[0] + h_a[0] + 0.32, "s": "修复前：查重嵌在修正轮内", "size": 12, "color": "#9a3b3b", "weight": "bold"})
    elements["texts"].append({"x": col_b_x + w / 2, "y": ys_b[0] + h_b[0] + 0.32, "s": "修复后：每段收口无条件", "size": 12, "color": "#2f6b3b", "weight": "bold"})

    # 列内竖向箭头（上盒底 -0.03 → 下盒顶 +0.03）
    for cx, hs, ys in [(col_a_x + w / 2, h_a, ys_a), (col_b_x + w / 2, h_b, ys_b)]:
        for i in range(len(hs) - 1):
            elements["arrows"].append({
                "x1": cx, "y1": ys[i] - 0.03, "x2": cx, "y2": ys[i + 1] + hs[i + 1] + 0.03, "color": RULE, "rad": 0.0})

    # 修复点横向箭头：A2 右缘 → B2 左缘
    ya = ys_a[1] + h_a[1] / 2
    yb = ys_b[2] + h_b[2] / 2
    elements["arrows"].append({
        "x1": col_a_x + w + 0.05, "y1": ya, "x2": col_b_x - 0.05, "y2": yb, "color": "#1f5fae", "rad": 0.10})
    # 修复点注释（放在两列之间下方净带，不压箭头/盒，§3 净距）
    elements["texts"].append({"x": 5.575, "y": 3.55, "s": "修复点：查重工序提至段收口（含首轮）", "size": 10, "color": "#1f5fae", "weight": "normal"})
    elements["texts"].append({"x": 5.575, "y": 2.20, "s": "首轮进容差即 break → 复读漏到成片（仅兜底删句）", "size": 9.5, "color": "#9a3b3b", "weight": "normal"})
    return elements, (11, 9.0)


def build_fig10():
    elements = {"boxes": [], "arrows": [], "texts": []}
    cards = ["方法论", "叙事", "访谈", "散文", "论文", "教程", "编年", "auto(入口)"]
    cw = 2.40
    ch = _box_height(1)
    xs = [0.35 + i * (cw + 0.14) for i in range(4)]
    row1_y = 7.3
    row2_y = row1_y - ch - GAP_V
    for i, name in enumerate(cards[:4]):
        elements["boxes"].append({"x": xs[i], "y": row1_y, "w": cw, "h": ch, "title": name, "body": ["素材卡 · 文体块"], "fc": "#eef3ee"})
    for i, name in enumerate(cards[4:]):
        elements["boxes"].append({"x": xs[i], "y": row2_y, "w": cw, "h": ch, "title": name, "body": ["素材卡 · 文体块"], "fc": "#eef3ee"})

    mh = _box_height(2); mw = 7.2
    merge_y = row2_y - mh - GAP_V
    elements["boxes"].append({"x": 5.5 - mw / 2, "y": merge_y, "w": mw, "h": mh,
                              "title": "voice_of：卡.voice 逐键合并 DEFAULT_VOICE",
                              "body": ["缺键落默认；读卡不改卡", "duty / cover / mapping / vocab 各自不同"], "fc": "#fdf6e3"})

    ph = _box_height(2); pw = 8.0
    prompt_y = merge_y - ph - GAP_V
    elements["boxes"].append({"x": 5.5 - pw / 2, "y": prompt_y, "w": pw, "h": ph,
                              "title": "script_engine 提示词：每卡文体四件套不同",
                              "body": ["讲解体卡 = 原讲解文案（逐字一致）", "小说卡 = 评书块；demo/demo_bad 各归各卡"], "fc": "#f4f6f8"})

    rw = 2.8; rh = _box_height(2); rxs = [0.35, 4.1, 7.85]
    labels = ["① 人选项目", "② 卡默认 form", "③ DEFAULT_FORM"]
    sub = [["script.dialogue_form", "非空且认得"], ["card['form']", "认得才用"], ["qa（兜底）", "不让没选落空值"]]
    resolve_y = prompt_y - rh - GAP_V
    for x, title, body in zip(rxs, labels, sub):
        elements["boxes"].append({"x": x, "y": resolve_y, "w": rw, "h": rh, "title": title, "body": body, "fc": "#eef3ee"})

    # 八卡 → voice_of（单一合流箭头，起止于盒缘，§7 落点落元素）
    elements["arrows"].append({"x1": 5.5, "y1": row2_y - 0.03, "x2": 5.5, "y2": merge_y + mh + 0.03, "color": RULE, "rad": 0.0})
    # voice_of → 提示词
    elements["arrows"].append({"x1": 5.5, "y1": merge_y - 0.03, "x2": 5.5, "y2": prompt_y + ph + 0.03, "color": RULE, "rad": 0.0})
    # resolve 三级横向箭头
    for i in range(2):
        elements["arrows"].append({"x1": rxs[i] + rw + 0.04, "y1": resolve_y + rh / 2,
                                   "x2": rxs[i + 1] - 0.04, "y2": resolve_y + rh / 2, "color": "#1f5fae", "rad": 0.0})

    # 注释（净带，不压箭头/盒）
    gap_center_1 = (row2_y + (merge_y + mh)) / 2  # 八卡→voice_of 缝中心
    elements["texts"].append({"x": 3.0, "y": gap_center_1, "s": "八卡各自 voice 块", "size": 10, "color": SUB, "weight": "normal"})
    elements["texts"].append({"x": 5.5, "y": resolve_y - 0.32, "s": "resolve_form 三级顺序（取值同源）", "size": 9.5, "color": "#1f5fae", "weight": "normal"})
    elements["texts"].append({"x": 5.5, "y": 0.35, "s": "站位归卡、节奏归对话形式：卡与卡各说各话", "size": 9.5, "color": SUB, "weight": "normal"})
    return elements, (11, 9.0)


def _draw_elements(ax, elements):
    for b in elements["boxes"]:
        box = FancyBboxPatch((b["x"], b["y"]), b["w"], b["h"],
                             boxstyle="round,pad=0.02,rounding_size=0.06",
                             linewidth=1.2, edgecolor=RULE, facecolor=b["fc"], zorder=2)
        ax.add_patch(box)
        ax.text(b["x"] + b["w"] / 2, b["y"] + b["h"] - 0.18 - ROW / 2, b["title"],
                 ha="center", va="center", fontsize=11, fontweight="bold",
                 color=INK, zorder=3)
        for i, line in enumerate(b["body"]):
            ay = b["y"] + b["h"] - 0.18 - ROW * (1.5 + i)
            ax.text(b["x"] + b["w"] / 2, ay, line, ha="center", va="center",
                    fontsize=10, color=SUB, zorder=3)
    for a in elements["arrows"]:
        ax.add_patch(FancyArrowPatch((a["x1"], a["y1"]), (a["x2"], a["y2"]),
                     arrowstyle="-|>", mutation_scale=MUT, linewidth=1.5,
                     edgecolor=a["color"], facecolor=a["color"], zorder=4,
                     connectionstyle="arc3,rad=%s" % a["rad"]))
    for t in elements["texts"]:
        ax.text(t["x"], t["y"], t["s"], ha="center", va="center", fontsize=t["size"],
                color=t["color"], fontweight=t.get("weight", "normal"), zorder=5)


def save(elements, fs, path_png, path_svg):
    fig, ax = plt.subplots(figsize=fs)
    ax.set_xlim(0, 11); ax.set_ylim(0, fs[1]); ax.axis("off")
    _draw_elements(ax, elements)
    fig.savefig(path_png, dpi=150, bbox_inches="tight", facecolor="white")
    fig.savefig(path_svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gen():
    e9, fs9 = build_fig9()
    save(e9, fs9, "articles/assets/9_首轮复读绕过查重_fig1.png", "articles/assets/9_首轮复读绕过查重_fig1.svg")
    e10, fs10 = build_fig10()
    save(e10, fs10, "articles/assets/10_文体块分卡_fig1.png", "articles/assets/10_文体块分卡_fig1.svg")
    print("fig9 done / fig10 done")


if __name__ == "__main__":
    gen()
