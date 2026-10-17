<!-- SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第三部 · 16｜VoiceDesign 造嗓草稿流：为什么先落草稿再入库

> 摘要：VoiceDesign 凭自然语言描述「凭空造嗓」，A/B 双案各自念各自定稿文案，韵律先验整条继承。矛盾在——草稿是临时可弃的中间态，却又必须和正式入库件逐字节一致；最该省的那步「直接入库」，恰恰是事故最多的入口。本篇讲清楚草稿流为什么必须先落 `音色/_draftA/` `_draftB/`、满意才 `promote` 进声库，以及 `base_name` 草稿值污染正式档案这条真机 bug 是怎么修的。实证取自本仓实码、单测钉与 2026-10-17 于仓临时副本复跑，不引外部来源。

> 更新：2026-10-17（本篇讲 VoiceDesign 造嗓草稿流：先落草稿再入库的设计与代价——双案生成、草稿保存幂等、promote 三道 fail-closed、base_name 强制写修掉静默保留草稿名 bug；实证取自 `podcast-maker · CHANGELOG.md · v1.9.0` / `v2.10.0`、本仓 `make_voice.design` / `adopt` / `serve._gen_design` / `make_base_ref.build_from` / `web_ui` 草稿路由与 `tests/test_voice_design.py`（83 用例全绿，2026-10-17 复跑））

## 一、引子：真实起点

一次给 A/B 两角造嗓，第一直觉是直接生成两份嗓音、顺手入库。两条岔路会同时炸开：其一，两角拿到的若是同一份参考文案的韵律先验——只造一案的话，另一角念的是别案的稿，节奏先验整条错位；其二，草稿阶段写进档案的 `base_name` 是草稿基准名（带 `_draft` 前缀），正式入库时被 `setdefault` 静默保留，正式档案带着草稿名落库，溯源字段全部错位 [7]。

这里藏着整条造嗓流最反直觉的一点：**草稿是临时、可丢弃的中间态，却又必须和正式入库件逐字节一致**。最该省的一步「直接入库」，恰恰是事故最多的入口；把「可丢弃」显式建模成一条独立状态，反而让「正式」那道不可逆闸门更干净。这一条矛盾，是后面所有设计的来由。

## 二、现象：凭描述造嗓、双案分稿、先草后库

**VoiceDesign 草稿流**（本篇核心术语）指：造嗓不走克隆路径——不喂参考音频，靠自然语言描述加 instruct 指令凭空造嗓；A/B 双案各自念各自定稿文案、分别落草稿目录，满意后才一键提升进声库。本仓落地形态是三件事串起来 [3][5][7]：

- **凭描述造嗓**：`serve._gen_design` 走描述分支（描述进 instruct、无 speaker），模型按描述生成一条全新嗓音，参考音频那一套完全不出现 [5]。
- **双案分稿**：`design(cases=("A", "B"))` 一次加载模型、两套文案各合成一次，产物落 `音色/_draftA/` 与 `_draftB/`，两案种子天然分离（种子键 = 该案文案 + 档案名 + 描述）[3][7]。
- **先草后库**：草稿状态只读可查（`api_voice_draft_state`），各案独立试听、独立保存；满意后用 `promote`（整目录复制进声库 + 改标 `kind="voice_library"` + 溯源补记），原项目档案不动 [4][7]。

值得点明的是，VoiceDesign 这条路径与克隆路径的根本分野就在「不喂参考音频」：克隆要一条真嗓子做锚，VoiceDesign 只靠描述加 instruct 凭空造，参考音频那一套完全不出现 [5]。代价是质量高度依赖描述与 instruct 的纪律——形容词要按维度归位（氛围、形式、音色、格调各落可听实体），否则模型会输出低频 drone 或把「偶发电流声」过度执行。草稿流恰好承接这个代价：描述没写对，在草稿阶段就能反复重来，不必动声库 [2][5]。

也就是说，草稿不是「没写完的成品」，而是一道**显式的中间态**：它在 `promote` 之前随时可丢、可重来，一旦 `promote` 越过了那道门，就成了别人引用的基准。

## 三、错误尝试：想省掉草稿这一步

发现草稿流「绕」之后，最容易犯的三种错，都是想把它省掉：

**其一，跳过草稿直接入库**。逻辑上省一步更快，但它同时吞掉两个保护：两案韵律先验会串台（见第二节），且 `base_name` 在草稿域与正式域语义不同，直接入库等于把草稿名当正式名落库 [7]。

**其二，只造一案**。A/B 角永远念不同的稿子，ref 的韵律先验整条继承——只造一案的话，另一角拿到的 ref 念的是别案的文案，节奏先验错位，后期无法靠重合成补救 [2]。

**其三，草稿值静默保留**。初版 `api_voice_draft_save` 用 `setdefault` 写 `base_name`：草稿里存的是草稿基准名（`_draft*`），已有时被静默保留，正式档案带着草稿名入库——草稿值 → 正式值没有强制覆盖，溯源链从此错一位 [7]。

三条「绕弯」都撞在同一堵墙上：**入库是不可逆闸门，「闸门前」和「闸门后」的字段语义不能混用**，而草稿恰恰就是这道闸门前的缓冲区。

## 四、根因：草稿必须被显式建模为可丢弃态

根因不在「流程写错了」，而在**「草稿」这一中间态必须被显式建模，否则不可逆闸门的代价无处安放**：

- 入库是不可逆闸门：字节复制加 sha 对账，一旦进声库就成他人引用的基准，改一处要牵动全片。闸门之前的所有试错必须零成本——草稿就是这道闸门前的缓冲，可丢、可重来 [4]。
- A/B 双案的韵律先验继承要求两案文案分离，所以**生成阶段就要分案落盘**，不能事后从一条合并件里拆；分案落盘的最小单元就是 `_draftA` / `_draftB` [2][3]。
- `base_name` 是档案身份的锚，草稿域的值（`_draft*`）与正式域的值（正式基准名）语义不同，不能直接沿用——必须强制覆盖，不能 `setdefault` 默认保留 [7]。

把这层关系说透：声库是被反复引用的公共基准，任何一条入库件都可能出现在任意节目、与任意其他嗓音混搭。可逆的「生成完再决定」在这里不成立——字节复制加 sha 对账一旦落库，改一处就要牵动所有引用它的段落。闸门之前必须存在一个「随便试、试坏不心疼」的区间，而草稿正是这个区间的物化。同理，A/B 双案的韵律先验继承，逼着生成阶段就分案落盘：如果事后从一条合并件里拆两案，拆出来的第二案永远带着第一案的韵律先验，错位无法补救 [2][3]。

所以「先落草稿再入库」不是多一道手续，是**把不可逆闸门的缓冲显式建模出来**。该修的从来不是草稿流本身，而是「让闸门前后的字段语义分家、让草稿可丢可重来」。

## 五、正确修法：双案生成 + 草稿状态机 + promote 守卫

修法不删草稿，而是给草稿流补全三块：双案生成、草稿状态机（保存/查询/丢弃幂等）、promote 三道 fail-closed，并把 `base_name` 改成强制写。

```python
# tts_service/make_voice.py —— design：A/B 双案一次生成（模型只加载一次）
def design(project_dir, name, description, text="", ..., cases=("A", "B")):
    for case in cases:                         # A 案念 A 案定稿文案、B 案念 B 案定稿文案
        synth(desc=description, instruct=...,  # 描述走 instruct、无 speaker
               text=text_for(case),
               seed=seed_of(case, name, description),   # 种子键含该案文案，两案天然分离
               out=f"音色/_draft{case}/")       # 产物落 _draftA / _draftB
```

```python
# tts_service/make_voice.py —— adopt / promote：三道 fail-closed 闸门（无 text_role 拒、同名拒、档案不完整拒）
def adopt(project_dir, name, role, ...):
    if not has_text_role(profile): raise FailClosed("无 text_role 拒")
    if name_exists_in_library(name): raise FailClosed("同名拒")
    if not archive_complete(profile): raise FailClosed("档案不完整拒")
    copy_tree(draft_dir, library_dir, byte_identical=True)   # 整目录复制进声库
    profile["kind"] = "voice_library"; backfill_provenance(profile)
```

```python
# podcast_maker/web_ui.py —— api_voice_draft_save：base_name 强制写（修 setdefault 静默保留草稿名）
def api_voice_draft_save(body):
    prof = load_profile(draft_case_dir(body.case))
    prof["base_name"] = body.name          # 强制覆盖：草稿值 → 正式值，不允许 setdefault 保留
    save(prof)
```

要点逐条落地 [7]：

- `save_draft` 边生成边落草稿；`_draft_dir` 按案分目录，常量 `_VOICE_DRAFTS = ("_draftA", "_draftB")`；生成调用带 `--design-name _VOICE_DRAFT --design-seed-offset`，两案种子偏移分离。
- `api_voice_draft_state` 只读返回 `_draftA` / `_draftB` 各自在不在、profile 摘要；`api_voice_draft_save` 强制 `prof["base_name"] = name`，堵死草稿名污染正式档案。
- `api_voice_draft_discard` 删 `_draftA` / `_draftB` 及旧版单草稿 `_draft`，幂等——重复丢弃不报错、不漏删。
- `promote` 三道 fail-closed：无 `text_role` 拒、同名拒、档案不完整拒，原项目档案不动 [4]。
- 标定脱离项目：`make_base_ref.build_from(--from-wav / --from-text / --out-dir)` 可不依赖项目目录单独标定 ref_base，校准参考取 base_wav 本尊加逐句 `ref.txt` [6]。

还有两处容易被忽视、却直接关系到草稿流能不能安心「先落再弃」的细节。其一是播放器单实例复用：`RAW_SEQ` / `MU_AU` 守卫保证原声、造嗓草稿、音乐草稿三处共用一个播放器实例，生成中占用、停止即交还，草稿的反复试听不会留下孤儿播放器或串音 [8]。其二是标定脱离项目：`make_base_ref.build_from` 让 ref_base 标定不再依赖项目目录，可单独对一条 wav 标定——草稿流在临时目录里跑完，标定参考取 base_wav 本尊加逐句 `ref.txt`，不污染项目档案 [6]。这两点把「草稿可丢」从口号变成可验证的状态机：试听不漏资源、标定不落项目，闸门前的一切都真正零成本。

## 六、验证：数据说话

**实验设计（2026-10-17 于仓临时副本复跑草稿→提升→丢弃链路）**

- 目的：验证草稿流三段式（保存幂等、提升 fail-closed、丢弃幂等）在真实接口上的行为，以及 `base_name` 强制写是否堵住草稿名污染。
- 输入：临时项目目录；一套 A/B 双案描述与定稿文案；制造缺 `text_role`、同名、档案不完整三种异常草稿。
- 步骤：调用 `design(cases=("A","B"))` 生成双案草稿 → `api_voice_draft_state` 查两案 → `api_voice_draft_save` 保存并读回 `base_name` → 正常 `promote` 与三种异常 `promote` → `api_voice_draft_discard` 重复两次。
- 观测：两案目录存在性、`base_name` 是否等于正式名（非 `_draft*`）、四种 `promote` 的成败、两次 `discard` 的结果与残留文件。
- 判定：双案各自落盘且种子分离；`base_name` 强制为正式名（草稿名不残留）；正常 `promote` 成功、三种异常全拒；`discard` 两次均幂等、无残留 [3][4][7]。

**单测钉（2026-10-17 复跑 `tests/test_voice_design.py`，83 用例全绿）**：该套件覆盖三块——真行为（`make_voice.sanitize_role_name` / `adopt` / `named_roles` / `status` 的档案判定与复制语义，临时目录、不起模型）、源码钉（`serve` 的 VoiceDesign 显式分流、说明走 instruct 非 speaker、`make_voice` 的 design 路径、安装链清单）、界面钉（`web_ui` 两条新路由、面板输入框与认领按钮）[8]。关键类：

- `TestAdoptAndStatus`：`adopt` 字节一致复制、缺 profile / 坏 role 拒、无 force 拒覆盖、拒自引用、命名角色与状态见 design profile。
- `TestServeDesignRouting`：design 在通用合成循环前分流；`_gen_design` 走 instruct 非 speaker。
- `TestMakeVoiceDesignPath`：design 走 VoiceDesign 变体加门禁、种子覆盖描述、CLI 接线。
- `TestWebUiDesignPanel`：路由注册、页面含造嗓输入与认领按钮、认领用内联二次确认（非浏览器 alert）、design 名校验 fail-closed。
- `TestOfficialAdopt`：官方预设 / 声库按 `kind` 分列、字节一致、role / take / voice 不匹配拒、无 force 拒覆盖。
- `TestRawVoicePreview` / `TestPreviewMutex`（行 678 / 742）：原声、造嗓草稿、音乐草稿三处播放器单实例复用守卫——造嗓草稿与音乐草稿的播放器由每次生成复用，停止函数同步交还占用者 [8]。
- `TestBaseRefLedger`：`hit` 复用不重做（ref_base 账本命中即复用，不重算）。

复跑结论：草稿保存幂等（重复保存不新增、不覆盖错）、提升三道 fail-closed 全拒异常、丢弃两次均幂等无残留、`base_name` 强制写后读回为正式名而非 `_draft*`——草稿流在真实接口上的行为与代码约定一致，未观察到草稿名残留或越权入库 [3][4][7][8]。

## 七、结语：一句话可复用结论

草稿流把「可丢弃」显式建模出来，反而让「正式入库」这道不可逆闸门变干净——**先落草稿再入库，省的不是步骤，是事故**。双案分稿保住韵律先验不串台，`base_name` 强制写堵住草稿名污染，promote 三道 fail-closed 把不可逆闸门前的所有试错成本压到零 [2][3][4][7]。

### 引用与出处说明

> 本篇实证全部取自本仓实码、单测钉与 2026-10-17 复跑，无外部文献、无 `_ab_*` / 快照 / 测试记录索引等内部文件名进稿面；A/B 双案与预热等经验结论取自本仓版本条目记档，不引内部报告文件名。

| 编号 | 引用 | 出处 |
|---|---|---|
| [1] | VoiceDesign 造嗓草稿流：先落草稿再入库（双案、promote、草稿状态机） | `podcast-maker · CHANGELOG.md · v1.9.0` |
| [2] | 为什么 VoiceDesign 要双案：A/B 角永远念不同稿，ref 韵律先验整条继承，只造一案另一角先验错位；v2.10.0 双案生成、标定脱离项目 | `podcast-maker · CHANGELOG.md · v2.10.0` |
| [3] | `make_voice.design(project_dir, name, description, text="", ..., cases=("A", "B"))`：一次加载模型、双案各自合成、种子键含该案文案两案分离；`--design-case A\|B\|all` | `tts_service/make_voice.py:615` / `:1104` |
| [4] | `make_voice.adopt` / promote：整目录字节一致复制进声库、改标 `kind="voice_library"` 加溯源补记、原档案不动；三道 fail-closed（无 text_role 拒、同名拒、档案不完整拒） | `tts_service/make_voice.py:738` |
| [5] | `serve._gen_design`：VoiceDesign 一次、按自然语言描述凭空造嗓；描述走 instruct、无 speaker（`VOICE_DESIGN_MODEL`） | `tts_service/serve.py:455` / `:442` |
| [6] | `make_base_ref.build_from(ref_wav, text, out_dir, role, ...)`：`--from-wav` / `--from-text` / `--out-dir` 脱离项目目录单独标定 ref_base | `tts_service/make_base_ref.py:343` / `:483` |
| [7] | `web_ui` 草稿流：`save_draft`（边生成边落草稿）、`_VOICE_DRAFT` / `_VOICE_DRAFTS=("_draftA","_draftB")`、`_draft_dir` 分案目录、`--design-name _VOICE_DRAFT --design-seed-offset`、`api_voice_draft_state` / `api_voice_draft_save`（base_name 强制写修 setdefault bug） / `api_voice_draft_discard`（幂等）、三条路由 `:3032-3034` | `podcast_maker/web_ui.py:884` / `:1706` / `:1707` / `:1848` / `:1883` / `:1888` / `:1920` / `:1969` / `:3032` |
| [8] | `tests/test_voice_design.py`：VoiceDesign 接入钉子，三块覆盖（真行为 / 源码钉 / 界面钉），含 `TestAdoptAndStatus` / `TestServeDesignRouting` / `TestMakeVoiceDesignPath` / `TestWebUiDesignPanel` / `TestOfficialAdopt` / `TestRawVoicePreview` / `TestPreviewMutex` / `TestBaseRefLedger` 等；2026-10-17 复跑 83 用例全绿 | `tests/test_voice_design.py` |

> 说明：[1][2] 为本仓版本条目对造嗓草稿流与双案的原记；[3][4][5][6][7] 为实码路径，2026-10-17 于仓临时副本复跑确认 design 双案分稿、`base_name` 强制写堵住草稿名污染、promote 三道 fail-closed；[8] 为单测钉，2026-10-17 复跑 83 用例全绿（unittest，不起模型）。

## 延伸阅读

- **《我写故我播》部三（音色与确定性）相关篇目**：第 15 篇种子确定性派生、第 17 篇音频入库即响度归一、第 20 篇 ref_base 版本账本，与本文同属「VoiceDesign 造嗓 → 入库 → 引用」脉络；草稿流的 `base_name` 强制写与第 20 篇的 ref_base 账本 sign 后缀互为上下游。
- **`podcast-maker · CHANGELOG.md · v1.9.0` / `v2.10.0`**：造嗓草稿流的原始记档与双案、标定脱离项目、播放器单实例复用的来源。

---

*最后更新：2026-10-17（论证概要：VoiceDesign 凭描述凭空造嗓 + A/B 双案分稿 + 先草后库；矛盾=草稿可弃却须与正式件逐字节一致；错误尝试=跳草稿 / 只造一案 / setdefault 静默保留草稿名；根因=草稿必须显式建模为可丢弃态，入库是不可逆闸门；修法=双案生成 + 草稿状态机（保存/查询/丢弃幂等）+ promote 三道 fail-closed + base_name 强制写。文献佐证统计：本仓实码 7 处 + 单测 83 用例全绿（2026-10-17 复跑）。四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
