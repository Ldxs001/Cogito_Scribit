# -*- coding: utf-8 -*-
"""§十二 综合验证器：实测文本/箭头包围盒，查 文本-文本 / 文本-箭头 / 文本-盒 / 箭头穿透 / 箭头头占宽 vs 缝宽。
导入 gen_figures_0910 的 build_* 复用同一几何，杜绝漂移。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import gen_figures_0910 as G

fm.fontManager.addfont(r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False
ROW = G.ROW
NET = 0.6 * ROW  # §3 净距 ≥ 0.6 行高 = 0.18 数据单位


def _to_data(ax, ext):
    inv = ax.transData.inverted()
    x0, y0 = inv.transform((ext.x0, ext.y0))
    x1, y1 = inv.transform((ext.x1, ext.y1))
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _intersect(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _arrows_bbox(ax, a):
    patch = FancyArrowPatch((a["x1"], a["y1"]), (a["x2"], a["y2"]),
                            arrowstyle="-|>", mutation_scale=G.MUT, linewidth=1.5,
                            edgecolor=a["color"], facecolor=a["color"], zorder=4,
                            connectionstyle="arc3,rad=%s" % a["rad"])
    ax.add_patch(patch)
    ext = patch.get_window_extent(ax.figure.canvas.get_renderer())
    return _to_data(ax, ext)


def build_and_measure(elements, fs):
    fig, ax = plt.subplots(figsize=fs)
    ax.set_xlim(0, 11); ax.set_ylim(0, fs[1]); ax.axis("off")
    fig.canvas.draw()
    texts, arrows, boxes = [], [], []
    issues = []
    for b in elements["boxes"]:
        boxes.append((b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]))
        t = ax.text(b["x"] + b["w"] / 2, b["y"] + b["h"] - 0.18 - ROW / 2, b["title"],
                    ha="center", va="center", fontsize=11, fontweight="bold", color=G.INK, zorder=3)
        tb = _to_data(ax, t.get_window_extent(fig.canvas.get_renderer()))
        texts.append((tb, b["title"], "title"))
        # §2 宽度预算：标题宽 ≤ 盒宽 − 2×内边距
        if tb[2] - tb[0] > b["w"] - 2 * 0.18 + 0.02:
            issues.append("盒内标题溢出: [%s] 宽 %.2f > 盒宽-0.36=%.2f" % (b["title"][:10], tb[2] - tb[0], b["w"] - 0.36))
        for i, line in enumerate(b["body"]):
            ay = b["y"] + b["h"] - 0.18 - ROW * (1.5 + i)
            tt = ax.text(b["x"] + b["w"] / 2, ay, line, ha="center", va="center", fontsize=10, color=G.SUB, zorder=3)
            bb = _to_data(ax, tt.get_window_extent(fig.canvas.get_renderer()))
            texts.append((bb, line, "body"))
            if bb[2] - bb[0] > b["w"] - 2 * 0.18 + 0.02:
                issues.append("盒内body溢出: [%s] 宽 %.2f" % (line[:10], bb[2] - bb[0]))
    for a in elements["arrows"]:
        arrows.append(_arrows_bbox(ax, a))
    for t in elements["texts"]:
        tt = ax.text(t["x"], t["y"], t["s"], ha="center", va="center", fontsize=t["size"],
                     color=t["color"], fontweight=t.get("weight", "normal"), zorder=5)
        tb = _to_data(ax, tt.get_window_extent(fig.canvas.get_renderer()))
        texts.append((tb, t["s"], "note"))
        # §2 注释距画布边 ≥ 一个字宽
        if tb[0] < 0.12 or tb[2] > 11 - 0.12 or tb[1] < 0.12 or tb[3] > fs[1] - 0.12:
            issues.append("注释贴画布边: [%s] bbox=(%.2f,%.2f,%.2f,%.2f)" % (t["s"][:10], tb[0], tb[1], tb[2], tb[3]))
    plt.close(fig)
    return texts, arrows, boxes, issues


def verify_fig9():
    e, fs = G.build_fig9()
    texts, arrows, boxes, issues = build_and_measure(e, fs)
    # 1. 文本-文本 重叠（同一盒内 title/body 不查）
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if texts[i][2] == "title" and texts[j][2] == "body" and texts[i][1] == texts[j][1][:len(texts[i][1])]:
                continue
            if _intersect(texts[i][0], texts[j][0]):
                issues.append("文本重叠: [%s] × [%s]" % (texts[i][1][:10], texts[j][1][:10]))
    # 2. 文本-箭头
    for (tb, s, k) in texts:
        for ab in arrows:
            if _intersect(tb, ab):
                issues.append("文本压箭头: [%s] 压在箭头上" % s[:12])
    return issues


def verify_fig10():
    e, fs = G.build_fig10()
    texts, arrows, boxes, issues = build_and_measure(e, fs)
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if _intersect(texts[i][0], texts[j][0]):
                issues.append("文本重叠: [%s] × [%s]" % (texts[i][1][:10], texts[j][1][:10]))
    for (tb, s, k) in texts:
        for ab in arrows:
            if _intersect(tb, ab):
                issues.append("文本压箭头: [%s] 压在箭头上" % s[:12])
    return issues


def arrow_head_size():
    """画一段极短（0.08）的箭头，其 extent 即箭头头本身的尺寸。"""
    fig, ax = plt.subplots(figsize=(11, 9.0)); ax.set_xlim(0, 11); ax.set_ylim(0, 9.0); ax.axis("off")
    fig.canvas.draw()
    a = FancyArrowPatch((5, 4.92), (5, 5.0), arrowstyle="-|>", mutation_scale=G.MUT, linewidth=1.5, edgecolor="k", facecolor="k")
    ax.add_patch(a)
    fig.canvas.draw()
    ext = _to_data(ax, a.get_window_extent(fig.canvas.get_renderer()))
    plt.close(fig)
    return (ext[2] - ext[0], ext[3] - ext[1])  # 宽, 高（纯箭头头）


def _seg_in_box(x1, y1, x2, y2, box, tol=0.05):
    """箭头线段（去掉两端 tol）是否穿入 box 内部（§2 箭头不得穿透盒）。"""
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    if L < 1e-9:
        return False
    # 去掉两端 tol 后的参数区间
    t0, t1 = tol / L, 1 - tol / L
    if t0 > t1:
        return False
    bx0, by0, bx1, by1 = box
    import math
    steps = 24
    for k in range(steps + 1):
        t = t0 + (t1 - t0) * k / steps
        px, py = x1 + dx * t, y1 + dy * t
        if bx0 - 1e-6 < px < bx1 + 1e-6 and by0 - 1e-6 < py < by1 + 1e-6:
            return True
    return False


def verify_arrows(elements):
    issues = []
    for a in elements["arrows"]:
        for b in elements["boxes"]:
            box = (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])
            if _seg_in_box(a["x1"], a["y1"], a["x2"], a["y2"], box):
                issues.append("箭头穿透盒: %s→%s 穿入 [%s]" % (a.get("color"), b["title"][:8], b["title"][:8]))
    return issues


if __name__ == "__main__":
    hw = arrow_head_size()
    print("箭头头占宽=%.3f 占高=%.3f（MUT=%d）；竖向缝宽 GAP_V=%.2f" % (hw[0], hw[1], G.MUT, G.GAP_V))
    print("  缝宽 - 箭头头占高 = %.3f （需 >0 保证带杆可见）" % (G.GAP_V - hw[1]))
    e9, _ = G.build_fig9(); e10, _ = G.build_fig10()
    p9 = verify_arrows(e9); p10 = verify_arrows(e10)
    i9 = verify_fig9(); i10 = verify_fig10()
    print("=== #9 综合验证 ===")
    print("PASS" if not (i9 or p9) else "FAIL")
    for x in (i9 + p9): print("  ", x)
    print("=== #10 综合验证 ===")
    print("PASS" if not (i10 or p10) else "FAIL")
    for x in (i10 + p10): print("  ", x)
