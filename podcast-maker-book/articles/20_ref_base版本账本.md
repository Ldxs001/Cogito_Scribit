<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第三部 · 20｜ref_base 版本账本：换嗓串嗓事故的 sign 后缀与角色账本

> 摘要：克隆音色靠一条参考音频加文本确定性派生种子做逐句抽样。换嗓（adopt / adopt_official / inherit）是日常操作，但它一旦不失效旧参考件，合成就会静默用旧嗓子出整期声音。本文只讲这一个事故的拆机：为什么换嗓会串嗓、为什么体检会把「嗓源本身不对」误读成「每句都漂移」、以及 v2.6.0 用 sign 后缀 + 角色账本怎么把「换嗓零克隆、同源可追溯」钉死。边界声明：本文覆盖 v2.6.0 的 ref_base 版本账本（sign 后缀、换嗓三处接线、体检锚同源、旧件不兼容迁移）与 v2.10.0 把 ref_base 收为标定唯一参考的收束；C→B→V 演变线与 roster 接管基准嗓是背景脉络，点到即止。

## 一、引子：真实起点

克隆音色的工作方式是：一条参考音频（ref）加文本，确定性地派生种子做逐句抽样 [1]。参考音频不是一成不变的——换嗓是常态：用户认领一个新声库（adopt）、认领官方音色（adopt_official）、或从别的项目继承（inherit），都会换掉 `ref.wav` 与 `profile.json` [2]。

问题在于，换嗓只是「换参考」，并没有一个机制去失效与之配套的 `ref_base.wav` / `icl.wav`——这两件是克隆时按旧 ref 生成的。一旦旧件残留，合成链路就会静默拿旧嗓子出声，而系统里没有一个判定者说「这批声音是用旧嗓子合成的」[2]。

## 二、现象：它到底长什么样

事故在一次换嗓后爆发。某项目 13:35 认领声库新嗓（只换 `ref.wav` / `profile.json`），凌晨 01:03 旧嗓的 `ref_base.wav` / `icl.wav` 仍原样残留；`_ref_pair()` 的判定逻辑是「icl 两件齐备即用」，于是整期 **138 句**的合成条件全是旧嗓 [2]。

表象是体检大面积点名，但方向是反的：

- 体检锚 = 新 `ref.wav`，而合成条件 = 旧嗓的 `icl`（ref_base 系）——**锚与合成条件不同源**，Base 克隆的固有偏移被记到每一句头上 [2]。
- 结果：**73 句点名**、B 角整批嵌入相似度 0.71–0.85，换种子重出 **24 句全部无效** [2]。
- 实测 `cos(旧 ref_base, 新 ref)` = **0.809（B）**，**A 恰好新旧近源 0.974 所以 A 全过** [2]。

也就是说，点名大多不是「每句都漂移」，而是体检在正确报警——报的是「这批声音不是档案里那个人」。换种子重出 24 句全无效，因为嗓源本身就不是档案里那个人，调韵律救不了 [2]。

## 三、错误尝试：我们怎么绕弯的

绕弯走过两条路，都救不回来：

**其一，靠换种子重出想救。** 当时把 24 句拿去换种子重念，结果全部无效——嗓源本身就是旧人，韵律再怎么调，合成的还是旧嗓的音色，自然过不了体检。这条路的盲区在于它没意识到根因在「嗓源」，不在「韵律」[2]。

**其二，靠体检锚拿 `ref.wav` 去比对。** 这反而把问题放大：体检锚用的是新 `ref.wav`，合成条件用的是旧嗓的 `icl`（ref_base 系），两者不同源，Base 克隆的固有偏移被逐句记到头上，于是 73 句被点名、B 角整批破线。锚与合成条件不同源，体检越严，误报越多 [2]。

两条路同源的盲区：都在「合成之后」想办法，没人去管「合成之前参考件版本对不对、锚和合成条件是不是同一条嗓子」。

## 四、根因：为什么

根因两句话：

1. **换嗓认领不失效旧 ref_base / icl。** `_ref_pair()` 的判定是「icl 两件齐备即用」，它不核对这两件对应的 ref 字节是不是当前认领的那条。旧件残留 → 齐备 → 静默用旧嗓合成，整期 138 句条件全错 [2]。
2. **锚口径与合成条件不同源。** 体检锚拿 `ref.wav`，合成条件拿 `icl`（ref_base 系），两条嗓子不是同一条，Base 克隆的固有偏移被记到每一句头上。只要锚和合成条件来自不同的参考件，体检量到的就不是「这句漂不漂移」，而是「这两条嗓子差多少」[2]。

两个根因同源：参考件没有版本概念，既没在换嗓时失效旧件，也没让体检锚和合成条件指向同一条嗓子。系统靠「文件名 + 齐备即用」做判定，而文件名不带版本信息，记忆不可验证。

## 五、正确修法：怎么做对的

v2.6.0 的修法是给参考件上「版本账本」——文件名即映射、可验证不靠记忆。

### 5.1 sign 后缀：文件名即映射

`ref_base` / `icl` 全带 sign 后缀：`ref_base_<sign>.wav` / `icl_<sign>.wav` / `icl_<sign>.txt`，**sign = 原生 ref 的 sha256 前 8 位**。换一字节 ref，sign 就变，旧条目零克隆、不污染新嗓 [2]。

```text
sign = sha256(ref_bytes).hexdigest()[:8]          # 原生 ref 内容指纹，前 8 位
ref_base_<sign>.wav / icl_<sign>.wav / icl_<sign>.txt   # 文件名即映射
```

### 5.2 换嗓三处接线：旧件不丢、新件查账

- **`adopt`**：换嗓前把旧版本件 stash 出来再覆盖目录、拷完原样还原——旧嗓的 `ref_base` 一个不丢，换回旧嗓零克隆 [2]。
- **`adopt_official` / `inherit`**：认领后接 `ensure_base_ref()`——按当前 ref 字节重算 sign 查账，命中直接切 active，未命中才生成新条目 [2]。
- **`_ref_pair()`（唯一判定处）缺件 fail-closed**：icl 两件齐备才可用，缺件不静默回退旧嗓，交上层生成新条目 [3]。

### 5.3 体检锚与合成条件同源

声纹锚从 `ref.wav` 改为当期合成同源的 `ref_base_<sign>`；`voice_profiles` 带出 `base_wav` / `base_sign`，体检报告 `sv_info.anchors` 记录当期用的哪条嗓子，可追溯 [2]。当期用什么生成，就用什么检测——锚和合成条件从此是同一条嗓子。

### 5.4 旧无后缀件不兼容迁移

旧的无后缀 `ref_base.wav` / `icl.wav` 不做兼容迁移（未推送过，存量项目删了重做即可）[2]。

### 5.5 演变脉络：ref_base 是怎么长出来的

ref_base 不是 v2.6.0 凭空出现的，它是一条「基准嗓从哪来、版本归谁管」逐步收紧的线的成熟站。

v1.x 是双模型环境：Base 变体常驻做克隆，另起 CustomVoice 变体录参考音频、跑完即退。当时在 xvec_only（只喂向量）与 ICL（参考音频连同转录文本一起进上下文）两条路之间实测句间 F0 相对极差 27.4% vs 13.1%，据此定下 ICL 路线，xvec_only 官方标为实验性、不进产品；种子也从「音色名」换成音频内容指纹 sha256[:16]，而 ref.txt 因 ICL 把转录带进上下文而不可选 [5]。

v1.8.0 嗓音系统重构：CustomVoice 退役，音色变成「本地音频条目」——`official:名字#takeN`（官方预录）与 `named:名字`（VoiceDesign 入库）两类，选中即把该音频复制进项目槽位，此后该项目用这条音频，不再有按项目动态合成音色的模型路径；裸内置音色名输入按退役处理 fail-closed 报错 [6]。

v1.9.0 的 VoiceDesign 造嗓草稿流把「先落草稿再入库」定型，参考音频的产出从此走草稿 → 试听 → 入库的有据链路 [6]。

这条线一路把基准嗓的来源与版本逐步收紧，v2.6.0 的 sign 后缀账本正是收紧到「文件名即映射、可验证不靠记忆」的那一站——它不重新发明 ref_base，只是给它上了版本。

## 六、验证：数据说话

### 6.1 实验设计：sign 后缀账本逻辑（临时副本，stdlib 复刻）

**目的**：在临时副本上用 stdlib 复刻 `_ref_pair` / `ensure_base_ref` 的纪律，验证 sign 后缀机制能同时保证「命中复用」「版本隔离」「缺件 fail-closed」「角色隔离」四件事，且全不依赖真仓。

**输入**：以 sha256 模拟原生 ref 的内容指纹（sign = sha256(ref)[:8]）；构造 `ref_base_<sign>.wav` / `icl_<sign>.wav` / `icl_<sign>.txt` 三件套路径；`ensure_base_ref(role_dir, ref_bytes, ledger)` 复刻唯一判定处——icl 两件齐备才 `HIT_REUSE`，否则 `MISSING_FAIL_CLOSED`。

**步骤**：① 同内容两次算 sign，看是否相等（命中复用）；② 改 1 字节重算，看 sign 是否改变（版本隔离）；③ 只放旧 `ref_base` 不放 `icl`，调 `ensure_base_ref`，看是否 fail-closed；④ 两件齐备再调，看是否命中复用；⑤ 给 A/B 两角各算 sign，看是否不同（角色隔离）。

**观测**：各场景返回的判定串与 sign 值。

**判定**：同内容 sign 相等、改 1 字节 sign 改变、缺 icl 返回 fail-closed（不静默用旧）、齐件返回命中复用、A/B sign 不同，则账本四纪律成立。

实测（临时副本，未动真仓）：

| 场景 | 返回 / sign | 结论 |
|---|---|---|
| S1 同内容复用 | sign 两次均 `199aeb95`，相等 | 命中复用，不重做 |
| S2 版本隔离 | 改 1 字节 → `ec2d3271`，不同 | 旧 sign 条目不被新嗓复用 |
| S3 缺件 fail-closed | `MISSING_FAIL_CLOSED` / `6a349575` | 不静默用旧，交上层生成 |
| S4 齐件命中 | `HIT_REUSE` / `6a349575` | 账本命中，不重做 |
| S5 角色隔离 | A `343e8d96` / B `5f7f761f`，不同 | A/B 各归各 sign，合成条件与锚同源 |

*表 1：临时副本实验——sign 后缀账本四纪律全成立（stdlib 复刻 `_ref_pair` / `ensure_base_ref`，未动真仓）。*

### 6.2 落地验证（v2.6.0，真机 + 全量单测）

- **全量 1519 通过（skipped=1）** [2]。
- **删旧无后缀件 → 真机生成** `ref_base_a71d9702`（A）/ `ref_base_2d9a4787`（B）+ 账本落盘；复跑出「账本命中，不重做」；reader 判定 A/B 各归各 sign，合成条件与锚严格同源 [2]。
- **锚自检**：`cos(ref_base_<sign>, 原生 ref)` = **A 0.994 / B 0.974**——账本里的 ref_base 与当下原生 ref 高度同源，sign 映射可信 [2]。
- **存量消纳**：现有 138 句为旧嗓所出，新锚下 B 破线属预期，该期重出后即同源——点名是体检在正确报警，不是误杀 [2]。

*表 2：v2.6.0 事故 vs 修复对照（实测，CHANGELOG 记档）*

| 项 | 事故态 | 修复态 |
|---|---|---|
| 换嗓后旧件 | `ref_base.wav` / `icl.wav` 残留，静默用旧嗓 | sign 后缀隔离，旧件 stash 不丢、换回零克隆 |
| 整期合成条件 | 138 句全旧嗓 | 按当前 ref 字节查账，命中切 active |
| 体检锚 | 新 `ref.wav`（与合成条件不同源） | 当期 `ref_base_<sign>`（同源可追溯） |
| 点名方向 | 73 句点名、B 0.71–0.85、`cos(旧,新)` 0.809(B) | `cos(ref_base_<sign>,原生ref)` 0.994(A)/0.974(B) |
| 换种子重出 | 24 句全无效 | 嗓源对了，重出即同源 |

### 6.3 收束：ref_base 成为标定唯一参考（v2.10.0）

v2.10.0 把 ref_base 进一步收为标定的唯一参考：`make_base_ref._gen_baseref` 抽出候选挑选唯一实现（项目链 `build_role` 与标定链 `build_from` 共用），标定直接以 `ref_base` 本尊为参考、取该角色 `base_wav` + 单份 `ref.txt` 逐句合成，命令行 `--from-wav` / `--from-text` / `--out-dir` 脱离 `--project-dir`；`tts_engine.voice_entity_ref` / `ensure_calib_ref` 定位音色本体并缓存命中 [4]。「检测的同源性」从合验判据一路贯穿到标定的源头，与本篇的「锚与合成条件同源」是同一纪律的两次落地。

## 七、结语：一句话可复用结论

换嗓串嗓不是「合成质量」问题，是「参考件没有版本」问题——`_ref_pair()` 靠「齐备即用」做判定，文件名不带版本信息，记忆不可验证，于是旧件残留就被静默复用。v2.6.0 的修法只有一句话能概括：让文件名即映射——sign = sha256(ref)[:8] 后缀挂在 `ref_base` / `icl` 上，换嗓三处接线（stash 旧件 / 查账切 active / 缺件 fail-closed），体检锚也从 `ref.wav` 改到当期 `ref_base_<sign>`。命中复用、版本隔离、缺件 fail-closed、角色隔离四件事，从此不靠记忆、可验证。

### 引用与出处说明

| 编号 | 引用 | 出处 |
|------|------|------|
| [1] | 克隆音色工作方式：一条参考音频（ref）+ 文本确定性派生种子逐句抽样；参考音频非一成不变 | podcast-maker · CHANGELOG.md · v2.2.0（base_ref 进 ICL 上下文）/ v2.6.0（背景）<br>`tts_service/make_base_ref.py` |
| [2] | v2.6.0 ref_base 版本账本（换嗓串嗓事故修复）：事故（13:35 认领新嗓只换 ref.wav/profile.json，01:03 旧 ref_base.wav/icl.wav 残留；`_ref_pair()` 齐备即用→138 句旧嗓；体检锚=新 ref.wav 与合成条件旧嗓 icl 不同源→73 句点名、B 0.71–0.85、换种子重出 24 句全无效；`cos(旧 ref_base,新 ref)`=0.809(B)/0.974(A)）；修法（sign=sha256 前 8 位后缀；adopt stash 旧件 / adopt_official+inherit 接 ensure_base_ref 查账切 active；声纹锚改 ref_base_<sign>、voice_profiles 带 base_wav/base_sign、sv_info.anchors 记录；旧无后缀件不兼容迁移）；验证（全量 1519 通过；删旧无后缀件→ref_base_a71d9702(A)/ref_base_2d9a4787(B)+账本落盘、复跑账本命中不重做、reader A/B 各归各 sign；`cos(ref_base_<sign>,原生ref)`=A 0.994/B 0.974；138 句旧嗓所出 B 破线属预期重出后同源） | podcast-maker · CHANGELOG.md · v2.6.0 · 条目「ref_base 版本账本（换嗓串嗓事故修复）」<br>`tts_service/make_base_ref.py`；`podcast_maker/tts_engine.py:_ref_pair()` |
| [3] | `_ref_pair()`：ICL 参考唯一判定处——icl 两件齐备即用 icl，否则退回 `ref.wav`；v2.6.0 后缺件 fail-closed 不静默用旧嗓；声纹参考四处（检测 / 候选验收 / 基线池）全部改用 `ref_wav` 键（icl 含静音拼接件不得参与说话人相似度比对） | podcast-maker · CHANGELOG.md · v2.2.0（_ref_pair 初版）/ v2.6.0（fail-closed 收敛）<br>`podcast_maker/tts_engine.py:_ref_pair()` |
| [4] | v2.10.0 标定改以 ref_base 为参考：`_gen_baseref` 候选挑选唯一实现（build_role 与 build_from 共用）、`build_from` 脱离项目；`voice_entity_ref`/`ensure_calib_ref` 本体定位 + 缓存命中即用、落 `calib_refs/<角色>/<本体指纹前16>/`；标定取 base_wav 本尊 + ref.txt 逐句；全量 1612 通过 | podcast-maker · CHANGELOG.md · v2.10.0 · 条目「标定改以 ref_base 为参考、念角色自己的 ref.txt」「ref_base 的候选挑选收敛为唯一实现」「标定脱离项目」<br>`podcast_maker/tts_engine.py:voice_entity_ref`(:974)/`ensure_calib_ref`(:1049)；`tts_service/make_base_ref.py:_gen_baseref`(:210) |
| [5] | v1.x 双模型环境：Base 常驻克隆 + CustomVoice 录参考音频跑完即退；xvec_only vs ICL 实测句间 F0 相对极差 27.4% vs 13.1%（Base+ICL 13.1%），定下 ICL 路线、xvec_only 官方标实验性不进产品；种子从音色名换成音频内容指纹 sha256[:16]；ref.txt 因 ICL 把参考音频连同转录文本一起放进上下文而不可选 | podcast-maker · CHANGELOG.md · v1.x · 双模型环境 / ICL 路线决策<br>`podcast_maker/tts_service/serve.py`（Base 常驻 / C 录制）；`podcast_maker/tts_engine.py`（种子 sha256[:16]） |
| [6] | v1.8.0 CustomVoice 退役：音色=本地音频条目（`official:名字#takeN` 官方预录 / `named:名字` VoiceDesign 入库两类，选中即复制进项目槽位，无按项目动态合成音色的模型路径），裸内置音色名 fail-closed 报错，`parse_voice_source()` 统一解析；v1.9.0 VoiceDesign 造嗓草稿流（先落草稿再入库） | podcast-maker · CHANGELOG.md · v1.8.0 · 条目「嗓音系统重构——CustomVoice 退役，音色=本地音频条目，选中即复制」<br>`podcast_maker/tts_service/design.py`；v1.9.0 · VoiceDesign 造嗓草稿流 |

## 延伸阅读

- **同书 #19《声门三件套与傅里叶域分段》**：本篇的「体检锚与合成条件同源」是第 9 维能正确报警的前提——锚若不同源，就像本篇事故一样把「嗓源不对」误读成「每句漂移」。
- **同书 #14《音色漂移检测：从三维合验到五族合验》**：v2.10.0 把标尺 / 试听 / 标定收同源的收束（含标定改以 ref_base 为参考），与本篇「同源」纪律是同一底层原则的两次落地。

---

*最后更新：2026-10-19（含表1 sign 账本四纪律实验 + 表2 事故/修复对照 + 实验设计段（目的/输入/步骤/观测/判定）+ 伪代码(sign 计算/_ref_pair fail-closed) + v2.10.0 同源收束；四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
