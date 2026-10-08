# -*- coding: utf-8 -*-
# 图：进度条轨迹前后对比（数据源 podcast-maker · CHANGELOG.md · v0.45.0 实测轨迹段）
# 真实实测：假模型走真实任务通路 .02s 采样 80 次；改前仅见 0/50/95/100，改后 10/31/72/86/96/99/100，分段路 17 进 0 退
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 注册中文字体（SimHei），避免 CJK 字形缺失
fm.fontManager.addfont(r"C:/Windows/Fonts/simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

before = [0, 50, 95, 100]
after  = [10, 31, 72, 86, 96, 99, 100]

fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=150)
ax.step(range(len(before)), before, where="post", marker="o", color="#999999",
        linewidth=2, label="改前：仅见 0/50/95/100（跳变）")
ax.step(range(len(after)), after, where="post", marker="o", color="#1f6feb",
        linewidth=2, label="改后：10→31→72→86→96→99→100")
ax.set_ylim(0, 105)
ax.set_xticks(range(max(len(before), len(after))))
ax.set_xlabel("采样序号（.02s × 80 次）")
ax.set_ylabel("进度 %")
ax.set_title("进度条轨迹：改前跳变 vs 改后五段预算推进")
ax.grid(True, alpha=.3)
ax.legend(loc="lower right", fontsize=9)
fig.text(0.01, -0.02, "数据出处：podcast-maker · CHANGELOG.md · v0.45.0 · 实测轨迹段 [2]", fontsize=7, color="#666")
fig.tight_layout()
fig.savefig("articles/assets/28_进度条_fig1.png", bbox_inches="tight")
fig.savefig("articles/assets/28_进度条_fig1.svg", bbox_inches="tight")
print("OK 28_进度条_fig1 png+svg")
