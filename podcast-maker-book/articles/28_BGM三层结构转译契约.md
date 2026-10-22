<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第四部 · 28｜BGM 三层结构转译契约：caption/lyrics/元数据与中频塌陷 drone 墙

> **结论先行**：背景 BGM 能生成（#22）、中文也能被转译成英文三层输入（#27），但生成的 30 秒曲子几乎都在第 6 秒后「塌掉」——前 6 秒中频（300-2k）还占 92~96%，从第 6 秒起持续塌陷，18 秒后中频只剩 0.1%、80-300Hz 占 98%，退化成一条恒稳低频 drone 墙铺到曲末。根因不在模型「不会写音乐」，而在转译契约本身：旧转译层只产一个 `caption` 字符串，`lyrics` 硬编码 `[Instrumental]`、三个元数据字段全走默认空——三层里两层半是空的，模型建完开场氛围就没有任何「演进指令」，只能静态铺底。v2.9.0 的修法是把转译指令重写为输出 JSON 三层（caption 长句含编排演进 / lyrics 用结构标记写时间脚本 / 元数据给 bpm·keyscale·timesignature），并用 `_parse_bgm_translation` 在代码层做确定性校验（bpm 限 30~300、拍号只认 2/3/4/6、相邻结构标记拆行），解析不出结构即降级按原文直出。本文只谈这一个智能体的三层契约与中频塌陷根因；转译层的 CoT 劫持与四维归位见 #27，AI 生成件的响度标尺见 #29 [1][2][3]。
>
> 更新：2026-10-23（本篇属第四部「背景音乐」，承 #27 的「中文→英文三层输入」，专门拆开「为什么必须是三层协同、缺一层就退化成 drone 墙」这一契约级根因与 v2.9.0 的修复；实证取自 podcast-maker 真仓 `CHANGELOG.md · v2.9.0`、`web_ui` / `music_gen` 源码、单测，以及本批次在仓临时副本用 stub-LLM 与直接解析回放的对照实验 [1][2][3][4][5]）

## 一、引子：真实起点

让模型生成一段 30 秒垫底 BGM，给一句「诡异的低音氛围」就能出曲——这件事在前两篇里已经打通：#22 解决了本地生成链路，#27 解决了「中文描述怎么变成模型吃得动的三层输入、又怎么不被它自己的 CoT 劫持」。链路是通的，但生成的曲子听起来「怪」。

怪在形状：前几秒还有点氛围，往后越来越闷，最后二十多秒只剩一团压在低频的轰鸣，没有任何推进。这不是偶发——分段频谱矩阵实测，多版、多 seed 一致复现，是一条能被稳定观测到的退化曲线，不是「手气不好」[1]。

本文的起点，就是把「链路通了、曲子却退化成 drone 墙」这件事讲清楚：问题不在模型能力，而在我们交给模型的「契约」缺了一多半 [1]。

## 二、现象：它到底长什么样

v2.9.0 把 BGM 转译从「单个 caption 字符串」升级为「三层结构化输入」，并修掉了中频塌陷。先看清两层现象。

**三层契约（`caption` + `lyrics` + 元数据）**：ACE-Step 官方输入是三层协同——
- `caption`：整体画像，一行英文写风格、氛围、乐器、音色，且要体现编排的演进；
- `lyrics`：时间脚本，纯器乐用结构标记写音乐如何随时间展开（`[Intro - ambient]` / `[Main Theme - sparse bass]` / `[Outro - fade out]`）；官方明说纯音乐可只填 `[Instrumental]`，但那是无演进写法——垫底 BGM 恰恰要演进，否则模型建完开场就退化成静止 drone；
- 元数据：`bpm` / `keyscale` / `timesignature`，节奏与调性锚点 [1][2]。

**中频塌陷、退化为 drone 墙（分段频谱矩阵实测）**：连续多发生成的 30 秒 BGM，前 6 秒中频（300-2k）占 92~96%；第 6 秒起持续塌陷，18 秒后中频仅 0.1%、80-300Hz 占 98%，整段退化成一条恒稳低频 drone 墙（多版、多 seed 一致复现）[1]。

**代码层确定性校验（`_parse_bgm_translation`）**：不靠模型自觉，做硬校验——`bpm` 取整并限官方区间 30~300，越界置 `None`（回到自动估计）；`timesignature` 只认 2/3/4/6，其余清空；`lyrics` 把挤在一行的相邻结构标记拆成一行一个；`caption` 空即判失败（它是必需层，没它整趟白转）[2]。

**降级口径（`_bgm_fallback`）**：LLM 不可用或答不出可解析结构时，WARN 降级——`caption` 吃原文、`lyrics` 走 `[Instrumental]`、元数据留空、`degraded=True`，不拦生成。损失止于这一次生成 [2]。

## 三、错误尝试：我们怎么绕弯的

绕弯集中在「要么不给演进指令、要么给错了演进维度」。

**第一类想当然：只产单个 `caption`，`lyrics` 硬编码 `[Instrumental]`，元数据全默认空**。这是「模型内部有 LM 规划器、给个整体画像它自己会发展」的放任版——结果模型建完开场氛围后没有任何时间脚本与节奏锚点，只能把开场状态静态铺底到曲末。三层里两层半是空的，又反过来逼出更闷的低频补偿。这是 v2.9.0 之前线上真实跑的形态 [1]。

**第二类想当然：加「第五维律动」去补演进**。既然缺演进，就往转译指令里加一个「律动」维度，并给默认律动例外。真机第三发实测音符时值标准差 0.60→0.303、拍层稳定，确有正向数据——但这是「在错的契约层上打补丁」：律动维度没有解决「两层半为空」的结构问题，只是把演进的希望押在一个维度上。v2.9.0 把这第五维与同期一处未发布的措辞收控改动一并回退 [1]。

**第三类想当然：措辞收控把 `deep sub bass` 引导进 80-300Hz**。试图用描述把能量「搬」出低频，却把 drone 从 <80Hz 闷响变成有实际声压的低频墙，听感反而退化；更糟的是「80-300Hz 仅 2.2%」被误判为病灶，而那「空洞」实为「无 drone」，能量搬入反而放大问题。回退依据正是这条反直觉观测 [1]。

三类弯的本质一样：**演进指令的位置错了**——要么全压在 `caption` 一个维度上、要么押错维度、要么用描述去硬挪频谱。正确的落点是把「演进」显式写成 `lyrics` 时间脚本，并用元数据给节奏锚点，三层一起讲同一个故事。

## 四、根因：为什么

把现象拆开，根因只在「契约结构」一处，干净利落。

**需要三层协同的根因**：ACE-Step 的生成由 `caption`（场景画像）+ `lyrics`（时间脚本，控制音乐随时间展开）+ 元数据（节奏调性锚点）三层共同驱动；三层必须一致（caption 的乐器要对应 lyrics 的器乐段标记，caption 的情绪要对应 lyrics 的能量标记），模型不擅长解决冲突。旧转译层只产单个 `caption` 字符串，指令全文未提 `lyrics`、结构标记与元数据字段——转译模型既不知道这些字段存在、也没有输出通道；生成侧 `lyrics` 硬编码 `[Instrumental]`、三个元数据字段全走默认空。于是**三层中两层半为空**，模型建完开场氛围后无演进指令，静态铺底到曲末，这就是中频塌陷、退化为 drone 墙的契约级根因 [1]。

**为什么退化形态恰好是「低频 drone 墙」**：缺了时间脚本与节奏锚点后，模型没有「往哪推进」的约束，倾向于把能量压进最稳、最不易冲突的低频持续音；而中频（300-2k，承载旋律与大多数乐器音色）因为没有演进标记去激活，逐步塌空。分段频谱矩阵里「前 6 秒中频 92~96% → 18 秒后 0.1%、80-300Hz 占 98%」正是这条机制的投影，不是独立故障 [1]。

**校验必须落在代码层而非模型层**：`bpm` / 拍号 / `lyrics` 换行这些结构性字段，若靠模型「自觉」就会漂移（越界 bpm、非法拍号、相邻标记挤一行）。v2.9.0 把它们收进 `_parse_bgm_translation` 的确定性校验，喂什么错值都拦得住，模型只负责产出语义、结构合法性由代码兜底 [2]。

## 五、正确修法：怎么做对的

修法不另起炉灶，而是重写转译契约 + 代码层兜底校验，并撤销叠加在错层上的补丁。

**转译指令重写为输出 JSON 三层，且写明三层一致性铁律**：`caption` 长句含编排演进；`lyrics` 用官方结构标记写时间脚本（`[Intro - ambient]` / `[Main Theme - sparse bass]` / `[Outro - fade out]`），段落控制在 2~4 段；元数据给 `bpm` / `keyscale` / `timesignature`；并明确三层讲同一个故事、只保留用户提到的元素。`cmd_generate` 同步增 `lyrics` / `bpm` / `keyscale` / `timesignature` 四参，`GenerationParams.lyrics` 由硬编码 `"[Instrumental]"` 改为 `lyrics or "[Instrumental]"`（保留纯器乐缺省），元数据按传入值填 [1][3]。

```python
# podcast_maker/web_ui.py —— translate_bgm_prompt：三层 JSON 转译指令（四维归位 + 预算走统一推动点）
def translate_bgm_prompt(cfg, prompt, log=None):
    instruction = (转译指令：caption 一行英文 ≤60 词、四维各落执行域、"
                   "lyrics 用 [Intro - ambient] / [Main Theme - ...] 写时间脚本、"
                   "元数据 bpm/keyscale/timesignature 锚节奏调性、三层一致、只保留用户提到元素)
    try:
        llm = make_llm(cfg)
        text, _ = llm.chat([{"role": "user", "content": instruction}],      # instruction 末尾拼 prompt（中文）
                           temperature=0.2,
                           max_tokens=int(cfg.get("llm.max_tokens", 8192)))  # 预算走统一推动点
    except LLMError as e:
        log("LLM 转译失败（%s），按原文直接生成。" % e); return _bgm_fallback(prompt)
    data = _parse_bgm_translation(text)                                     # 代码层确定性校验
    if data is None:
        log("LLM 转译没答出可解析的三层结构，按原文直接生成。"); return _bgm_fallback(prompt)
    return data
```

**代码层确定性校验，不靠模型自觉**：解析出来后，`bpm` 限 30~300、越界置 `None`；`timesignature` 只认 2/3/4/6；`lyrics` 挤行拆行；`caption` 空即失败降级。这些判定是确定性的 [2]。

```python
# podcast_maker/web_ui.py —— _parse_bgm_translation：bpm 30~300、拍号 2/3/4/6、lyrics 拆行、caption 空降级
def _parse_bgm_translation(text):
    body = 抽取 {} 之间(text)                       # 容忍 ```json 围栏与前后杂话
    obj = json.loads(body)
    caption = " ".join(str(obj.get("caption") or "").split())
    if not caption: return None                      # caption 空即判失败（必需层）
    lyrics = 拆行(obj.get("lyrics"))                 # 相邻结构标记拆成一行一个
    try:
        bpm = int(obj.get("bpm"))
        if not 30 <= bpm <= 300: bpm = None          # 越界置 None，回到自动估计
    except (TypeError, ValueError): bpm = None
    tsign = str(obj.get("timesignature") or "").strip()
    if tsign not in ("2", "3", "4", "6"): tsign = "" # 只认四拍号，其余清空
    return {"caption": caption, "lyrics": lyrics or "[Instrumental]",
            "bpm": bpm, "keyscale": ..., "timesignature": tsign, "degraded": False}
```

**生成侧透传四参 + 撤销错层补丁**：`cmd_generate` 把三层字段透传 CLI，落稿账本新增 `lyrics` / `bpm` / `keyscale` / `timesignature` 四字段；同期回退到四维版（删除第五维律动维度行与默认律动例外、撤除未发布的措辞收控改动）——回退的依据是措辞收控把能量误搬进 80-300Hz、且第五维虽有正向数据但压不住「两层半为空」的结构病灶 [1][3]。

```python
# music_service/music_gen.py —— cmd_generate：三层参数透传 + 落稿响度归一（见 #29）
def cmd_generate(lib, prompt, seconds, seed, ..., lyrics, bpm, keyscale, timesignature):
    params = GenerationParams(
        caption=prompt, lyrics=(lyrics or "[Instrumental]"), instrumental=True,
        bpm=bpm, keyscale=keyscale or "", timesignature=timesignature or "",
        duration=float(seconds), thinking=True,
        use_cot_caption=False, use_cot_language=False, use_cot_metas=False, seed=eff)
    ...
    norm = loudness.normalize_file(wav, ffmpeg=ff, allow_limited=True)   # 落稿归一，标尺见 #29
```

## 六、验证：数据说话

**转译契约与代码层校验（本批次 stub-LLM + 直接解析双重真实实验，见图）** [5]：

| 验证项 | 真实数字 / 口径 | 出处 |
|---|---|---|
| 中频塌陷现象 | 前 6 秒中频（300-2k）92~96%；第 6 秒起持续塌陷；18 秒后中频仅 0.1%、80-300Hz 占 98% | `CHANGELOG.md · v2.9.0` [1] |
| 真机回退后 | 0-27 秒中频（300-2k）稳定 4.1~9.2%（回退前 18 秒后为 0.1%）；谱重心 94~153 Hz；rms -17.5~-24.6 dBFS 无断崖 | `CHANGELOG.md · v2.9.0` [1] |
| 真机账本三层字段 | `lyrics` = `[Intro - deep sub-bass]` / `[Main Loop - subtle electric crackle]` / `[Outro - seamless match]`、`bpm=70`、`keyscale=D minor`、`timesignature=4`、`lm=pt`；落稿 -22.99 LUFS（`norm_limited=false`） | `CHANGELOG.md · v2.9.0` [1] |
| 代码层校验（本批次回放） | `bpm=999` → `None`；`timesignature=5` → `""`；挤行 lyrics 拆行；caption 空 → 判定失败降级 | 本批次临时副本实测 [5] |
| 降级路径（本批次回放） | 答非 JSON 三层结构 → `degraded=True`、`caption` 退回原文、`lyrics=[Instrumental]`、日志含「三层结构」 | 本批次临时副本实测 [5] |
| 单测钉 | `TestBgmCaption` 3→5 条：转译成功 / 预算=`llm.max_tokens` / 降级原文 / 答非 JSON 降级 / 结构性字段代码层校验；本批次复跑全 PASS | `tests/test_music_service.py`（实测复跑，2026-10-23）[4] |
| 全量回归 | 1551 → 1553 通过（skipped=1） | `CHANGELOG.md · v2.9.0` [1] |

**单测钉（本批次临时副本实跑）**：`tests/test_music_service.py` 中 `TestBgmCaption` 钉住转译成功取三层字段、预算走 `llm.max_tokens`、LLM 不可用或答非 JSON 时降级原文、以及结构性字段由代码层校验四类行为；本批次在仓临时副本复跑 5 条全部 PASS，与 CHANGELOG 同版本全量 1551→1553 相互印证 [1][4]。

### 实验设计（三层契约真实回放与校验突变）

- **目的**：确认转译层在真实代码路径上确实输出三层结构、代码层校验能拦截错值、且 LLM 不可用时降级不拦生成；并直接验证 `_parse_bgm_translation` 的确定性校验。
- **输入**：仓的临时副本（含真仓 `web_ui.py` 的 `translate_bgm_prompt` / `_parse_bgm_translation` / `_bgm_fallback`）、一个 stub LLM（按真实 `make_llm` 接口，`chat` 返回受控 JSON 或抛 `LLMError`）、出厂 `llm.max_tokens=47872`；另直接调用 `_parse_bgm_translation` 喂各类 JSON 字符串。
- **步骤**：① 正常路径——stub 返回合法三层 JSON（含四维归位 caption + 多行 lyrics + bpm/keyscale/timesignature），观测解析结果；② 校验突变——stub 依次返回 `bpm=999`、`timesignature=5`、挤在一行的 lyrics、caption 空串，并直接喂带围栏 ` ```json ` 的三层串，观测代码层是否拦截（→`None` / `""` / 拆行 / 降级）；③ 降级突变——stub 抛 `LLMError` 或答非 JSON，观测是否 `degraded=True` 且 `caption` 退回原文。
- **观测**：正常路径三层字段齐全；`bpm=999`→`None`、`timesignature=5`→`""`、挤行 lyrics 被拆行、带围栏 JSON 被正确抽取、caption 空→判定失败走降级；`LLMError`/非 JSON→`degraded=True`、`caption=原文`、`lyrics=[Instrumental]`、日志含「三层结构」。
- **判定**：三层契约的「转译成功 / 代码层校验 / 降级」在真实代码路径上全部成立，与 `TestBgmCaption` 及 CHANGELOG v2.9.0 记录相互印证；实验后副本弃用，真仓未动 [1][2][4][5]。

## 七、结语：一句话可复用结论

背景 BGM 要的是「演进」，不是「一段好听的开场」——演进必须显式写成 `lyrics` 时间脚本、用元数据给节奏锚点，三层一起讲同一个故事；只要三层里有一层空着（尤其 `lyrics` 与元数据），模型就会退化成静态铺底，频谱上就投影成「前几秒中频还在、往后塌成低频 drone 墙」。一句话可复用：**多输入协同的契约，缺一层不是「少点信息」，而是逼模型用最稳的低频去填空白；结构性字段的合法性必须收进代码层校验，不能押在模型自觉上**。#27 讲「中文怎么变成它能懂的三层输入、又怎么不被 CoT 劫持」，本篇补上「为什么必须是三层、缺一层就退化」这道契约级闸门；过了这道闸，AI 生成件还要过 #29 的唯一响度标尺。

### 引用与出处说明

> 来源声明：本篇实证全部取自 podcast-maker 真实代码仓、单测与本地 stub-LLM / 直接解析实测，无 web 来源；CHANGELOG 锚点统一署真仓 `CHANGELOG.md`，不出现快照/索引文件名 [1][2][3][4][5]。

| 编号 | 引用 | 出处 |
|------|------|------|
| [1] | v2.9.0 三层结构转译契约升级：现象（30 秒曲目约 6 秒后中频塌陷、18 秒后中频仅 0.1%、80-300Hz 占 98% 退化为 drone 墙，分段频谱矩阵实测、多版多 seed 复现）；根因（三层协同中两层半为空）；修法（`_parse_bgm_translation` 代码层校验，bpm 30~300、拍号 2/3/4/6、相邻结构标记拆行）；真机验证（落稿 -22.99 LUFS、`norm_limited=false`、0-27 秒中频稳定 4.1~9.2%、谱重心 94~153 Hz）；撤销第五维律动与未发布措辞收控；全量 1551→1553 | `podcast-maker · CHANGELOG.md · v2.9.0` |
| [2] | `web_ui.py`：`_bgm_fallback`（`:115`，降级口径）/`_parse_bgm_translation`（`:122`，bpm 30~300、timesignature 2/3/4/6、lyrics 拆行、caption 空判失败）/`translate_bgm_prompt`（`:162`，指令重写三层 JSON + `max_tokens` 走 `llm.max_tokens`） | `podcast_maker/web_ui.py:115,122,162` |
| [3] | `music_service/music_gen.py`：`cmd_generate`（`:312`，增 `lyrics`/`bpm`/`keyscale`/`timesignature` 四参，`GenerationParams.lyrics = lyrics or "[Instrumental]"`）；落稿账本新增三层字段；同版本回退到四维版 | `music_service/music_gen.py:312` |
| [4] | `tests/test_music_service.py`：`TestBgmCaption`（`:400`，3→5 条：转译成功 / 预算=`llm.max_tokens` / 降级原文 / 答非 JSON 降级 / 结构性字段代码层校验）；本批次临时副本实跑全 PASS | `tests/test_music_service.py`（实测复跑，2026-10-23） |
| [5] | 本批次 stub-LLM 真实回放 + 直接 `_parse_bgm_translation` 探测：正常三层→非降级、带围栏 JSON 正确抽取；`bpm=999`→`None`、`timesignature=5`→`""`、挤行 lyrics 拆行、caption 空→判定失败降级；非 JSON→`degraded=True`、caption 退回原文、`lyrics=[Instrumental]`、日志含「三层结构」；测量条件为仓的临时副本、当次版本 v2.9.0、日期 2026-10-23 | 本文实验设计段（实测，2026-10-23） |

> 说明：全部为项目实证（仓库源码、单测与本地 stub-LLM / 直接解析实测），无 KB / 联网文献；[4][5] 为本文推导层（实验设计段）的复跑记录，测量条件为仓的临时副本、当次版本 v2.9.0、日期 2026-10-23。

## 延伸阅读

- **#27 BGM 转译层**：本篇讲「为什么必须是三层、缺一层就退化成 drone 墙」，#27 讲「中文描述怎么变成英文三层输入、又怎么被 CoT 劫持」——两者是同一转译层的正反两面，#27 是本篇的上一层。
- **#22 本地 BGM 生成**：本篇的三层契约最终要喂给 #22 的本地生成链路；#22 解决「怎么生成」，本篇解决「喂给它的契约为什么必须是三层」。
- **#29 AI 生成件响度归一**：过了三层契约的 BGM 最终还要过 #29 的唯一响度标尺（-23 LUFS / 真峰值 -1 dBTP），与内置档同尺——契约管「结构对不对」，标尺管「响度齐不齐」。

---

*最后更新：2026-10-23（论证概要：BGM 三层结构转译契约——现象=30 秒曲目约 6 秒后中频（300-2k）从 92~96% 塌陷、18 秒后仅 0.1%、80-300Hz 占 98% 退化为低频 drone 墙（分段频谱矩阵实测、多版多 seed 复现）；根因=三层协同（caption/lyrics/元数据）中两层半为空（旧只产单个 caption、lyrics 硬编码 [Instrumental]、元数据全默认空），模型建完开场无演进指令静态铺底；错误尝试=只给 caption / 加第五维律动补丁 / 措辞收控误搬能量入 80-300Hz（均已回退）；修法=转译指令重写输出 JSON 三层 + `_parse_bgm_translation` 代码层确定性校验（bpm 30~300、timesignature 2/3/4/6、lyrics 拆行、caption 空降级）+ cmd_generate 透传四参 + 撤销第五维与措辞收控；实证=本批次临时副本 stub-LLM 与直接解析回放（bpm=999→None、tsign=5→''、挤行拆行、非 JSON→degraded=True）+ TestBgmCaption 5 条复跑全 PASS + CHANGELOG v2.9.0 真机（落稿 -22.99 LUFS、0-27 秒中频 4.1~9.2%、谱重心 94~153 Hz、全量 1551→1553）。文献佐证全为项目实证。**四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
