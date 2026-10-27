<!-- SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第三部 · 18｜stdout 纪律：结果通道为什么只能有一行 JSON

> 摘要：VoiceDesign 造嗓成功落盘，但父进程却报「音色工具没返回可解析的结果」。根因不在解析容错，而在协议——子进程的 stdout 被约定为「结果通道」，只能有一份 JSON；faster-qwen3-tts 的 CUDA 图预热用裸 `print` 把六行 `Warming up / Captured` 垫在结果 JSON 前面，父进程 `json.loads` 当场炸。修法不是让解析「更宽容」，而是把通道纪律焊死：`serve._stdout_to_stderr` 把库的杂输出重定向到 stderr（5 处调库点全包），`web_ui._cli_json` 在父进程侧按花括号配平抠出首个完整 JSON 块兜底（值内花括号天然免疫、抠不出返回 `None` 由调用方 fail-closed），`_sub_env` 注入 `PYTHONIOENCODING=utf-8` 消除 GBK 乱码进报错文案。本文用 2026-10-18 于仓临时副本复跑的突变实验（旧行为炸 / 新行为提取成功 / 值内花括号 / fail-closed / 真仓包裹点计数）实测，并对照 `tests/test_voice_design.py:1164` 的 `TestStdoutContract` 五个钉子。实证取自本仓实码与单测，不引外部来源。

> 更新：2026-10-18（本篇讲 stdout 纪律——结果通道只能有一行 JSON；矛盾=「解析炸了」表象下是协议层问题不是容错问题；错误尝试=父进程侧正则跳前几行 / 指望第三方库改 print；根因=子进程 stdout 被约定为结构化结果通道、库的进度日志不该走 stdout；修法=serve._stdout_to_stderr 重定向 + web_ui._cli_json 兜底双保险 + _sub_env 注入 UTF-8；实证取自 podcast-maker · CHANGELOG.md · v1.9.0 / v2.0.0、tts_service/serve.py:301、podcast_maker/web_ui.py:1544 / :1535 / :1567、tests/test_voice_design.py:1164、2026-10-18 于仓临时副本复跑的突变实验）

## 一、引子：真实起点

某次 VoiceDesign 造嗓，全流程跑完、嗓子也落盘了，父进程却弹一句「音色工具没返回可解析的结果」。翻日志，模型加载、CUDA 图预热、合成、落盘每一步都正常，唯独最后那一句解析失败。

把子进程的原始输出捞出来看，罪证就在最前面：

```text
\r\nWarming up predictor (3 runs)...\r\n
Capturing CUDA graph for predictor...\r\n
CUDA graph captured!\r\n
Warming up talker graph (3 runs)...\r\n
{"result": {"role": "_draft"}, "status": {}}
```

六行 `Warming up / Captured` 是 faster-qwen3-tts 的 CUDA 图预热用裸 `print` 直写 stdout 的杂讯，它们正好垫在结果 JSON 前面。父进程拿整段输出喂 `json.loads`，第一字节是 `\r\n`，解析直接炸——于是「成功了却报没成功」。

这不是偶发脏数据，是**约定冲突**：库把 stdout 当日志通道，父进程把 stdout 当结果通道，两边对「stdout 里该有什么」的理解根本没对齐。

## 二、现象：结果通道被杂行污染

本仓里，`make_voice --json` 模式下父进程要和子进程严格按「**stdout 恰好一份 JSON**」的契约通信。这条契约的隐含前提极其刚性：只要结果 JSON 前面或后面垫了任何非 JSON 字符，`json.loads` 就会失败——它不跳过前缀、不忽略杂行、不猜「哪段是结果」。

而麻烦在于，第三方库（这里是两个具体文件 `predictor_graph.py` / `talker_graph.py`）并不守约：同库的 `model.py` 规规矩矩用 `logger` 写日志，这两个文件却偷懒用 `print()` 直写 stdout。更糟的是，这类预热_print 是**在结果产生之前**发生的，所以杂行永远垫在最前面，恰好命中 `json.loads` 最脆弱的位置。

现象可以精确描述成一句话：**结果通道被库的进度/日志杂行污染，导致「成功」被解析层误判为「无结果」**。

## 三、错误尝试：我们怎么绕弯的

绕弯有两条路，都试过、都错。

**第一条：父进程侧正则跳前几行。** 直觉是「既然前面垫了杂行，那就跳过前 N 行再解析」。这路一上手就崩：
- 杂行数量是**库的实现细节**——今天预热 6 行，明天换版本可能 3 行或 9 行，跳行数是猜的；
- 杂行里可能本身就含 `{` 或 `}`（比如日志里打印某个 dict），按行硬切会把 JSON 拦腰斩断；
- 更隐蔽：万一库把结果也拆成多行 `print`，跳行逻辑直接把真结果跳没了。

这条错路把「解析健壮性」建立在「预测库的打印行为」上——而那是你控制不了的东西。

**第二条：指望第三方库改 `print`。** 让库作者把 `print` 换成 `logger`、或把预热日志改走 stderr。这是把本仓的契约正确性外包给别人的实现：库不归你管、升级不可控、且只对当前这一个库有效——下一个不守约的库照旧炸。修法不能绑定在某个库的良心上。

两条都撞在同一堵墙上：**想用「更聪明的解析」去容纳「不守约的通道」，本质是让结果通道的定义变得模糊；而模糊的通道定义，恰恰是不可治理的根源**。

## 四、根因：为什么不是解析容错问题

根因不在「解析该不该更宽容」，而在**协议层**：

子进程的 stdout 在本仓被约定为**结构化结果通道**——它的唯一合法内容是一份 JSON。这个约定的价值不在于「漂亮」，而在于它让 `json.loads` 的失败成为一个**精确的信号**：只要炸了，就一定是有东西越界进了结果通道。如果把解析改成「跳过杂行再猜」，这个信号就被淹没了——你再也分不清「库没返回」和「库返回了但前面垫了行」。

所以正确的根因表述是：**库的进度/日志输出不该走 stdout，而该走 stderr；stdout 只留给结果 JSON。** 这是「通道职责分离」，不是「解析兜底」。一旦把 stdout 锁死为结果专属，库的杂输出无论多少、何时产生，都不该出现在结果通道里——它们本就该去 stderr，被父进程当作进度读，而不是被当作结果解析。

这里藏着整条纪律最反直觉的一点：**真正的修复不是让消费方更宽容，而是让生产方更守约；宽容消费方等于把生产方的违约合法化，偏差从此不可见**。

## 五、正确修法：两层防御焊死通道纪律

修法不另起炉灶，而是把「stdout 仅为结果通道」焊进调库的正确位置，并用父进程侧兜底防住任何漏网的杂行。

```python
# tts_service/serve.py —— _stdout_to_stderr：stdout 仅为结果通道，进度一律 stderr
@contextlib.contextmanager
def _stdout_to_stderr():
    """本块内第三方库偷偷写进 stdout 的输出，一律赶到 stderr。

    本程序的 stdout 是**结果通道**：make_voice --json 模式下调用方要整段
    解析，垫进一行杂字就解析不了。而 faster-qwen3-tts 的 CUDA 图预热用裸
    print() 直写 stdout，六行 Warming/Captured 正好垫在结果 JSON 前面。
    """
    with contextlib.redirect_stdout(sys.stderr):
        yield
```

调用方把每次调库的块都裹进这个上下文管理器。原始实码里它包裹了**模型加载、预热、克隆合成、设计合成、内置合成共 5 处**——少一处，那条路第一次跑就会把库的 stdout 杂行垫进结果 JSON。

```python
# podcast_maker/web_ui.py —— _cli_json：从子进程输出抠出最外层 JSON（最后一道保险）
def _cli_json(tail: str):
    s = (tail or "").strip()
    if not s:
        return None                      # 空串直接 fail-closed
    dec = json.JSONDecoder()
    idx = s.find("{")
    while idx >= 0:
        try:
            obj, _end = dec.raw_decode(s, idx)   # 从每个 { 起试，取首个完整块
            return obj if isinstance(obj, dict) else None
        except ValueError:
            idx = s.find("{", idx + 1)          # 值里的 { 不会误切：raw_decode 天然免疫
    return None                                 # 抠不出返回 None，由调用方 fail-closed
```

`_cli_json` 是**最后一道保险**：即使 serve 层有漏网之鱼，父进程侧也能从被污染的 stdout 里把真正的 JSON 抠出来。`raw_decode` 从每个 `{` 起试解析、取第一个能完整闭合的块——值里出现的 `{` `}`（比如错误信息里写了「描述里有花括号 { 和 }」）不会误切，因为 `raw_decode` 按括号配平而非按行切。抠不出就返回 `None`，调用方 fail-closed 报错并带上原文片段，**绝不静默**。

```python
# podcast_maker/web_ui.py —— _sub_env：子进程环境注入 UTF-8，消除 GBK 乱码进报错文案
def _sub_env():
    return dict(os.environ, PYTHONIOENCODING="utf-8")
```

`_sub_env` 在拉起子进程时注入 `PYTHONIOENCODING=utf-8`，消除 Windows GBK 环境下「报错文案本身乱码、连错误都看不清」的次生问题——它和 `_cli_json` 同属「结果通道纪律」的配套，确保即便走到 fail-closed 报错，错误文案也是可读的 UTF-8。

要点逐条落地 [1][2][3][4][5][7]：

- **生产方守约**：`serve._stdout_to_stderr` 把库杂输出重定向到 stderr，5 处调库点全包，stdout 不再被污染。
- **消费方兜底**：`web_ui._cli_json` 按花括号配平抠首个完整 JSON 块，值内花括号不误切，抠不出返回 `None`。
- **fail-closed 不静默**：两层都失败时不假装成功，调用方据 `None` 报错并带原文，符合全书「不可见漂移最坏」的口径。
- **环境配套**：`_sub_env` 注入 UTF-8，保证报错文案可读。
- **官方仓同律**：v2.0.0 官方仓往 stdout 裸 print 两行 `Using precomputed LM hints` 污染结果通道，`music_gen.py` 用**同手法**新增 `_stdout_to_stderr`（实码 3 处包裹），真机实测 stdout 恢复「恰好一行 JSON」，两行杂音落进 stderr。

## 六、验证：数据说话

**实验设计（2026-10-18 于仓临时副本复跑，不动真仓）**

- 目的：验证「stdout 纪律」双保险——旧行为（裸 print 垫 JSON 前）必然炸，新行为（重定向 + 兜底）能稳定提取 JSON，且值内花括号不误切、无 JSON 时 fail-closed。
- 输入：从真仓 `tts_service/serve.py` 与 `podcast_maker/web_ui.py` 用 `ast` 抽取 `_stdout_to_stderr` / `_cli_json` 两个真实函数到临时命名空间；构造真实事故串（faster-qwen3-tts CUDA 图预热六行裸 print 垫在结果 JSON 前）。
- 步骤：① 旧行为直喂 `json.loads`；② 新行为先 `_stdout_to_stderr` 重定向库输出、再 `_cli_json` 提取；③ 值内含花括号的对象垫杂音后提取；④ 空串/纯文本/截断 JSON 三类 fail-closed 输入。
- 观测：旧行为是否炸、新行为 stderr 捕获杂行数、`_cli_json` 提取结果、值内花括号是否误切、fail-closed 是否返回 `None`、真仓包裹点计数。
- 判定：旧行为 `json.loads` 炸（复现事故）即 PASS；新行为提取出 `{"result": {"role": "_draft"}}` 即 PASS；值内花括号完整提取即 PASS；三类输入均返回 `None` 即 PASS；真仓 `serve.py` 包裹点计数与单测钉的 5 一致即 PASS。

**复跑实测（2026-10-18，仓临时副本）**

| 实验 | 输入 | 结果 |
|---|---|---|
| 1 旧行为 | 事故串直喂 `json.loads` | 当场炸：`Expecting value: line 2 column 1 (char 2)`（复现「无结果」误报） |
| 2 新行为 | 事故串先重定向再 `_cli_json` | stderr 捕获 1 行 `Warming`；提取 `{'result': {'role': '_draft'}, 'status': {}}` |
| 3 值内花括号 | `{"error": "描述里有花括号 { 和 } 也要能解析", "nested": {"k": "{v}"}}` 垫杂音 | 完整提取（含嵌套 `{'k': '{v}'}`，不误切） |
| 4 fail-closed | `""` / `"压根没有 JSON"` / `'{"error": "被截断的'` | 三者均返回 `None` |
| 真仓包裹点 | `serve.py` 中 `with _stdout_to_stderr():` | 计数 = 5（与单测钉一致） |
| 真仓包裹点 | `music_gen.py` 中 `with _stdout_to_stderr():` | 计数 = 3（v2.0.0 官方仓同手法） |

单测钉与实验互为印证：`tests/test_voice_design.py:1164` 的 `TestStdoutContract` 五个方法把契约焊死 [4]：

- `test_cli_json_extracts_from_polluted_stdout`：用本文实验 2 同款事故串，断言 `data["result"]["role"] == "_draft"`；
- `test_cli_json_survives_braces_inside_values`：值内花括号不误切（对应实验 3）；
- `test_cli_json_returns_none_fail_closed`：空串/纯文本/截断 JSON 均 `assertIsNone`（对应实验 4）；
- `test_stdout_to_stderr_redirects_lib_prints`：断言库 `print` 被赶到 stderr（对应实验 2 重定向）；
- `test_serve_wraps_all_lib_call_sites`：断言 `serve.py` 中 `with _stdout_to_stderr():` **计数 == 5**——少一处，那条路第一次跑就会污染结果通道，这正是「统一包裹点」纪律的硬保证。

## 七、结语：一句话可复用结论

结果通道只能有一行 JSON，不是因为解析器娇气，而是因为「通道职责分离」让失败成为精确信号。**真正的修复不是让消费方更宽容，而是让生产方守约**——`serve._stdout_to_stderr` 把库杂输出赶到 stderr（5 处全包），`web_ui._cli_json` 在父进程侧兜底抠 JSON（值内花括号免疫、抠不出 fail-closed），两条防线把「成功被误判为无结果」这一类事故从根上消掉 [1][2][3][4][5][7]。

## 引用与出处说明

> 本篇实证全部取自本仓实码、单测与 2026-10-18 于仓临时副本复跑，无外部文献、无 `_ab_*` / 快照 / 测试记录索引等内部文件名进稿面；复跑用 `ast` 从真仓 `tts_service/serve.py` 与 `podcast_maker/web_ui.py` 抽取真实函数到临时命名空间，不动真仓；真实事故串取自 `tests/test_voice_design.py:1174` 的同款六行 CUDA 图预热序列。

| 编号 | 引用 | 出处 |
|---|---|---|
| [1] | 造嗓报「音色工具没返回可解析的结果」：faster-qwen3-tts 加载与 CUDA 预热阶段裸 `print` 写入 stdout，垫在 JSON 结果之前致解析失败；修法 `serve.py` 新增 `_stdout_to_stderr()` 上下文管理器（stdout 仅为结果通道，进度一律 stderr），包裹模型加载、预热、克隆合成、设计合成、内置合成共 5 处；`web_ui` 侧 `_cli_json()` 按花括号配平取首个完整 JSON 块兜底、值内花括号不误切；`_sub_env()` 注入 `PYTHONIOENCODING=utf-8` 消除 GBK 乱码进报错文案 | `podcast-maker · CHANGELOG.md · v1.9.0` |
| [2] | `serve._stdout_to_stderr`：`@contextlib.contextmanager` 包裹 `contextlib.redirect_stdout(sys.stderr)`，注释明言「本程序的 stdout 是**结果通道**」；实码包裹 5 处调库点 | `tts_service/serve.py:301`（装饰器 `:300`） |
| [3] | `web_ui._cli_json`：`json.JSONDecoder().raw_decode` 从每个 `{` 起试取首个完整 JSON 块，值内花括号天然免疫，抠不出返回 `None`；`_cli_error` 也走 `_cli_json` 提取错误 | `podcast_maker/web_ui.py:1544` / `:1567` |
| [4] | `TestStdoutContract` 五方法：`_cli_json` 从污染 stdout 提取、值内花括号不误切、fail-closed 返回 `None`、库 print 重定向到 stderr、`serve.py` 包裹点计数 == 5 | `tests/test_voice_design.py:1164` |
| [5] | 官方仓往 stdout 裸 print 两行 `Using precomputed LM hints` 污染结果通道；修法 `music_gen.py` 新增 `_stdout_to_stderr()` 同手法（实码 3 处包裹），真机实测 stdout 恢复「恰好一行 JSON」，两行杂音落 stderr | `podcast-maker · CHANGELOG.md · v2.0.0` |
| [6] | 2026-10-18 于仓临时副本复跑突变实验：旧行为 `json.loads` 炸 `Expecting value: line 2 column 1`；新行为 stderr 捕获 1 行 `Warming` 并提取 `{'result': {'role': '_draft'}, 'status': {}}`；值内花括号含嵌套 `{'k': '{v}'}` 完整提取；三类 fail-closed 输入均返回 `None`；真仓 `serve.py` 包裹点 = 5、`music_gen.py` = 3 | 仓临时副本复跑实测（不动真仓） |
| [7] | `_sub_env` 注入 `PYTHONIOENCODING=utf-8`，消除 GBK 乱码进报错文案，与结果通道纪律配套 | `podcast_maker/web_ui.py:1535` |

> 说明：[1][5] 为本仓版本条目对 stdout 纪律的原记（v1.9.0 造嗓侧 + v2.0.0 官方仓同手法）；[2][3][7] 为实码路径，确认 `_stdout_to_stderr`（serve.py:301，5 处包裹）、`_cli_json`（web_ui.py:1544，花括号配平兜底、fail-closed）、`_cli_error`（:1567，同走 `_cli_json`）、`_sub_env`（:1535，UTF-8 注入）；[4] 为 `TestStdoutContract` 五个钉子（test_voice_design.py:1164），把包裹点计数钉死为 5；[6] 为 2026-10-18 于仓临时副本复跑的突变实验（旧行为炸 / 新行为提取成功 / 值内花括号 / fail-closed / 真仓包裹点计数），与单测钉互为印证。

## 延伸阅读

- **《我写故我播》部三（音色与确定性）相关篇目**：第 16 篇 VoiceDesign 造嗓草稿流（先落草稿再入库，本篇的 stdoud 纪律就在其落盘调用链上）、第 17 篇音频入库即响度归一（同属「落库做死、运行时只压整体档」的确定性脉络）、第 20 篇 ref_base 版本账本（换嗓串嗓事故的 sign 后缀与角色账本）；本部多篇共同构成「确定性不是调出来的，是结构上焊死的」。
- **`podcast-maker · CHANGELOG.md · v1.9.0 / v2.0.0`**：stdout 纪律的原始记档与官方仓同手法延伸；`tests/test_voice_design.py` 的 `TestStdoutContract` 是该契约的永久守卫。

---

*最后更新：2026-10-18（论证概要：stdout 纪律——矛盾=「成功被误判为无结果」表象下是通道协议冲突；错误尝试=父进程正则跳行 / 指望第三方库改 print；根因=子进程 stdout 被约定为结构化结果通道、库杂输出不该走 stdout（通道职责分离，宽容消费方=把生产方违约合法化）；修法=serve._stdout_to_stderr 重定向(5 处全包) + web_ui._cli_json 兜底(花括号配平、值内花括号免疫、fail-closed) + _sub_env 注入 UTF-8，双保险。实证：2026-10-18 仓临时副本突变实验（旧行为 json.loads 炸 / 新行为提取 {'result':{'role':'_draft'}} / 值内花括号含嵌套 {'k':'{v}'} 完整提取 / 三类 fail-closed 均 None / serve 包裹点=5、music_gen=3），对照 TestStdoutContract 五钉子（test_voice_design.py:1164）。文献佐证统计：版本条目 2 处 + 实码 4 处 + 单测 1 处 + 复跑 1 处。四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
