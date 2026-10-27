<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第四部 · 22｜本地 BGM 生成：把"搭环境"与"出曲"拆成两件事

> **结论先行**：本地 BGM 生成把"环境就位"和"每次出曲"拆成两件职责分明的活——前者是一次性的六步脚本搭建（独立 venv、镜像优选、权重自检），后者是被脚本包干的 10 秒级生成。核心命题是：把最重的活（装 torch、下权重）压进一次性搭建，让出曲侧只做"写临时目录 → 搬出 → 响度归一 → 记账"四步，并复用全局音乐库与同一条响度标尺。本文只谈 podcast-maker 这一个智能体的 `music_service` 模块；BGM 听不见（#21）、响度归一（#29）、转译层（#27）是相邻的独立篇目，不在此展开 [1][2]。
>
> 更新：2026-10-20（本篇属第四部「背景音乐」，承接 #21 BGM 听不见、为 #24 人声闪避与 #27～#29 的 BGM 三层结构 / 响度归一 / 转译层做模块铺垫；实证取自 podcast-maker 真仓 `CHANGELOG.md · v2.0.0` 与 `music_service` 模块源码及单测 [1][2][3][5]）

## 一、引子：真实起点

背景音乐卡上那一枚「生成」按钮，按下去要能在一台没有云依赖、没有预置素材的机器上，跑出一条 30 秒左右的真实器乐循环。这件事在早期不是这样解决的：仓库里一度用固定频率正弦波叠出来的 drone 垫去填 BGM，四档听着是同一个蜂鸣，判废；而一旦想离开"内置素材包"去真生成，挡在前面的不再是算法，而是环境——torch 去哪装、官方仓怎么下、权重落哪、和已经养着的 TTS 栈会不会互相搅动。把"出曲"和"搭环境"混在一起写，每一次生成都要重新面对这一长串前置，等于让最轻的动作背上最重的包袱。本文的起点就是把这个包袱从出曲侧剥离出去 [1]。

## 二、现象：它到底长什么样

v2.0.0 之后，`music_service` 模块的现状可以拆成两个互不打扰的半场。

**搭建半场（一次性）**：`setup_music_env.py` 由配置页「背景音乐」卡的搭建按钮触发，走六步——拿代码、找 Python、建独立 venv、装 `torch 2.7.1+cu128` 与官方仓依赖、下模型权重、自检。关键设计是这层栈和 TTS 栈（torch `2.9.1+cu126`）互不搅动：各自一套 venv，谁也不碰谁的依赖。下载环节做了镜像优选——torch 源上交大镜像优先、pytorch 官方兜底（官方源实测 `0.65 MB/s`，上交大 `6.3 MB/s`，差一个数量级）；PyPI 依赖显式走清华源；模型权重复用官方 `acestep.model_downloader`（ModelScope 自动兜底），不重写下载逻辑 [3]。

**出曲半场（每次）**：`music_gen.py` 暴露五个子命令 `--generate/--status/--save/--discard/--delete`，生成固定进全局音乐库的 `_draft.wav`（草稿）+ `_draft.json`（账本）；试听满意后 `--save --name X` 改名入库并改写账本 `role`，撞名拒绝、取消与删除幂等、静音拒收、时长 10~30 秒外拒收，全程 fail-closed；stdout 只输出一份 JSON（结果通道），进度走 stderr。真机跑通的一次完整生成：ACE-Step `2B turbo` 主干 + `0.6B` LM，10 秒曲目 `rc=0`，产物 `48 kHz` / `10.00` 秒 / 峰值 `0.8913` / RMS `0.0700`，stdout 恰好一行 JSON，验证后草稿已丢弃、音乐库无残留 [1][2]。

![图1：从搭建到出曲——一次性环境搭建 vs 每次出曲（v2.0.0 真机实测）](assets/22_local_bgm_gen_fig1.png)

图1 左为搭建脚本的镜像优选实测（上交大 `6.3 MB/s` 对 pytorch 官方 `0.65 MB/s`）；右为真机一次生成的产物规格（48 kHz / 10.00 s / 峰值 `0.8913` / RMS `0.0700`）。两半场共用一条纪律：**进度走 stderr、结果留 stdout**，父进程按 JSON 口径抠取 [1][2]。

## 三、错误尝试：我们怎么绕弯的

绕弯集中在两处，恰好对应"拆两件事"之前的两类想当然。

**第一类想当然：用内置固定素材包糊弄 BGM**。早期内置 BGM 是固定频率正弦波叠出来的 drone 垫，四档听着是同一个蜂鸣，判定废弃——但凡换一档，听感纹丝不动，混音侧怎么调默认值都救不了"有时好像有、有时完全没有"。这条路被废弃，不是因为生成技术难，而是因为它从根上没解决"真实器乐纹理"这件事 [1]。

**第二类想当然：搭建脚本把"装环境"当成一次性顺手活，却没给 Windows 留后路**。首跑即炸于 `os.rename`（`WinError 183`）：`shutil.rmtree(..., ignore_errors=True)` 把 Windows 只读文件（`.git` 对象全为只读）的删除失败静默吞掉，残骸使 git clone 失败、退到 tarball 后归位 rename 撞上残留目录；还有 `--save ""` 静默滑入 status 分支——空串经 argparse 归入默认空串，`if args.save:` 判假，误走 status 分支输出成功假象 [1]。

这两处弯的本质，是把"一次性重活"和"每次轻活"当成了同一种活来写：前者需要确定性（删不干净就停手），后者需要纪律（空输入就拒绝），混在一起必然有一头失守。

## 四、根因：为什么

把两件事拆开看，根因各自干净。

**固定 drone 垫的根因**是一条尺度判据：一段背景音乐的价值在于"它是真实器乐、有可被混音压住的能量分布"，而正弦波叠出来的垫在全频段是一个形状，换档不改形状，所以四档同蜂鸣。要让 BGM 真正可用，必须本地跑一个能生成真实器乐的模型，而不是继续往"假纹理"里打补丁 [1]。

**搭建脚本两坑的根因**都在"平台假设"上：其一，`shutil.rmtree` 的 `ignore_errors=True` 在 Windows 上对只读文件是"删失败也不说话"，于是 clone 前的清理成了走过场，残骸在几百秒后 rename 时炸出来；其二，argparse 的默认空串和用户输入的空串在分发时无法区分，`if args.save:` 把两者都判为假，空名悄悄溜进 status 分支。两个都是"平台/接口语义没对齐"的坑，不是算法坑 [1][3]。

**出曲侧真正的根因命题**（为本篇的相邻篇 #23 铺垫）：收尾动作之间是有先后契约的——搬运成品出临时目录，必须先于清场临时目录完成，否则清场会把还没搬走的成品连同目录一起带走。这条契约在 v2.0.0 的修法里被显式钉死 [2]。

## 五、正确修法：怎么做对的

拆两件事之后，每件事都有自己的标准答案。

**出曲侧走本地 ACE-Step 离线生成**：主干 `2B turbo` + `0.6B` LM，用官方仓自带的 Python API（`acestep.handler` / `acestep.inference`），不重写任何推理逻辑；生成固定进草稿位，试听满意再入库，和 VoiceDesign 造嗓同构 [1][2]。

**搭建脚本两坑的修法**是确定性优先：新增 `_rmtree()`——遍历解除只读后删除，删完断言目录不存在，删不干净当场报错，不让下一步在几百秒后炸；`fetch_repo()` 重写，tarball 半成品（`ACE-Step-1.5-main`）完整时直接捡用归位，不重下。空名修法更简单也更深：`--save` 默认值改 `None`，分发判 `is not None`，空名按非法输入拒绝，不再有"空串溜进 status"的缝隙。镜像优选与 flash-attn 默认跳过（v2.1.0 收口）让搭建在受限网络下也能跑通：flash-attn 仅为注意力加速，SDPA 自动回退下功能与音质零影响，缺席只慢不残，默认滤除并打 `[WARN]`，需要时以 `--with-flash-attn` 旗标走镜像链安装 [1][3]。

**出曲侧的四步骨架**——写临时目录、搬出、响度归一、记账——在源码里是一条确定路径。下面是 `cmd_generate` 的脱敏骨架，保留真实标识符与阈值 [2]：

```python
# music_service/music_gen.py —— cmd_generate：出曲侧四步（生成→先搬后清→归一→记账）
def cmd_generate(lib, prompt, seconds, …):
    tmp_dir = os.path.join(lib, ".generating")   # 官方把 wav 写进这个临时目录
    _clear_scratch(tmp_dir); os.makedirs(tmp_dir, exist_ok=True)
    wav, js = draft_paths(lib)
    try:
        with _stdout_to_stderr():                 # 模型加载/推理整段重定向，结果通道不被污染 [2]
            result = generate_music(dit, lm, params, config, save_dir=tmp_dir)
        if not result.success or not os.path.isfile(src := result.audios[0]["path"]):
            return _fail("音频产物没落盘")          # 失败即失败，不静默
        shutil.move(src, wav)                      # ① 先搬出临时目录，再让 finally 清场（顺序不能反）[2]:451
        _check_not_silence(wav); _mono_s16(wav, ff) # 规格统一：s16 单声道
        norm = _loudnorm_lib().normalize_file(wav, ffmpeg=ff, allow_limited=True)  # 共享 tools/bgm_loudness 标尺
        write_json_file(js, {"role": DRAFT_NAME, "seed": real_seed, "norm_limited": bool(norm["limited"]), …})  # 记账
        print(json.dumps({"ok": True, "draft": draft_state(lib)}), flush=True)     # 结果通道：恰好一行 JSON
        return 0
    except Exception as e:
        return _fail("生成失败：%s" % e)
    finally:
        _clear_scratch(tmp_dir)                    # ② 只负责清场，此时成品已安全 [2]:513
```

**响度归一复用唯一实现** `tools/bgm_loudness.py`：内置 15 档与生成侧共用一条标尺（`-23 LUFS` / 真峰值 `-1 dBTP`），ACE-Step 产物是 f32 立体声且响度自由发挥（实测 `-16.4 LUFS`，比内置档响 `6.5 dB`），不归一就会压场；归一只施加线性增益、不夹不削，峰值先撞线的稀疏瞬态类 BGM 按 `allow_limited=True` 显式放行落稿并记 `norm_limited`，不达标但受控可追溯，而不是删稿停产 [4]。

## 六、验证：数据说话

**六步搭建（一次性）与真机实测产物规格（每次出曲）对照** [1][2][3]：

| 半场 | 关键事实 | 真实数字 / 口径 |
|---|---|---|
| 搭建（一次性） | torch 源优选 | 上交大 `6.3 MB/s` vs 官方 `0.65 MB/s` |
| 搭建（一次性） | 双栈隔离 | 搭建 venv torch `2.7.1+cu128` vs TTS 栈 `2.9.1+cu126` |
| 搭建（一次性） | flash-attn | 默认跳过（`_requirements_without_flash` 滤除 + `[WARN]`），`--with-flash-attn` 走镜像链 |
| 出曲（每次） | 模型 | ACE-Step `2B turbo` + `0.6B` LM |
| 出曲（每次） | 产物规格 | `48 kHz` / `10.00 s` / 峰值 `0.8913` / RMS `0.0700` |
| 出曲（每次） | 结果通道 | stdout 恰好一行 JSON，`rc=0` |
| 出曲（每次） | 响度标尺 | 共享 `tools/bgm_loudness`：`-23 LUFS` / `-1 dBTP`，ACE-Step 实测 `-16.4 LUFS` |

**单测钉（本批次临时副本实跑）**：在仓的临时副本（无权重、假 acestep 模块、ffmpeg 在场）跑 `tests/test_music_service.py` 的 `TestLibraryOps`（8 钉：空库状态形态 / 无草稿保存失败 / 账本改写 / 重名拒绝 / 非法名拒绝 / 取消幂等 / 删除守卫 / 状态列出库）、`TestGenerateFailClosed`（4 钉：空描述、时长越界、缺环境指路、stdout 合同）、`TestGenerateHandoffOrdering`（5 钉：草稿存活、清场失败不误杀、原始中文只进账本、thinking 码保留、草稿响度归一），共 **17 钉，0 fail、0 error**（少数缺环境依赖用例按设计 skip）；把 `shutil.move` 挪回 `finally` 之后，顺序反向，该批钉子立刻红——钉的生效性由反向即红佐证 [3][5]。CHANGELOG 记录的同版本全量为 **1496 条通过**、该模块 **47 条钉子**、真机 10 秒生成 `rc=0` [1]。

### 实验设计（出曲侧收尾顺序钉的复跑）

- **目的**：确认"先搬后清"的顺序被测试钉死，且反向即红。
- **输入**：`music_service/music_gen.py`、`tests/test_music_service.py` 的目标测试类；临时副本（无权重，以假 `acestep` 模块按官方合同往 `save_dir` 写 wav 并裸 print 一行杂音，不加载任何权重）。
- **步骤**：`python` 标准库 `unittest` 加载 `TestLibraryOps` / `TestGenerateFailClosed` / `TestGenerateHandoffOrdering` 三类的全部方法并执行；另手工把 `music_gen.py:451` 的 `shutil.move` 移回 `finally` 之后复跑同批。
- **观测**：正常顺序下 17 钉全绿；反向后 `test_draft_survives_scratch_cleanup` 立即报"成品搬出临时目录之前被清场删掉了"，草稿 `isfile` 为假。
- **判定**：顺序正向全绿且反向必红，即"先搬后清"契约成立；与 CHANGELOG v2.0.0 记录的全量 1496 / 47 钉子相互印证 [1][3][5]。

## 七、结语：一句话可复用结论

把最重的活（装 torch、下权重）压进一次性搭建、让出曲侧只做"临时目录 → 草稿位 → 标尺 → 账本"四步，本地 BGM 出曲就从"需要人盯全程的手动多步搭建"变成"10 秒的一键"——**分清楚哪件事只做一次、哪件事每次都做，比把两件事揉在一起写更省心，也更不容易炸**。相邻篇 #23 会讲：即便拆干净了，出曲侧收尾那一步的顺序写反，照样能把整趟推理白烧掉。

## 引用与出处说明

> 来源声明：本篇实证全部取自 podcast-maker 真实代码仓与单测，无 web 来源；CHANGELOG 锚点统一署真仓 `CHANGELOG.md`，不出现快照/索引文件名 [1][2][3][4][5]。

| 编号 | 引用 | 出处 |
|------|------|------|
| [1] | v2.0.0 新增本地 BGM 生成模块；六步搭建脚本；真机跑通 10 秒曲目 `rc=0`（48 kHz / 10.00 s / 峰值 0.8913 / RMS 0.0700）；全量 1496 条通过；47 条 `test_music_service` 钉子 | `podcast-maker · CHANGELOG.md · v2.0.0` |
| [2] | `music_gen.py` 五子命令 CLI；`cmd_generate` 先搬后清（`:451`）/`finally` 清场（`:513`）；草稿流 `_draft.wav`+`_draft.json`；时长 10~30 s 拒收；stdout 一行 JSON | `music_service/music_gen.py:312,451,513` |
| [3] | `setup_music_env.py` 六步搭建；torch `2.7.1+cu128`；独立 venv 与 TTS 栈 `2.9.1+cu126` 互不搅动；镜像优选（上交大 6.3 / 官方 0.65 MB/s）；flash-attn 默认跳过 | `music_service/setup_music_env.py` |
| [4] | 响度归一唯一实现 `tools/bgm_loudness.py`；`-23 LUFS` / `-1 dBTP`；ACE-Step 产物实测 `-16.4 LUFS` 比内置档响 6.5 dB | `tools/bgm_loudness.py` |
| [5] | `TestLibraryOps` 8 钉 / `TestGenerateFailClosed` 4 钉 / `TestGenerateHandoffOrdering` 5 钉；本批次临时副本（无权重 / 假 acestep / ffmpeg 在场）实跑 17 钉 0 fail 0 error | `tests/test_music_service.py`（实测复跑，2026-10-20） |

> 说明：全部为项目实证（仓库源码与单测），无 KB / 联网文献；[5] 为本文推导层（实验设计段）的复跑记录，测量条件为仓的临时副本、当次版本 v2.0.0、日期 2026-10-20。

## 延伸阅读

- **#21 BGM 听不见**：本篇讲"本地怎么生成 BGM"，#21 讲"生成出来的 BGM 为什么在混音里听不见"——两者是同一模块的产出端与消费端。
- **#29 AI 生成件响度归一**：本篇提到的 `tools/bgm_loudness` 标尺，在 #29 展开"峰均比超 22.5 dB 的 limited 放行"的完整契约。
- **#27 BGM 转译层**：中文描述经 LLM 转英文 caption、又被 CoT 劫持的坑，是本篇"出曲侧只做四步"之外的前端一环。

---

*最后更新：2026-10-20（论证概要：本地 BGM 生成把"搭环境"与"出曲"拆成两件职责——一次性六步搭建（独立 venv / 镜像优选 / 权重自检）与每次 10 秒出曲（草稿流 / 共享响度标尺 / 一行 JSON）；实证取自真仓 CHANGELOG v2.0.0 与 music_service 源码、单测；文献佐证 5 条全为项目实证；四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
