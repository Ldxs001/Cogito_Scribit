# -*- coding: utf-8 -*-
"""《我写故我播》#14 配图生成脚本（与成稿同源，留档复核）。
生成两图：
  fig1 测量维度数演进（v1.1.0 三维 → v1.2.0 四维 → v1.3.0 六维测量）
  fig2 第9维（源-滤波）三量分离度 AUC
数据全部来自 podcast-maker · CHANGELOG.md（v1.1.0 / v1.2.0 / v1.3.0 / v2.3.0）；
详见 articles/14_音色漂移检测.md 引用表。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT = r"C:/Windows/Fonts/simhei.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:/Users/sm001/WorkBuddy/Cogito_Scribit/podcast-maker-book/articles/assets"


def fig1():
    # 测量维度数演进：v1.1.0=3 → v1.2.0=4 → v1.3.0=6
    vers = ["v1.1.0\n三维", "v1.2.0\n四维", "v1.3.0\n六维测量"]
    dims = [3, 4, 6]
    notes = ["谱心×1.0\n基频×0.8\n响度×0.4", "＋存在感频带\n2.4-4.8kHz", "＋<300Hz能量\n＋基音抖动"]
    colors = ["#7a94b2", "#7e9e8a", "#9e8a74"]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    bars = ax.bar(vers, dims, color=colors, edgecolor="#333", width=0.55)
    for b, d, n in zip(bars, dims, notes):
        ax.text(b.get_x() + b.get_width() / 2, d + 0.12, str(d),
                ha="center", va="bottom", fontsize=14, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, 0.35, n,
                ha="center", va="bottom", fontsize=9, color="#444")
    # 标注两处“放行了人耳判坏”的事故
    ax.annotate("2da 0054：三维放行，频谱形状重分布漏检",
                xy=(0, 3), xytext=(0.05, 4.6),
                fontsize=8.5, color="#a05050",
                arrowprops=dict(arrowstyle="->", color="#a05050"))
    ax.annotate("0058_B：四维总分放行，基频塌 -2.75σ 漏检",
                xy=(2, 6), xytext=(1.45, 6.7),
                fontsize=8.5, color="#a05050",
                arrowprops=dict(arrowstyle="->", color="#a05050"))
    ax.set_ylabel("测量维度数量")
    ax.set_ylim(0, 8)
    ax.set_title("音色漂移检测：测量维度演进（v1.1.0 → v1.3.0）", fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT + "/14_音色漂移检测_fig1.png", dpi=150)
    fig.savefig(OUT + "/14_音色漂移检测_fig1.svg")
    plt.close(fig)


def fig2():
    # 第9维（源-滤波）三量分离度 AUC
    names = ["D_cep 倒谱谱包络", "D_rel 同句自比", "D_glot 声门三件套"]
    auc = [0.810, 0.857, 0.762]
    colors = ["#7a94b2", "#7e9e8a", "#9e8a74"]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    bars = ax.barh(names, auc, color=colors, edgecolor="#333", height=0.55)
    for b, v in zip(bars, auc):
        ax.text(v + 0.008, b.get_y() + b.get_height() / 2, "%.3f" % v,
                va="center", fontsize=12, fontweight="bold")
    # 抑制口径标注
    ax.text(0.02, 0.02,
            "抑制口径：D_cep<池80分位(1.47) 且 D_glot<池70分位(0.94)\n"
            "池内报警 42→18 句（-57%）",
            transform=ax.transAxes, fontsize=8.5, color="#444",
            bbox=dict(boxstyle="round", fc="#eee", ec="#aaa"))
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("分离度 AUC（越大越能区分真混入）")
    ax.set_title("第9维（源-滤波）三量分离度（v2.3.0）", fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT + "/14_音色漂移检测_fig2.png", dpi=150)
    fig.savefig(OUT + "/14_音色漂移检测_fig2.svg")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    print("OK: 14 fig1/fig2 generated")
