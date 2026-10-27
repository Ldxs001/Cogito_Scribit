# podcast-maker-book/articles/assets/gen_figures_26.py
# 生成 #26《环境音执行层》两张配图（PNG + SVG），数据来自真实 ffmpeg 实验与 CHANGELOG 真机实测。
# 测量条件：仓的临时副本 / podcast-maker v2.7.0 源码 / ffmpeg 9.0.1 / 2026-10-22。

import os
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt

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


# ---------------------------------------------------------------- fig1
# 中间件对照：WAV（现行）vs mp3 直连（事故）。真实 ffmpeg 实验：
# 句子 3.0s + 停顿 0.18s + 事件音 2.23s = 期望 5.41s；mp3 直连 concat demuxer
# 只吐出 2.23s（下游 0.18s 停顿 + 3.0s 句子整段丢失）。
def fig1():
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    sfx, gap, sent = 2.23, 0.18, 3.0
    labels = ["WAV 中间件\n（现行）", "mp3 直连\n（事故路径）"]
    totals = [sfx + gap + sent, sfx]      # 事故路径只保留事件音自身长度
    colors = {"sfx": "#7e9e8a", "gap": "#a29674", "sent": "#7a94b2", "broken": "#b06a6a"}
    y = [1, 0]
    # WAV：三段堆叠
    ax.barh(y[0], sfx, color=colors["sfx"], edgecolor="#333", height=0.5)
    ax.barh(y[0], gap, left=sfx, color=colors["gap"], edgecolor="#333", height=0.5)
    ax.barh(y[0], sent, left=sfx + gap, color=colors["sent"],
            edgecolor="#333", height=0.5)
    # mp3 直连：仅事件音段（红，破损）
    ax.barh(y[1], sfx, color=colors["broken"], edgecolor="#333", height=0.5)
    ax.text(sfx / 2, y[0], "事件音 2.23s", va="center", ha="center",
            color="white", fontsize=11)
    ax.text(sfx + gap + sent / 2, y[0], "句前停顿 + 句子 3.0s", va="center",
            ha="center", color="white", fontsize=10)
    ax.text(sfx / 2, y[1], "事件音 2.23s\n(下游全部丢失)", va="center",
            ha="center", color="white", fontsize=10)
    ax.text(sfx + 0.1, y[1] - 0.62, "↓ 下游 0.18s 停顿 + 3.0s 句子整段丢失",
            fontsize=10, color="#7a3a3a")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("输出时长（秒）", fontsize=11)
    ax.set_xlim(0, 6.2)
    ax.set_title("环境音中间件：WAV（现行）vs mp3 直连（事故）· 输出时长对照",
                 fontsize=12.5)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=colors["sfx"]),
                       plt.Rectangle((0, 0), 1, 1, color=colors["gap"]),
                       plt.Rectangle((0, 0), 1, 1, color=colors["sent"]),
                       plt.Rectangle((0, 0), 1, 1, color=colors["broken"])],
              labels=["事件音 2.23s", "句前停顿 0.18s", "句子 3.0s",
                      "mp3 直连破损段"], fontsize=9, loc="lower right")
    save(fig, "26_sfx", 1)


# ---------------------------------------------------------------- fig2
# 执行层三路真机回填对照（CHANGELOG v2.7.0 端到端实测）：
# before 3.0→5.41s（+2.41s）/ after 累计 +9.674s / 垫底句长不变。
def fig2():
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    cats = ["句前 before\n(单句 +2.41s)", "句后 after\n(累计 +9.674s)",
            "垫底 bed\n(句长不变)"]
    vals = [5.41 - 3.0, 9.674, 0.0]      # 增量秒数
    bars = ax.bar(cats, vals, color=["#7a94b2", "#7e9e8a", "#a29674"],
                  edgecolor="#333", width=0.58)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, "%.3f s" % v,
                ha="center", fontsize=10)
    ax.set_ylabel("新增时长（秒）", fontsize=11)
    ax.set_title("环境音执行层三路真机回填（v2.7.0 端到端实测）", fontsize=12.5)
    ax.set_ylim(0, 11)
    ax.text(0, 5.41 - 3.0 + 0.6,
            "句前：3.0s 句体 → 5.41s\n(事件音 2.23s + 停顿 0.18s 实测回填)",
            fontsize=8.5, color="#333")
    save(fig, "26_sfx", 2)


if __name__ == "__main__":
    fig1()
    fig2()
    print("OK 26 figures")
