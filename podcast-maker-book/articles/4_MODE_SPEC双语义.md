<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第一部 · 04｜一套配置管两种字幕模式：MODE_SPEC 接驳表的双语义

> 摘要：字幕有单行/双行与歌词两种模式，同一批配置（margin_lr、margin_v、bg_alpha、outline、lyric_max_rows）在两模式下语义完全不同——单双行里是「文字距边」，歌词里却是「框宽/框底/框透明度」。若每种模式各抄一份值域，迟早漂移。核心做法是一条：这些带模式的枚举点位集中在 MODE_SPEC 一张接驳表里，每项给界面一个 label、给管线一组 options 子值，界面与管线读同一份、不抄第二份。本文只讲这张接驳表的双语义，不展开单点渲染算法。

## 一、引子：真实起点

在字幕卡把模式从「单行」切到「歌词」，画面上的边距、透明度却没有跟着变——因为两种模式各自维护一份边界参数，切模式时只改了渲染分支、没改参数来源 [1]。这个症状的根不在「哪段渲染错了」，而在「同一批配置在两种模式下有两套解释，却没有一个地方统一说明」：单行里的 margin_v 是「文字距底边」，歌词里的 margin_v 却是「框底距底边」，同一个名字、两种含义，谁改了、以哪套为准，没有中央裁决 [1]。

## 二、现象：接驳表长什么样

`config_manager.py` 里，`MODE_SPEC` 是一个字典，每个键携带 `label` 与 `options` 两样东西 [2]。`label` 是给界面看的分类名（如「背景档位」「动画档位」），`options` 是一组子值，由管线按需取用——背景档位的某个选项里塞着 `bg_top` / `bg_bottom` / `accent` / `light` / `muted` 五个色值，动画档位的某个选项里塞着 `filter` / `cost` / `desc` [2]。一个典型条目形如：

```text
"background.preset": {
    "label": "背景档位",
    "options": {
        "ink":    {"label": "墨色极简", "bg_top": "#12224A", "bg_bottom": "#081630",
                   "accent": "#C9A45C", "light": "#E8EDF8", "muted": "#96A5C3"},
        "slate":  {"label": "冷灰学术", "bg_top": "#1A2430", "bg_bottom": "#0C1218",
                   "accent": "#6FA8DC", "light": "#E4EDF5", "muted": "#8FA3B8"},
    },
},
"animation.mode": {
    "label": "动画档位",
    "options": {
        "static":   {"label": "静止", "filter": "",            "cost": "最省",
                     "desc": "不做任何运动，纯静止背景"},
        "kenburns": {"label": "缓推", "filter": "zoompan",     "cost": "低",
                     "desc": "全程匀速缩放。会带动背景元素位移，构图会被放大"},
        "waveform": {"label": "波形", "filter": "showwaves",   "cost": "中",
                     "desc": "半透明声波随音频律动"},
        "spectrum": {"label": "频谱", "filter": "showspectrum","cost": "高",
                     "desc": "频谱条铺底，技术向"},
    },
},
```

`options` 里的子值不是给界面展示的，是给管线消费的：`bg_top` 进背景绘制、`filter` 进 ffmpeg 滤镜串、`cost` 进预算估算 [2]。界面只认 `label`，管线只认 `options` 里的具体键——一张表喂两路，各取所需。

![MODE_SPEC 一处定义，界面语义与管线语义两路消费](assets/4_MODE_SPEC双语义_fig1.svg)  
*图 1：`MODE_SPEC` 一处定义，每项 `label` 走界面语义（分区标题、下拉文案）、`options` 子值走管线语义（背景色值 / 滤镜 / 预算）；「同一批配置两种语义」的接驳关系在表里一眼可查（详见第四节两义对照）。*

## 三、错误尝试：每个模式各写一份值域、options 里裸塞原始值

两处具体翻车，都是「第二份真值来源」或「裸值外露」的变种。

其一，**每个模式各抄一份边界参数**：`margin_lr` / `margin_v` 在单行分支写一遍、在歌词分支又写一遍，两处各自解释同一个名字 [1]。后端改了歌词里的 `margin_v` 含义，单行分支的旧解释还在，界面上看不出任何异常——参数矛盾被两份副本各自掩盖。

其二，**options 里直接塞裸值当标签**：动画档位若把 `options` 的键（`static` / `kenburns`）直接当界面文案，下拉框就会显示英文内部名「static」「kenburns」，用户看见的是代码标识符而不是「静止」「缓推」[3]。后果是同一台机器上「配置页显示」与「内部消费」用的是两套语言，排查时只能对着裸值猜它是什么意思。

## 四、根因：为什么是接驳表而非双份

根因一句话：**凡同一件事存在两种语义，把两种语义各放一份，两份迟早不一致；不一致时没有人能判定哪份算数** [1]。字幕模式下的边界参数，本质就是「同一批名字、两种解释」：单双行管「文字背景填充 + 文字位置」，歌词管「一个固定宽高的半透明框，文字在框里」[1]。`margin_lr` 在单双行是「文字距左右」，在歌词却是「框宽（兼折行容量）」；`margin_v` 在单双行是「文字距底边」，在歌词是「框底距底边」；`bg_alpha` 在单双行是「每行填充块透明度」，在歌词是「整块框透明度」；`outline` 在单双行是「填充块内边距」，在歌词「不适用」；`lyric_max_rows` 在歌词是「框高 = 行数 × 行距」[1]。

这张两义对照，逐行列出就是接驳表的实质：

| 配置名 | 单/双行语义 | 歌词语义 |
|---|---|---|
| `margin_lr` | 文字距左右 | 框宽（兼折行容量） |
| `margin_v` / `margin_v_vertical` | 文字距底边 | 框底距底边 |
| `bg_alpha` | 每行填充块透明度 | 整块框透明度 |
| `outline` | 填充块内边距 | 不适用（仅单双行生效） |
| `lyric_max_rows` | —— | 框高 = 行数 × 行距 |

「接驳表」展开是三层纪律，缺一层就会长出第二份真值：

**定义处唯一。** 带模式的枚举点位只在 `MODE_SPEC` 写一遍，每项同时声明 `label`（界面语义）与 `options` 子值（管线语义）。任何模块需要这些信息，import 这张表，不复制字段。

**派生，而非抄写。** 界面要的枚举标签只从一个函数取：`param_options(key)` 是唯一的枚举标签来源，它读 `MODE_SPEC`、把每项的 `label` 与 `options` 的 `label` 组装成界面用的选项列表 [2]。界面不另写一份值域；`modes_payload()` 把这张表喂给配置页，`coerce(key, value)` 按声明做类型与值域校验，也是唯一入口 [2]。

**拒绝，而非过滤。** `coerce` 遇到不在接驳表声明里的模式值直接拒绝；`modes_payload` 只暴露 `MODE_SPEC` 里登记过的点。野值不是被悄悄吞掉，是被点名拒绝——写错模式名时一切照常、配置就是不生效的坑，在结构层就被堵上 [2]。

## 五、正确修法：一处定义 + 双语义 + 两路消费

`MODE_SPEC` 是唯一的「接驳处」，界面与管线各自从这里取，不另存副本 [2]：

- **界面消费（label 语义）**：`param_options(key)` 给出下拉选项与文案，`modes_payload()` 把整张接驳表喂给配置页——分区标题、选项文案全部来自 `MODE_SPEC` 的 `label`，不在前端再写一遍 [2]。`coerce(key, value)` 按接驳表声明校验用户选的值是否落在 `options` 里，是唯一入口 [2]。
- **管线消费（options 子值语义）**：背景绘制读 `options[选中的档].bg_top` 等色值；动画引擎读 `options[选中的档].filter` 拼进 ffmpeg；预算估算读 `options[选中的档].cost` [2]。管线不认 `label`，只认 `options` 里的具体键。

两个消费方的骨架（真实实现 `podcast_maker/config_manager.py`，`param_options` :1400、`coerce` :1427，伪代码化）：

```python
# config_manager.py —— MODE_SPEC 接驳表的两处接法：界面取档位、写入做校验
def mode_options(key):                             # 界面取档位
    if key not in MODE_SPEC:
        return []                                  # 界面不出现该控件
    return list(MODE_SPEC[key]["options"].items()) # 逐档返回（档位值, 显示标签）

def set(self, key, value):                         # 写入校验
    if key not in MODE_SPEC:
        raise ConfigError("未知模式点")
    if value not in MODE_SPEC[key]["options"]:
        raise ConfigError("野模式值")               # 野模式值不静默收下
# 显示标签是枚举值的唯一展示来源——PARAM_SPEC 里再写 options 会被忽略
```

`param_options` 与 `coerce` 不认识任何具体模式名——它们只读 `MODE_SPEC`。新增一个带模式的枚举点位，这两个函数一行不改；写进一个不在接驳表里的模式值，当场 `KeyError` / `ValueError`。

这张接驳表如今长到多大，实测数一遍（2026-10-13，对 `podcast_maker/config_manager.py:MODE_SPEC` L282 起逐键解析）：**17 个带模式的枚举点位（顶层键），其下共 64 档 options 子值，全部在 `PARAM_SPEC` 里有声明、0 个孤儿点**；其中 `subtitle.preset` 双档（single / lyric）、`animation.mode` 四档（static / kenburns / waveform / spectrum）、`bgm.preset` 十五档 [2]。界面标签直接等于裸值（如下拉显示「static」而非「静止」）的缺陷数：**0** [3]。这 17 个键的全貌如下，每一行都是「label 走界面、options 子值走管线」的双语义实例：

| 接驳表键 | 档数 | 界面 label（分类名） | 管线 options 子值（举例） |
|---|---:|---|---|
| `background.preset` | 3 | 背景档位 | `bg_top` / `bg_bottom` / `accent` / `light` / `muted` |
| `cover.preset` | 3 | 封面档位 | （仅 label，无管线子值） |
| `bgm.preset` | 15 | 背景音乐档位 | （label 即档名，无子值） |
| `animation.mode` | 4 | 动画档位 | `filter` / `cost` / `desc` |
| `speaker_indicator.mode` | 4 | 说话人提示 | `desc`（AB 字幕色 / 侧栏色块 / 立绘说明） |
| `subtitle.preset` | 2 | 字幕版式 | `axis` / `window` / `frame_rows` |
| `intro_outro.preset` | 2 | 片头片尾 | （label 即档名） |
| `tts.engine` | 2 | 语音引擎 | （label 含许可证标注） |
| `llm.backend` | 3 | LLM 后端 | `default_base_url` |
| `bgm.mode` | 4 | 背景音乐来源 | （label 即来源名） |
| `script.compress_ratio` | 3 | 压缩档 | `desc` |
| `script.style_preset` | 0* | 风格倾向 | 由 `PRESET_SPEC` 填充（划界权在人，LLM 不选） |
| `audio.sample_rate` | 6 | 采样率 | `desc` |
| `audio.channels` | 2 | 声道数 | `desc` |
| `audio.codec` | 2 | 音频编码 | `desc` |
| `video.fps` | 5 | 视频帧率 | `desc` |
| `video.encoder_preset` | 5 | 编码预设 | `desc`（值原样送编码器） |

合计：17 个键、64 档子值；`script.style_preset` 的 options 在文件末尾由 `_fill_preset_modes` 从 `PRESET_SPEC` 注入，故表里先留空——它仍是「标签来源只有一处」的同一纪律，只是填充时机延后 [2]。

## 六、验证：数据说话

三项证据，测量条件一并给出。

**双语义接驳实证**（数据源 [1]）：CHANGELOG 记「一套配置管两种字幕模式——单行/双行管文字背景填充与文字位置，歌词管一个固定宽高的半透明框」[1]；「接驳表（同一批配置两种语义）」逐行列出 `margin_lr` / `margin_v` / `bg_alpha` / `outline` / `lyric_max_rows` 在两模式下的不同解释 [1]。`MODE_SPEC` 字典即该接驳处，界面 label 与管线 options 子值均由其派生 [2]。

**两路消费对照实证**（数据源 [2]）：下表给出每个消费方读接驳表的哪一侧、用什么函数、做什么，印证「无第二份副本」。

| 消费方 | 读接驳表哪一侧 | 用什么函数 | 用途 |
|---|---|---|---|
| 界面 | `label`（分类名 + 选项文案） | `param_options` / `modes_payload` / `coerce` | 渲染下拉、分区标题、值域校验 |
| 管线 | `options` 子值（`bg_top` / `filter` / `cost` …） | 背景绘制 / 动画引擎 / 预算估算 | 取色值、拼滤镜、估成本 |

**接驳表守卫实证**（数据源 [2][3]）：对账测试把「接驳表只描述已在 `PARAM_SPEC` 声明的点」定为不变式，并断言「每个模式点都是枚举、每个模式默认落在它的 options 里、界面标签从不等于裸值」[3]。这些断言就是「接驳表双语义、两路消费」的机器守门，任何一次把接驳表漏填或把标签写成裸值都会当场红 [3]。

**双语义一致性复跑设计**（守门复跑，数据源 [2][3]）：三层派生可各自独立核对——① 任取接驳表一个键改它的 `label`，`param_options` 给出的界面文案应随之变、不需要改任何第二个文件；② 任取一个模式值塞进 `options` 之外，`coerce` 应 `ValueError`；③ 任取一个 `options` 子键（如 `bg_top`）改色值，背景绘制应直接吃到新值，不需要改管线别处。这三类核对都写成断言进了 `tests/test_config_keys.py`（TestConfigKeys 三例 + TestEnumLabels 两例，2026-10-13 复跑全 PASS）[3]。

**计数复跑**（数据源 [2]）：对 `MODE_SPEC` 逐键解析（2026-10-13）——顶层键 17、options 子值合计 64 档、孤儿点 0、`subtitle.preset` 双档 / `animation.mode` 四档 / `bgm.preset` 十五档分布如第五节；标签==裸值缺陷 0。这组数据是「接驳表撑得住增长」的试金石：17 个带模式的枚举点、64 档子值，没有催生第二张表或第二份值域，说明结构撑得住。

## 七、结语：一句话可复用结论

字幕两种模式下的边界参数，只在 `MODE_SPEC` 一张接驳表里统一说明：每项给界面一个 `label`、给管线一组 `options` 子值，界面与管线读同一份、不抄第二份值域。一处定义、双语义、两路消费——同一批配置在两种模式下的两种解释，漂移在结构里没有生长点。

这张接驳表的最终形态可以用一组对称关系收束：**定义一处**（`MODE_SPEC` + `label`/`options`）、**界面语义一处**（`param_options` / `modes_payload` 只读 `label`）、**管线语义一处**（`options` 子值直接进绘制/滤镜/预算）、**校验入口一处**（`coerce`，野模式值当场拒绝）、**两路消费但同一接驳处**。五处「一处」合起来，才是「接驳表双语义」的完整含义——不是少写几行代码，而是让界面和管线除了这张表没有第二个信息来源。

### 引用与出处说明

| 编号 | 引用 | 出处 |
|------|------|------|
| [1] | 「一套配置管两种字幕模式」；「接驳表（同一批配置两种语义）」逐行两义对照（margin_lr / margin_v / bg_alpha / outline / lyric_max_rows） | podcast-maker · CHANGELOG.md · v0.41.0（L1526 / L1554） |
| [2] | `MODE_SPEC` 字典与 `label`/`options` 双语义；`param_options`（唯一枚举标签来源）/ `coerce`（校验入口）/ `modes_payload`（喂配置页） | `podcast_maker/config_manager.py`（MODE_SPEC L282；param_options L1400；coerce L1427；modes_payload L1505） |
| [3] | 守卫：接驳表只描述已声明点、每个模式点都是枚举、每个默认落在 options、界面标签从不等于裸值 | `tests/test_config_keys.py`（TestConfigKeys L64：test_mode_spec_only_describes_declared_points L147 / test_every_mode_point_is_an_enum L151 / test_every_mode_default_is_one_of_its_options L157；TestEnumLabels L260：test_labels_are_never_the_raw_value L268 / test_style_preset_labels_come_from_preset_spec L298） |

## 延伸阅读

- **同书其他篇**：#2《配置总表如何同时驱动界面与管线》讲 `PARAM_SPEC` 一处定义，本篇的 `MODE_SPEC` 是它之下「带模式的枚举点位」的专门接驳表，两者共用「一处定义、两路消费」的纪律；#6《检查段修补为什么返回空补丁》是另一处「结构层上锁而非提示词层苦劝」的同源案例。

---

*最后更新：2026-10-13（字数补厚：MODE_SPEC 17 枚举点/64 档子值/0 孤儿/双档四档十五档实测（2026-10-13 逐键解析）+ 17 键全貌表 + 两义对照表 + param_options/coerce 守门伪代码（config_manager.py:1400/:1427）+ 双语义一致性复跑设计 + 计数复跑；四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS；2026-10-13 稿面修订：正文代码块伪代码化（STYLE_GUIDE §2.12），论证与证据未动）*
