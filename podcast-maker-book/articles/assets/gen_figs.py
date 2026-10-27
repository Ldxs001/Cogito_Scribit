# -*- coding: utf-8 -*-
# 真实数据图生成（podcast-maker 真仓取材，临时副本实验与 CHANGELOG v2.0.0 实测）
# 注册黑体防方框；同时输出 PNG 与 SVG。
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

FONT = "C:/Windows/Fonts/simhei.ttf"
fm.fontManager.addfont(FONT)
plt.rcParams["font.family"] = fm.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False
BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- 图1：#22 从搭建到出曲（两阶段真实数据） ----------
fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.2))
fig.suptitle("本地 BGM 生成：一次性搭建 vs 每次出曲（v2.0.0 真机实测）", fontsize=13)

# 左：镜像优选实测下载速度（CHANGELOG v2.0.0 / v2.1.0）
ax[0].bar(["上交大镜像", "pytorch 官方"], [6.3, 0.65], color=["#2E8B57", "#B22222"])
ax[0].set_ylabel("下载速度 (MB/s)")
ax[0].set_title("搭建脚本镜像优选（实测）", fontsize=11)
for i, v in enumerate([6.3, 0.65]):
    ax[0].text(i, v + 0.12, "%.2f" % v, ha="center", fontsize=10)
ax[0].set_ylim(0, 7.2)

# 右：真机一次完整生成产物规格（CHANGELOG v2.0.0 真机跑通）
ax[1].bar(["峰值 0.8913", "RMS 0.0700"], [0.8913, 0.0700], color=["#4169E1", "#FF8C00"])
ax[1].set_ylabel("幅度 (0–1)")
ax[1].set_title("一次生成产物规格（48 kHz / 10.00 s / rc=0）", fontsize=11)
for i, v in enumerate([0.8913, 0.0700]):
    ax[1].text(i, v + 0.02, "%.4f" % v, ha="center", fontsize=10)
ax[1].set_ylim(0, 1.0)
fig.text(0.5, 0.02, "数据源：podcast-maker · CHANGELOG.md · v2.0.0（真机跑通 10 秒曲目 rc=0，stdout 恰好一行 JSON）",
         ha="center", fontsize=8, color="#555555")

fig.tight_layout(rect=[0, 0.05, 1, 0.95])
fig.savefig(BASE + "/22_local_bgm_gen_fig1.png", dpi=150)
fig.savefig(BASE + "/22_local_bgm_gen_fig1.svg")
plt.close(fig)

# ---------- 图1：#23 收尾顺序（事故 vs 修复） ----------
fig2, ax2 = plt.subplots(figsize=(11.2, 4.0))
ax2.axis("off")
ax2.set_xlim(0, 12)
ax2.set_ylim(0, 4)

def stage(ax, x, y, w, h, text, fc, tc="white"):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="#333333", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9.5, color=tc)

# 事故行（红）
ax2.text(0.1, 3.55, "事故（v2.0.0 修复前）：搬运在 finally 之后 → 成品被连目录一起清掉", fontsize=10.5, color="#B22222")
stage(ax2, 0.3, 3.0, 2.4, 0.55, "① 生成\n(模型加载+推理+VAE解码)", "#888888")
stage(ax2, 3.1, 3.0, 2.4, 0.55, "② finally 清场\n(删 .generating)", "#B22222")
stage(ax2, 5.9, 3.0, 3.0, 0.55, "③ 搬运出临时目录\n(在 finally 之后，文件已不存在)", "#B22222")
ax2.annotate("", xy=(3.1, 3.27), xytext=(2.7, 3.27), arrowprops=dict(arrowstyle="->"))
ax2.annotate("", xy=(5.9, 3.27), xytext=(5.5, 3.27), arrowprops=dict(arrowstyle="->"))
ax2.text(0.3, 2.45, "结果：isfile(src) 必为假，报「音频产物没落盘」，整趟生成白做", fontsize=9, color="#B22222")

# 修复行（绿）
ax2.text(0.1, 1.85, "修复（v2.0.0）：shutil.move 挪到 finally 之前 —— 先搬后清，顺序不能反", fontsize=10.5, color="#2E8B57")
stage(ax2, 0.3, 1.3, 2.4, 0.55, "① 生成\n(模型加载+推理+VAE解码)", "#888888")
stage(ax2, 3.1, 1.3, 3.0, 0.55, "② 搬运出临时目录\n(shutil.move 到草稿位)", "#2E8B57")
stage(ax2, 6.4, 1.3, 2.3, 0.55, "③ finally 清场\n(此时成品已安全)", "#2E8B57")
ax2.annotate("", xy=(3.1, 1.57), xytext=(2.7, 1.57), arrowprops=dict(arrowstyle="->"))
ax2.annotate("", xy=(6.4, 1.57), xytext=(6.1, 1.57), arrowprops=dict(arrowstyle="->"))
ax2.text(0.3, 0.75, "结果：rc=0，草稿落位、账本齐、临时目录已清；清场失败只 [WARN] 不误杀", fontsize=9, color="#2E8B57")

fig2.suptitle("成品被自己的清场删掉：收尾顺序的一次误杀与修复", fontsize=13)
fig2.text(0.5, 0.02, "数据源：podcast-maker · CHANGELOG.md · v2.0.0（music_gen.py:451 先搬后清 / :513 finally 清场）",
          ha="center", fontsize=8, color="#555555")
fig2.tight_layout(rect=[0, 0.05, 1, 0.93])
fig2.savefig(BASE + "/23_cleanup_kills_product_fig1.png", dpi=150)
fig2.savefig(BASE + "/23_cleanup_kills_product_fig1.svg")
plt.close(fig2)
print("figures written")
