#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 图生成脚本：为《我写故我播》#38 与 #12 两篇生成配图（PNG + SVG，simhei 防方框）。
# 真实数据取自 podcast-maker 项目：web_ui.py 网格断点、probe.py 容量口径、calibration.json 配比实测。
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = FontProperties(fname=r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = FONT.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11

# ----------------------------------------------------------------- #38 配置页网格重排
def fig38():
    widths = [
        (">=1420px", 4, "4 列"),
        ("1060-1420px", 3, "3 列"),
        ("720-1060px", 2, "2 列"),
        ("<720px", 1, "1 列"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.4))
    axes = axes.ravel()
    for ax, (lbl, ncol, tag) in zip(axes, widths):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.set_aspect("equal")
        ax.set_title("%s  →  %s" % (lbl, tag), fontproperties=FONT)
        # 画若干张卡，按 ncol 分行
        cards = [("时长", "档位"), ("BGM", "字幕"), ("音色", "环境"),
                 ("产能", "期数"), ("AIGC", "回调"), ("探针", "缓存")]
        x0, y0, w, h, gx, gy = 0.4, 4.6, 2.0, 1.0, 0.3, 0.4
        shown = cards[: max(6, ncol * 2)]
        idx = 0
        rows = (len(shown) + ncol - 1) // ncol
        y_bottom = y0 - (rows - 1) * (h + gy)   # 画布随行数自适应：框永远完整入画
        ax.set_ylim(min(0, y_bottom - 0.3), 6)
        for r in range(rows):
            for c in range(ncol):
                if idx >= len(shown):
                    break
                rx = x0 + c * (w + gx)
                ry = y0 - r * (h + gy)
                ax.add_patch(Rectangle((rx, ry), w, h, facecolor="#dce6f2",
                                       edgecolor="#5a7aa8", lw=1.1))
                ax.text(rx + w / 2, ry + h / 2, shown[idx][0],
                        fontproperties=FONT, ha="center", va="center", fontsize=9)
                idx += 1
        ax.axis("off")
    fig.suptitle("配置页 .grid.g4 四列响应式网格：一处定义、渲染只读取（不新增任何配置项）",
                 fontproperties=FONT, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p = os.path.join(HERE, "38_配置页网格_fig1")
    fig.savefig(p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(p + ".svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


# ----------------------------------------------------------------- #12 排图与压比
def fig12():
    # 真实口径（25 分钟一期，STANDARD_K=4.39 有效字/秒）
    target = round(1500 * 4.39)          # 成稿目标 1 = 6585
    floor = round(target * 1.25 * 1.2)   # 下限 = 9877
    ratio = 5                            # 1:5 档
    xmax = round(target * 1.25 * ratio)  # 输入max（素材容量上限）= 41156
    nominal = round(target * ratio)       # 名义容量 = 32925

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.6))

    # Panel A：字数三口径
    labels = ["成稿目标\n(1, 不含偏移)", "下限\n(1×1.25×1.2)", "1:5档名义容量\n(1×档位)"]
    vals = [target, floor, nominal]
    bars = ax1.bar(labels, vals, color=["#7ea6c4", "#9ab87a", "#c49a5a"])
    ax1.set_ylabel("字数（25 分钟一期）", fontproperties=FONT)
    ax1.set_title("排图的三把尺：由配置实时推导，一处定义三处同变", fontproperties=FONT, fontsize=11)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v, "%d" % v,
                 ha="center", va="bottom", fontproperties=FONT, fontsize=10)
    ax1.tick_params(axis="x", labelsize=9)

    # Panel B：压比体检红线（分母=成稿目标）
    ax2.set_xlim(0, 7.8)   # 宽度预算：右侧注释「上限 6.25…」起 x=6.6，画布随之放宽不裁边
    ax2.set_ylim(0, 1)
    ax2.add_patch(Rectangle((1.5, 0), 6.25 - 1.5, 1, facecolor="#9ab87a", alpha=0.35))
    ax2.add_patch(Rectangle((0, 0), 1.5, 1, facecolor="#d98b8b", alpha=0.25))
    ax2.plot([6.25, 6.25], [0, 1], color="#c0392b", lw=2)
    ax2.plot([1.5, 1.5], [0, 1], color="#c0392b", lw=2)
    ax2.text(0.75, 0.55, "低于下限\n(1.5) 偏松", fontproperties=FONT, ha="center", fontsize=9)
    ax2.text(3.9, 0.55, "达标区 [1.5, 6.25]", fontproperties=FONT, ha="center", fontsize=9)
    ax2.text(6.6, 0.5, "上限\n6.25\n(1:5档\n达线)", fontproperties=FONT, ha="left", fontsize=9, color="#c0392b")
    ax2.set_yticks([])
    ax2.set_xlabel("压比 = 原文 ÷ 脚本（分母=成稿目标）", fontproperties=FONT)
    ax2.set_title("压比体检两条红线：上限 6.25 / 下限 1.5", fontproperties=FONT, fontsize=11)

    fig.tight_layout()
    p = os.path.join(HERE, "12_排图压比_fig1")
    fig.savefig(p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(p + ".svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)

    # fig2: calibration.json 配比实测 k 分布（同音色异速比例，与 STANDARD_K=4.39 对照）
    cands = [
        os.environ.get("PODCAST_MAKER_HOME", ""),          # 运行时注入，不落本机路径
        os.path.join(HERE, "..", "..", "..", "..", "podcast-maker", "calibration.json"),
        os.path.join(os.path.dirname(HERE), "..", "..", "podcast-maker", "calibration.json"),
    ]
    ck = next((c for c in cands if c and os.path.exists(c)), None)
    if ck is None:
        print("skip fig2: calibration.json 未找到（可设 PODCAST_MAKER_HOME 注入；留档脱敏不写死本机路径）")
        return
    d = json.load(open(ck))
    g = d.get("groups", {})
    ks = [v["k"] for v in g.values() if "k" in v]
    fig2, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.bar(range(len(ks)), ks, color="#7ea6c4")
    ax.axhline(4.39, color="#c0392b", lw=1.6, ls="--")
    ax.text(0, 5.55, "STANDARD_K=4.39（脚本估时基准）", fontproperties=FONT,
            color="#c0392b", fontsize=9, va="top")   # 独立通道：贴顶放置，不蹭柱顶与基准线
    ax.set_ylabel("k（有效字/秒）", fontproperties=FONT)
    ax.set_xlabel("已校准音色组（按引擎·音色·语速分组）", fontproperties=FONT)
    ax.set_title("配比实测：时长校准系数 k 围绕基准波动、不同音色互不污染", fontproperties=FONT, fontsize=11)
    ax.set_ylim(4.0, 5.6)
    fig2.tight_layout()
    p2 = os.path.join(HERE, "12_排图压比_fig2")
    fig2.savefig(p2 + ".png", dpi=150, bbox_inches="tight")
    fig2.savefig(p2 + ".svg", bbox_inches="tight")
    plt.close(fig2)
    print("wrote", p2)


if __name__ == "__main__":
    fig38()
    fig12()
