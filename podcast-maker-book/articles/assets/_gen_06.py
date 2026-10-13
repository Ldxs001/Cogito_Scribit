# -*- coding: utf-8 -*-
"""《我写故我播》#06 配图生成脚本（与成稿同源，留档复核）。
fig1：PATCH_SCHEMA 空补丁三层加固防护（结构锁 -> 系统终审 -> 解析兜底）
数据来自 podcast-maker · CHANGELOG.md（v1.7.0 · 检查段修补空补丁三层加固）
与 podcast_maker/script_engine.py:PATCH_SCHEMA L2004 / patch_system / parse_patch；
突变实验见 articles/6_检查段修补空补丁.md 验证段。
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


def _box(ax, x, y, w, h, title, body, fc, ec="#333", fs=9.5):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.04",
                         fc=fc, ec=ec, lw=1.2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.42, title, ha="center", va="center",
             fontsize=10.5, weight="bold", color="#1a1a1a")
    ax.text(x + w / 2, y + h / 2 - 0.15, body, ha="center", va="center",
            fontsize=fs, color="#222")


def fig1():
    fig, ax = plt.subplots(figsize=(8.6, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    ax.text(1.6, 11.3, "模型交回：{edits:[], inserts:[]}", ha="center", va="center",
            fontsize=9.5, color="#a05050", weight="bold",
            bbox=dict(boxstyle="round", fc="#f7e7e7", ec="#c08080"))
    ax.add_patch(FancyArrowPatch((1.6, 10.8), (5.0, 10.0),
                 arrowstyle="-|>", mutation_scale=14, color="#a05050", lw=1.6))

    _box(ax, 2.2, 8.4, 5.6, 1.5,
         "层① 结构层（schema 锁）",
         "PATCH_SCHEMA.anyOf：\nedits / inserts 至少一个非空数组\n白卷在结构里写不出来",
         fc="#dbe4f0")
    _box(ax, 2.2, 5.6, 5.6, 1.5,
         "层② 提示词层（system 终审）",
         "patch_system 增加终审条款：\n结论已定，仅保留执行权\n不许返回空补丁",
         fc="#e7f0e7")
    _box(ax, 2.2, 2.8, 5.6, 1.5,
         "层③ 解析层（parse 兜底）",
         "parse_patch 空补丁拦截保留：\n格式合法也拦，给出原因递回下一轮\n解析层最后一道防线",
         fc="#f0e7e7")

    ax.add_patch(FancyArrowPatch((5.0, 8.4), (5.0, 7.1),
                 arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4))
    ax.add_patch(FancyArrowPatch((5.0, 5.6), (5.0, 4.3),
                 arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4))

    ax.text(8.6, 9.1, "拒绝", ha="center", va="center", fontsize=12,
            color="#a05050", weight="bold")
    ax.text(8.6, 6.3, "拒绝", ha="center", va="center", fontsize=12,
            color="#a05050", weight="bold")
    ax.text(8.6, 3.5, "拦截", ha="center", va="center", fontsize=12,
            color="#a05050", weight="bold")

    ax.text(5.0, 1.3,
            "三层互为独立防线：删任一层（如删 anyOf）其余两层仍拦，但结构层是白卷写不出的根本锁\n"
            "突变实验：临时副本删 anyOf，test_an_empty_patch_is_structurally_illegal 当场 KeyError 失败",
            ha="center", va="center", fontsize=8.4, color="#444")

    ax.set_title("PATCH_SCHEMA 空补丁三层加固防护（v1.7.0）",
                 fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "6_检查段修补空补丁_fig1.png"), dpi=150)
    fig.savefig(os.path.join(OUT, "6_检查段修补空补丁_fig1.svg"))
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    print("OK: 6 fig1 generated")
