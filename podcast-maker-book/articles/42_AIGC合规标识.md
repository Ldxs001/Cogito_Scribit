<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第七部 · 42｜AIGC 合规标识落地：元数据、语音声明、字幕偏移

> 摘要：按《人工智能生成合成内容标识办法》与强标 GB 45438-2025，全部产物要补三层标识——元数据隐式标识、片头语音声明、封面水印。本文只讲这一个矛盾：合规不是「写个字段」那么简单，它横着要应付各容器对未知键的脾气（mp4 默认静默丢键），竖着要让声明时长与字幕时间轴共享一个偏移，否则画面字幕整体错位；而制作者身份绝不能由代码代填。

## 一、引子：真实起点

某次出片后抽查产物，用 `ffprobe` 读 mp4 的自定义元数据，读回来是空的——明明写进去了。翻日志才发现：mov 封装**默认静默丢弃**未知元数据键，不报错、不警告，标识等于白写。

同一期节目还有另一头隐患：语音声明想落在片头，可字幕时间轴是按「片头秒数」整体后移的。声明时长一旦没并进那个偏移，字幕就会比画面早半句或晚半句，听众看着口型对不上字。

合规不是装饰。它是法定义务（2025-09-01 施行），漏一块的片子不该被造出来。

## 二、现象：它到底长什么样

强标 GB 45438-2025《网络安全技术 人工智能生成合成内容标识方法》要求给生成合成内容打标识，落到本工具是**三层**：

- **元数据隐式标识**（无条件义务）：文件里写一段 JSON，含七要素；
- **语音显式标识**：音频片头最前加一句「本节目人声由人工智能合成」；
- **封面/背景水印**：「AI 生成」字样随图走。

但三层各有各的坑，不是「写个字段」就完事：

| 容器 | 写入方式 | 关键坑 |
|---|---|---|
| mp3 / aac | ffmpeg `-metadata`（ID3 TXXX） | 直写可读回，无特殊坑 |
| mp4 / mov / m4a | ffmpeg `-metadata` + `use_metadata_tags` | mov 封装**默认静默丢弃**未知键，不开 `use_metadata_tags` 写完读不回 |
| PNG | 文件内插 `tEXt` 块（IHDR 之后） | 纯标准库就地插入，不重编码 |
| JPEG | 文件内插 `COM` 段（SOI 之后） | 同上，超 65533 字节才需多段 |

语音声明还有个隐性坑：它占时长，而字幕时间轴只认「片头偏移」一个数。两者分家即错位 [1]。

## 三、错误尝试：我们怎么绕弯的

绕弯有三条路，都试过、都错。

**第一条：制作者留空时代填一个名字。** 直觉是「总得有个人名，填工具名或原作者名都行」。错——代填任何名字都是**伪造归属**，比不填更糟：不填只是缺项，代填是把别人的身份按到这份产物上。所以留空必须**报错停产**，绝不代填 [2]。

**第二条：声明时长和片头偏移各算各的。** 声明是一段音频、片头是另一段音频、字幕是另一条时间轴——三处若各持一个数，画面字幕必然错位。实测「偏移口径分家」正是字幕错位的成因；声明时长若没并进片头秒数，字幕整体后移的量就少算一段 [1][3]。

**第三条：给 mp4 直接写 `-metadata` 不开 `use_metadata_tags`。** 字段确实写进去了，可 mov 封装把它丢了，`ffprobe` 读不回来——标识静默失效，比明错更危险，因为没人会去查 [1]。

## 四、根因：为什么

根因是三道天然裂缝，不是一处笔误。

**第一道：容器对未知键的态度不一。** mp3 的 ID3 收一切 TXXX；mov 却默认丢未知键。同一段 JSON，落进不同容器命运不同——这是封装格式的天性，代码必须逐容器适配 [1][2]。

**第二道：声明是音频、字幕是时间轴，二者共享一个偏移。** 声明拼在片头最前，它占的秒数必须并进「片头偏移」那一个数，字幕时间轴只认这一个值。任何一处把声明时长藏起来单算，画面与字幕就脱节 [3]。

**第三道：制作者身份跟的是运行工具的人。** 开源后每个用户填自己的；代码里若预设任何人的名字，既违法理也不通用。所以 `ContentProducer` 是唯一要人填的必填项，留空即 fail-closed 停产 [2]。

> **fail-closed**：出错时默认失败、不静默继续，靠报错而非假装成功暴露问题。本篇指打标失败（ffmpeg 缺失、声明合成失败、自定义音频路径不存在）让整条流水线停下来，不跳过。

## 五、正确修法：怎么做对的

修复口径收在 `podcast_maker/aigc_label.py` 一个唯一入口，不让各调用方各写一套。

### 5.1 七要素 JSON，法定三项必填，留空即停产

`aigc_json(cfg, content_id)` 按强标七要素组装元数据，强制 `ensure_ascii`（ASCII 安全，任何容器文本段都放得下）。七要素里法律必填的只有三个——`Label`（生成合成标签，取值只能是 1/2/3，本工具恒取 1）、`ContentProducer`（内容制作者）、`ProduceID`（内容编号）。`ContentProducer` 留空直接抛 `LabelError` 报错停产，**绝不代填**；两个传播者要素首次写入时与制作者/制作编号镜像 [2]。

```python
# podcast_maker/aigc_label.py（节选，去敏）
REQUIRED_FIELDS = ("Label", "ContentProducer", "ProduceID")

def aigc_json(cfg, content_id=""):
    producer = str(cfg.get("aigc.content_producer") or "").strip()
    if not producer:
        raise LabelError(
            "AIGC 标识已开启，但内容制作者（aigc.content_producer）没有填。")
    payload = {
        "Label": "1",
        "ContentProducer": producer,
        "ProduceID": str(content_id or ""),
        ...
    }
    return json.dumps({FIELD: payload}, separators=(",", ":"))
```

内容编号 `ProduceID` 一律取**去扩展名的文件名**——产物文件名已含期号，天然唯一，不需要调用方再传一份编号 [1]。

### 5.2 隐式标识：逐容器适配，不重编码

`tag_file(path, ...)` 按扩展名分派：音视频走 ffmpeg 流直拷（不重编码），图片走块插入（纯标准库，不重编码）。mp4/mov/m4a 必须叠 `+use_metadata_tags`——实测开与不开的差别就是元数据在不在 [2]。

```flow
元数据隐式标识（AIGC 七要素 JSON，ASCII 安全）
    ↓
├─ 音频/视频 → ffmpeg -metadata（mp4/mov/m4a 叠 use_metadata_tags，防静默丢键）
├─ PNG → 在 IHDR 后插 tEXt 块（纯标准库，不重编码）
└─ JPEG → 在 SOI 后插 COM 段（同上）
```

图片打标**幂等**：已有同值 AIGC 标识的图直接跳过——续跑会反复路过同一批封面，重复插入只会把文件越撑越脏 [2]。

### 5.3 显式声明：落在片头最前，时长并入片头偏移

语音声明由编排层合成好，经 `audio_engine.add_intro_outro` 拼在片头**最前**——取起始位置的理由：听众在形成「真人在说话」的印象之前就该被告知；平台试听与推荐流只播开头，末尾提示等于没说 [1]。

关键是声明时长**并入片头秒数一起返回**，字幕时间轴拿这一个偏移整体后移，无需单独知道「声明」的存在——偏移口径分家正是字幕错位的成因，这里从源头堵死 [3]。

```python
# podcast_maker/audio_engine.py:149（节选）
def add_intro_outro(body, out_path, cfg, sample_rate, channels):
    # AI 语音声明固定排最前；声明时长并入片头秒数
    decl_sec = probe_duration_safe(decl) if decl else 0.0
    ...
    if decl_sec:
        intro_sec = decl_sec + intro_sec
    return out_path, intro_sec, outro_sec
```

封面与背景的「AI 生成」水印在 `assets_factory` 绘制，与元数据、语音声明三路都随文件走，不受平台转码是否保留元数据的影响 [1]。

## 六、验证：数据说话

四组证据，全部来自 `tests/test_aigc_label.py` 与真实容器复验。

**七要素齐套**（`TestAigcJson::test_seven_elements`）：七要素一个不少，必填三项齐、首写传播者要素与制作者一致、首写编号与制作编号一致；`Label` 恒为 `"1"`（附录 E 取值只能是 1/2/3）[4]。

**制作者留空即报错**（`test_producer_is_legally_required`）：空配置 / 空串 / 纯空白三种形态都抛 `LabelError`；填入「 我的名字 」去首尾空白后正确落 `ContentProducer`——绝不代填 [2][4]。

**ASCII 安全 + 容器可读性**（`test_ascii_safe` / `test_mp3_tag_readable` / `test_mp4_tag_readable`）：中文经 `ensure_ascii` 转义后 `raw.isascii()` 为真，任何容器文本段都放得下；mp3 用 ID3 TXXX 写后 `ffprobe` 能读回 `AIGC`；mp4 **必须**能读回（断言 `raw is not None`）——这条断言就是「mov 默认丢键」的防火墙 [2][4]。

**声明并入片头、字幕不错位**（`TestDeclarationOffset::test_decl_absorbed_into_intro`）：声明 1.0s + 片头 2.0s → `intro_sec` 实测 **3.0 s**（误差 ≤0.02s），总时长 **8.0 s**；`test_no_decl_no_intro_passthrough` 验证无声明无片头时偏移恒为 0 [3][4]。

**图片块插入与幂等**（`TestImageTagging`）：PNG 经 `tEXt`、JPEG 经 `COM` 写入后读回 `AIGC` 七要素；`test_tag_twice_is_idempotent` 断言同值重复打标**零改动**；错误魔数（非 PNG）被 `LabelError` 拒绝 [2][4]。

**配置面同源**（`test_config_surface`）：`PARAM_SPEC["aigc.content_producer"]` 默认 `""` 且 `required=True`，且**断言 JSON 里不含 `wUwproject`**——制作者身份不预设任何人名，开源后由每个用户自己填 [5]。

| 维度 | 验证点 | 断言（节选自 `tests/test_aigc_label.py`） |
|---|---|---|
| 七要素 | 七项齐、必填三项、Label=1 | `test_seven_elements` |
| 必填纪律 | 留空三形态全报错、去空白生效 | `test_producer_is_legally_required` |
| 容错 | ASCII 安全、写后可读回 | `test_ascii_safe` / `test_mp3_tag_readable` / `test_mp4_tag_readable` |
| 偏移 | 声明+片头=单偏移、总时长对 | `TestDeclarationOffset` 两组 |
| 幂等 | 同值重复打标零改动 | `test_tag_twice_is_idempotent` |
| 配置同源 | 默认空、必填、不预设人名 | `test_config_surface` |

## 七、结语：一句话可复用结论

合规标识不是写个字段：横着要逐容器适配（mp4 必须开 `use_metadata_tags` 防静默丢键），纵着要让声明时长与字幕偏移共享一个数，而制作者身份绝不代填——留空就 fail-closed 停产，比伪造归属安全。

### 引用与出处说明

| 编号 | 引用 | 出处 |
|------|------|------|
| [1] | 合规标识整体落地：七要素 JSON、语音声明片头最前（平台只播开头）、mp4 必须开 `use_metadata_tags`（实测开与不开差别即元数据在不在）、声明时长并入片头偏移（偏移分家是字幕错位成因）、打标失败报错停产不静默跳过、内容编号取文件名、平台侧边界 | podcast-maker · CHANGELOG.md · v0.11.0 · 条目「合规标识整体落地」 |
| [2] | `aigc_label.py` 唯一入口：`aigc_json` 七要素 / `REQUIRED_FIELDS` 三法定必填 / `LabelError` 留空报错不代填；`tag_file`/`tag_image`/`tag_media`（PNG tEXt / JPEG COM / mp4 `use_metadata_tags`）；ASCII 安全；图片幂等 | podcast-maker · CHANGELOG.md · v0.11.0 · 新增段<br>`podcast_maker/aigc_label.py`（项目实证） |
| [3] | `add_intro_outro` 声明排最前、声明时长并入 `intro_sec`、字幕时间轴只认这一个数 | podcast-maker · CHANGELOG.md · v0.11.0 · 变更段<br>`podcast_maker/audio_engine.py:149`（项目实证） |
| [4] | 七要素齐套 / 留空报错 / ASCII / PNG·JPEG roundtrip / mp3·mp4 读回 / 声明并入片头（decl 1.0+intro 2.0=3.0s，总 8.0s）/ 幂等 / 错误魔数拒绝 | `tests/test_aigc_label.py`（TestAigcJson / TestImageTagging / TestMediaTagging / TestDeclarationOffset，项目实证） |
| [5] | `PARAM_SPEC["aigc.content_producer"]` 默认 `""`、`required=True`、JSON 不含任何人名 | `podcast_maker/config_manager.py:PARAM_SPEC`<br>`tests/test_aigc_label.py::test_config_surface`（项目实证） |

## 延伸阅读

- **同书其他篇**：#43《更新日志写成技术文章》讲本工具「现象→根因→修法→验证」的体例来源；本篇 v0.11.0 正是这套体例从「故障复盘」升格为「合规落地」的一例。

---

*最后更新：2026-10-11（四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
