# -*- coding: utf-8 -*-
"""§十二 §5 探针：实测 matplotlib 文本渲染宽 + 盒间净距，判 PASS/FAIL。
核心：overlap = 上盒底(y_i + h_i) - 下盒顶(y_{i+1} + h_{i+1})，>0 即叠压。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
import os

fm.fontManager.addfont(r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

INK = "#222222"; SUB = "#555555"; RULE = "#444444"; ROW = 0.30; GAP_V = 0.22

def _box_height(n_body):
    return 0.18 + (1 + n_body) * ROW + 0.18

def draw_box(ax, x, y, w, h, title, body, fc="#f4f6f8", ec=RULE, tcol=INK, bcol=SUB):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                         linewidth=1.2, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(box)
    t = ax.text(x + w / 2, y + h - 0.18 - ROW / 2, title, ha="center", va="center",
                fontsize=11, fontweight="bold", color=tcol, zorder=3)
    ext = t.get_window_extent(renderer=ax.figure.canvas.get_renderer())
    inv = ax.transData.inverted()
    tw_data = inv.transform((ext.x1, 0))[0] - inv.transform((ext.x0, 0))[0]
    res = {"title_w": tw_data, "title_overflow": tw_data > (w - 2*0.18)}
    body_exts = []
    for i, line in enumerate(body):
        ay = y + h - 0.18 - ROW * (1.5 + i)
        tt = ax.text(x + w / 2, ay, line, ha="center", va="center", fontsize=10,
                     color=bcol, zorder=3)
        e = tt.get_window_extent(renderer=ax.figure.canvas.get_renderer())
        bw_data = inv.transform((e.x1, 0))[0] - inv.transform((e.x0, 0))[0]
        body_exts.append((line, bw_data, bw_data > (w - 2*0.18)))
    res["body"] = body_exts
    res["bbox"] = (x, y, w, h)
    return res

def check_width(r, context):
    issues = []
    if r["title_overflow"]:
        issues.append(f"{context} 标题溢出 {r['title_w']:.2f}>{r['bbox'][2]-0.36:.2f}")
    for line, bw, ov in r["body"]:
        if ov:
            issues.append(f"{context} body溢出: {line} {bw:.2f}>{r['bbox'][2]-0.36:.2f}")
    return issues

def check_overlap(boxes, context):
    """boxes: list of (x,y,w,h)"""
    issues = []
    for i in range(len(boxes)-1):
        x1,y1,w1,h1 = boxes[i]
        x2,y2,w2,h2 = boxes[i+1]
        # 只检查竖向同列/同行堆叠；若 x 不同则不是堆叠关系
        if abs(x1-x2) > 0.01:
            continue
        top_lower = y2 + h2
        bottom_upper = y1
        overlap = bottom_upper - top_lower
        if overlap < 0.05:  # 允许 0.05 英寸制造误差
            issues.append(f"{context} 盒{i}底与盒{i+1}顶净距 {overlap:.2f}<0.05 叠压")
    return issues

def probe_fig9():
    fig, ax = plt.subplots(figsize=(11, 8.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8.0); ax.axis("off")
    fig.canvas.draw()
    col_a_x, col_b_x = 0.55, 6.05; w = 4.55
    A = [("段循环按段生成", ["写本段时前几段已定稿"]),
         ("首轮填充出稿", ["喂全篇已写正文", "首轮即可跨段复读"]),
         ("进容差即 break", ["收工；下一道工序开始"]),
         ("仅兜底删句", ["dedupe_script 删整段重复"])]
    B = [("段循环按段生成", ["写本段时前几段已定稿"]),
         ("首段填充出稿", ["喂全篇已写正文"]),
         ("每段收口无条件查重", ["含首轮；本地比对", "查到才发一次替换"]),
         ("兜底零触发", ["正常期数不到这刀；", "整篇路另挂整篇自查"])]
    h_a = [_box_height(len(b)) for _, b in A]
    h_b = [_box_height(len(b)) for _, b in B]

    def stack(first_y, heights):
        ys = [first_y]; y = first_y
        for h in heights[1:]:
            y -= h + GAP_V; ys.append(y)
        return ys
    ys_a = stack(7.05, h_a); ys_b = stack(7.05, h_b)

    issues = []
    boxes_a = []; boxes_b = []
    for xa, ya, (title,b), h in zip([col_a_x]*4, ys_a, A, h_a):
        r = draw_box(ax, xa, ya, w, h, title, b)
        issues.extend(check_width(r, "#9A"+title))
        boxes_a.append((xa, ya, w, h))
    for xb, yb, (title,b), h in zip([col_b_x]*4, ys_b, B, h_b):
        r = draw_box(ax, xb, yb, w, h, title, b, fc="#eef3ee")
        issues.extend(check_width(r, "#9B"+title))
        boxes_b.append((xb, yb, w, h))
    issues.extend(check_overlap(boxes_a, "#9A列"))
    issues.extend(check_overlap(boxes_b, "#9B列"))
    plt.close(fig)
    return issues

def probe_fig10():
    fig, ax = plt.subplots(figsize=(11, 8.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 8.0); ax.axis("off")
    fig.canvas.draw()
    issues = []
    cards = ["方法论", "叙事", "访谈", "散文", "论文", "教程", "编年", "auto(入口)"]
    cw = 2.40; ch = _box_height(1); xs = [0.35 + i*(cw+0.14) for i in range(4)]
    row1_y = 6.95; row2_y = row1_y - ch - GAP_V
    row_boxes = []
    for i, name in enumerate(cards[:4]):
        r = draw_box(ax, xs[i], row1_y, cw, ch, name, ["素材卡 · 文体块"], fc="#eef3ee")
        issues.extend(check_width(r, "#10R1"+name)); row_boxes.append((xs[i], row1_y, cw, ch))
    for i, name in enumerate(cards[4:]):
        r = draw_box(ax, xs[i], row2_y, cw, ch, name, ["素材卡 · 文体块"], fc="#eef3ee")
        issues.extend(check_width(r, "#10R2"+name)); row_boxes.append((xs[i], row2_y, cw, ch))

    mh = _box_height(2); mw = 7.2
    merge_y = row2_y - mh - GAP_V
    r = draw_box(ax, 5.5-mw/2, merge_y, mw, mh, "voice_of：卡.voice 逐键合并 DEFAULT_VOICE",
                 ["缺键落默认；读卡不改卡", "duty / cover / mapping / vocab 各自不同"], fc="#fdf6e3")
    issues.extend(check_width(r, "#10voice_of"))

    ph = _box_height(2); pw = 8.0
    prompt_y = merge_y - ph - GAP_V
    r = draw_box(ax, 5.5-pw/2, prompt_y, pw, ph, "script_engine 提示词：每卡文体四件套不同",
                 ["讲解体卡 = 原讲解文案（逐字一致）", "小说卡 = 评书块；demo/demo_bad 各归各卡"], fc="#f4f6f8")
    issues.extend(check_width(r, "#10prompt"))

    rw = 2.8; rh = _box_height(2); rxs = [0.35, 4.1, 7.85]
    labels = ["① 人选项目", "② 卡默认 form", "③ DEFAULT_FORM"]
    sub = [["script.dialogue_form", "非空且认得"], ["card['form']", "认得才用"], ["qa（兜底）", "不让没选落空值"]]
    resolve_y = prompt_y - rh - GAP_V
    resolve_boxes = []
    for x, title, body in zip(rxs, labels, sub):
        r = draw_box(ax, x, resolve_y, rw, rh, title, body, fc="#eef3ee")
        issues.extend(check_width(r, "#10"+title))
        resolve_boxes.append((x, resolve_y, rw, rh))
    issues.extend(check_overlap(resolve_boxes, "#10resolve"))

    # 关键：检查所有竖向相邻元素净距（gap = 上元素底 - 下元素顶）
    def gap_check(upper_bottom, lower_top, label):
        g = upper_bottom - lower_top
        if g < 0.05:
            issues.append(f"{label} 净距 {g:.2f}<0.05 叠压")

    for (x,y,w,h) in row_boxes[:4]:  # 第一排卡底 vs 第二排卡顶
        gap_check(y, row2_y + ch, f"#10 第一排卡{name}与第二排卡")
    for (x,y,w,h) in row_boxes[4:]:  # 第二排卡底 vs voice_of 顶
        gap_check(y, merge_y + mh, f"#10 第二排卡与voice_of框")
    gap_check(merge_y, prompt_y + ph, "#10 voice_of框与提示词框")
    gap_check(prompt_y, resolve_y + rh, "#10 提示词框与resolve_form框")
    plt.close(fig)
    return issues

if __name__ == "__main__":
    i9 = probe_fig9(); i10 = probe_fig10()
    print("=== #9 fig 探针结果 ===")
    print("PASS" if not i9 else f"FAIL ({len(i9)} 项)")
    for x in i9: print("  ", x)
    print("=== #10 fig 探针结果 ===")
    print("PASS" if not i10 else f"FAIL ({len(i10)} 项)")
    for x in i10: print("  ", x)
