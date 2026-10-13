#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 图生成脚本：为《我写故我播》#43 与 #44 两篇生成配图（PNG + SVG，simhei 防方框）。
# 真实数据取自 podcast-maker 项目：CHANGELOG 体例段 / test_changelog_tone.py（#43）、
# test_config_keys.py / test_banner.py / test_batch.py / test_timbre_guard.py（#44）。
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, FancyBboxPatch
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = FontProperties(fname=r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = FONT.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11


def _box(ax, x, y, w, h, text, fc, ec, fs=10, wrap=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                facecolor=fc, edgecolor=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, fontproperties=FONT, ha="center",
            va="center", fontsize=fs, wrap=wrap)


def _arrow(ax, x1, y1, x2, y2, color="#444"):
    ax.add_patch(FancyArrow(x1, y1, x2 - x1, y2 - y1, width=0.012,
                            length_includes_head=True, head_width=0.06,
                            head_length=0.09, edgecolor=color, facecolor=color))


# ----------------------------------------------------------------- #43 词表守门结构图
def fig43():
    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # 起点
    _box(ax, 3.6, 8.7, 2.8, 0.9, "CHANGELOG.md\n（版本记录）", "#e8eef5", "#5a7aa8", fs=10)
    _arrow(ax, 5.0, 8.7, 5.0, 7.9)
    _box(ax, 3.4, 7.0, 3.2, 0.9, "按行首「## v」切开\n（只认行首，避免体例区自切）", "#e8eef5", "#5a7aa8", fs=9.5)

    # 两路分支
    _arrow(ax, 4.2, 7.0, 2.0, 6.2)
    _arrow(ax, 5.8, 7.0, 8.0, 6.2)
    _box(ax, 0.3, 5.4, 3.4, 1.4, "体例区（head）\n正向判据", "#f3e7d0", "#c79a3a", fs=10)
    _box(ax, 6.3, 5.4, 3.4, 1.4, "正文（body）\n三类词表逐行扫描", "#dcefdc", "#5a9a5a", fs=10)

    # 体例区判据
    _arrow(ax, 2.0, 5.4, 2.0, 4.5)
    _box(ax, 0.2, 3.4, 3.6, 1.1,
         "判据①：必须含「文风：」条款\n判据②：必须写明 test_changelog_tone\n（规则删了，词表就没人知道）",
         "#fbf3e0", "#c79a3a", fs=8.5)
    # 正文扫描
    _arrow(ax, 8.0, 5.4, 8.0, 4.5)
    _box(ax, 6.2, 3.4, 3.6, 1.6,
         "人称叙事 / 产品定位论证 / 口语化措辞\n三类禁用串逐行比对\n命中即报 (行号, 词)",
         "#e6f5e6", "#5a9a5a", fs=8.8)

    # 注：跳过体例区避免自证
    _arrow(ax, 2.0, 3.4, 8.0, 3.4, color="#c0392b")
    ax.text(5.0, 3.62, "跳过体例区：那里写着词表本身，扫进去即自证",
            fontproperties=FONT, ha="center", va="bottom", fontsize=8.5,
            color="#c0392b")

    # 结果
    _box(ax, 0.2, 1.7, 3.6, 1.2, "体例区少一条 → 红\n（规则丢失即报警）", "#f6dada", "#c0392b", fs=9)
    _box(ax, 6.2, 1.7, 3.6, 1.2, "正文命中禁用串 → 红\n（命中即报行号与词）", "#f6dada", "#c0392b", fs=9)
    _arrow(ax, 2.0, 3.4, 2.0, 2.9)
    _arrow(ax, 8.0, 3.4, 8.0, 2.9)

    ax.set_title("更新日志词表守门：纪律从「记得住」变成「绕不过」",
                 fontproperties=FONT, fontsize=12, pad=10)
    fig.tight_layout()
    p = os.path.join(HERE, "43_更新日志写成技术文_fig1")
    fig.savefig(p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(p + ".svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


# ----------------------------------------------------------------- #44 回归循环图 + 钉子实例
def fig44():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.2, 5.6))
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 10)
    axL.axis("off")
    axR.set_xlim(0, 10)
    axR.set_ylim(0, 10)
    axR.axis("off")

    # 循环四节点（菱形布局）
    nodes = [
        (5.0, 8.4, "修复 bug\n（行为正确）"),
        (8.0, 5.0, "加钉子\n（必红断言）"),
        (5.0, 1.6, "CI 跑测试\n（提交时）"),
        (2.0, 5.0, "回归即红\n（拦截，不进生产）"),
    ]
    for (x, y, t) in nodes:
        _box(axL, x - 1.4, y - 0.7, 2.8, 1.4, t, "#e8eef5", "#5a7aa8", fs=9.5)
    _arrow(axL, 6.4, 8.0, 7.6, 6.2)
    _arrow(axL, 8.0, 3.6, 6.4, 2.4)
    _arrow(axL, 3.6, 1.6, 2.8, 3.6)
    _arrow(axL, 2.0, 6.2, 3.6, 8.0)
    axL.text(5.0, 5.0, "纪律：\n人记 → 绕不过", fontproperties=FONT,
             ha="center", va="center", fontsize=10, color="#c0392b")

    # 右：钉子实例清单
    axR.text(0.2, 9.4, "钉子实例（改回去必红）", fontproperties=FONT,
             ha="left", va="center", fontsize=11, color="#333")
    items = [
        ("版本齐步钉", "v0.6.0 漏改过一次：日志头=VERSION、ARCHITECTURE 抬头同源", "#5a9a5a"),
        ("抬头钉", "v0.47.1：抬头打印次数全仓=1、必须用 VERSION、字面量只两处", "#5a9a5a"),
        ("进度钉", "v0.45.0：_BANDS 五段首尾相接、写稿段>0.5、只增不减", "#5a9a5a"),
        ("承诺链钉", "v0.41.1：缺 quote/problem 不被丢；check6_schema 键必留", "#5a9a5a"),
        ("反回潮钉", "已下线项（extra_requirement/风格维）按源码扫防加回", "#5a9a5a"),
        ("否决零误伤钉", "test_timbre_guard：第9维两道级联各自零误伤、缺维不否决", "#5a9a5a"),
    ]
    y = 8.6
    for name, desc, c in items:
        axR.add_patch(Rectangle((0.2, y - 0.62), 0.18, 0.18, facecolor=c, edgecolor=c))
        axR.text(0.5, y - 0.1, name, fontproperties=FONT, ha="left",
                 va="center", fontsize=9.5, color="#222")
        axR.text(0.5, y - 0.42, desc, fontproperties=FONT, ha="left",
                 va="center", fontsize=7.6, color="#555")
        y -= 1.15

    axR.text(0.2, y - 0.2,
             "缺陷分类框架（test_config_keys）：4/5/6/10/11/13 类\n"
             "——靠人看不出，只能扫代码对账",
             fontproperties=FONT, ha="left", va="center", fontsize=8.2, color="#c0392b")

    fig.suptitle("测试钉子：把修好的 bug 钉成 CI 里一个必红的断言",
                 fontproperties=FONT, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p = os.path.join(HERE, "44_测试钉子_fig1")
    fig.savefig(p + ".png", dpi=150, bbox_inches="tight")
    fig.savefig(p + ".svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


if __name__ == "__main__":
    fig43()
    fig44()
