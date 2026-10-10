<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 第三部 · 13｜本地语音服务的显存为什么越占越多：黑窗、孤儿进程与 Job 对象

> 摘要：本地 TTS 服务是主程序拉起的独立进程；若不显式处理 Windows 的进程副作用与显存归属，就会留下占着数 G 显存的孤儿进程、每次合成弹黑窗挡在前面，甚至起服务时锁死整页、标定与音色工具在 CPU 上偷偷出波形。本文讲这几类副作用的根因与修法：用 **Job 对象** 解决孤儿与显存泄漏，用 **CREATE_NO_WINDOW** 解决黑窗，v2.10.0 再把起服务移出业务锁、给标定与音色工具补腾显存并烙设备身份。边界声明：Job 对象是 Windows 内核机制，非 Windows 退化为从前行为、不挡合成。

## 一、引子：真实起点

本地 TTS 跑批，用户合上笔记本前顺手关了主窗口，第二天再开，显卡风扇狂转——任务管理器里躺着两三个 `python` 进程，各占着几 G 显存，实际早已没有一期刊物在生成。

另一类反馈更直接：每次点「合成」，屏幕正中央弹出一个黑色控制台窗口，从开工挂到收工，刚好挡在字幕预览上。合成完它自己消失，但下一次又来。

这两件事看起来不相关：一个在后台偷显存，一个在前面挡视线。查下来是同一个源头的两种表现——本地语音服务作为**独立进程**被拉起时，Windows 的两套默认规则没被覆盖。

## 二、现象：两种失败形态

**形态 A · 黑窗**：每次合成，一个黑色控制台窗口随服务进程弹出，合成期间常驻前台。根因在控制台窗口的继承规则，与显存无关，但体验上最扎眼。

另有一处同根的症状：服务每次回 `/health` 探活都要 spawn 两次 `nvidia-smi` 量显存，单次合成与试听路径每次查询就各弹一次黑窗——不是合成才弹，是每次探活都弹，积少成多更烦。

**形态 B · 孤儿进程 + 显存泄漏**：主程序被强杀（关窗、崩溃、任务管理器「结束任务」）后，语音服务进程照常活着，带着已加载的权重继续占着数 G 显存，不释放。下次启动又拉一个，越积越多，直到显存耗尽、新合成失败。

表 1 把两类失败并排，便于看清它们各自对应哪条 Windows 规则。

| 维度 | 形态 A · 黑窗 | 形态 B · 孤儿进程 + 显存泄漏 |
|---|---|---|
| 可见表现 | 合成时弹黑色控制台窗口挡视线 | 主程序死后服务进程仍在，占显存 |
| 触及的 Windows 规则 | 控制台窗口的继承/创建规则 | 进程无「父死子亡」默认语义 |
| 旧凑法 | `DETACHED_PROCESS` | 主程序退出时手动 `kill` |
| 旧凑法的代价 | 反而更稳地弹窗（见第三节） | 主程序被强杀时根本没机会执行清理，kill 不到真身 |

**形态 C · 起服务锁死整页状态接口**：`acquire_service` 原本把 `_spawn_service`（内含最长 90 秒的 `_wait_ready`）整个包在 `_SERVICE_LOCK` 里——而这把锁同时护着所有读锁入口（状态接口、试听取标尺等）。起服务期间，任何读锁请求都排队等这把锁，界面观感即整页卡死 [6]。

**形态 D · 标定与音色工具未腾显存，参考音频在 CPU 上生成**：`unload_llm_models()` 全仓原来只在 `synthesize()` 内调一处，标定（`api_voice_calibrate`）、标尺构建（`_std_ruler_synth`）、四处音色工具（认领 / 声库认领 / 录制 / 造嗓，经 `make_voice.py` 子进程进 `make_base_ref.build`）这三类链都没调它 [7]。音色工具的显存判定发生在**子进程**内、按整卡空闲内存挑设备（门槛 5300 MB），LM Studio 驻留期间静默退回 CPU；而 CPU 与 CUDA 两条路径产出**不是同一条波形**（同一输入 md5 不同）[7]。后果：标定量得的语速与成片实际语速可能不同源，生成的 `ref_base` 与成片不在同一波形上。证据：本项目 `音色/` 下 14 份 `ref_base` 记录里 7 份 `device: cpu`、7 份 `cuda`，同一小时内反复横跳 [7]。

表 2 把 v2.10.0 修的两处并排，看清它们各自对应哪条机制。

| 维度 | 形态 C · 起服务锁死整页 | 形态 D · 标定 / 音色工具未腾显存 |
|---|---|---|
| 可见表现 | 起服务期间整页状态接口排队卡死 | `ref_base` 偶发在 CPU 上生成、与成片不同波形 |
| 触及的机制 | `_SERVICE_LOCK` 把起服务（含 90s 等待）与所有读锁入口串行 | 子进程设备判定不看主进程已占显存，静默退 CPU |
| 旧凑法 | 起服务直接包在锁内 | 只在 `synthesize` 内腾显存 |
| 旧凑法的代价 | 读锁入口全陪等 90 秒 | 标定 / 成片不同源、`ref_base` 波形漂移 |

## 三、错误尝试：曾经怎么凑

**黑窗一侧，先试了 `DETACHED_PROCESS`**——它的语义是「新进程没有控制台」。结果黑窗反而以另一种方式出现：语音服务自身确实无台，但服务是被 venv 的 `Scripts\python.exe` 启动器再拉起真身解释器的中间层。DETACHED 这个标志不向启动器向下透传，真身解释器发现自己没台可继承，就**自建一个新控制台**——黑窗照弹。

这带来两处具体后果：批量路径下服务要等整批 batch 收工才释放，黑窗从合成开工一直挂到收工；试听路径每次探活都 spawn `nvidia-smi`，于是每次查询再闪一个窗——黑窗不是一次，是每次探活都来一次。

**孤儿一侧，先试在主程序退出时手动 `proc.kill()` / `terminate()`**。两个缺口让它不可靠：其一，主程序握着的柄是 venv 启动器，不是真身解释器，kill 启动器不等于 kill 真身；其二，主程序被强杀（崩溃、任务管理器）时，清理代码根本没机会跑。再退一步想遍历子进程树挨个杀，又撞上 pid 重用与竞态——前一秒的 pid 下一秒可能是别的程序。

第一点值得展开：venv 的 `Scripts\python.exe` 只是个启动器，运行时会再 `exec` 一次真正的解释器；主程序 `kill` 掉的是启动器，真身早已独立运行、带着已加载权重继续占显存——这正是「杀了父没杀到子」的具象。也正因为这层中间层，强杀主程序时清理回调根本触不到真身，孤儿就这么来的。

**起服务一侧，旧做法是把 `_spawn_service` 整个塞进 `_SERVICE_LOCK`**——锁的初衷是护住服务状态槽的并发写，但起服务自带的 90 秒 `_wait_ready` 也被一起锁住，读锁入口在锁外干等 [6]。这不是「锁错了对象」，而是锁的粒度没把「起服务」与「读状态」分开。

**腾显存一侧，旧做法是只在 `synthesize()` 内调一次 `unload_llm_models()`**——标定与音色工具走的是另一批入口，根本不经过它；子进程里的设备判定又只看整卡空闲内存，主进程已占的显存它看不见 [7]。两条链各算各的，显存该腾没腾。

## 四、根因：Windows 的两套默认规则

先看清本地语音服务的进程关系——它不是「主程序拉一个服务」那么简单，中间隔着 venv 启动器：

| 结构 | 进程链 | 主程序被强杀后 |
|---|---|---|
| 无 Job 绑定 | 主程序 → venv 启动器（`Scripts\python.exe`）→ 真身解释器 → 语音服务（持显存） | 启动器与真身不归主程序管，服务照活，显存不还 |
| 有 Job 绑定 | 上述整条链被 `AssignProcessToJobObject` 关进同一 Job | 内核关 Job 句柄即杀整棵树，显存必还 |

这张表也是后面修法的落点：黑窗要管的是「控制台谁继承」，孤儿要管的是「这条链归谁回收」。

**黑窗根因**：Windows 下 `subprocess` 起进程，若不显式给 `CREATE_NO_WINDOW`，子进程（及其再拉的真身）按默认规则尝试继承或创建控制台。`DETACHED_PROCESS` 让「服务自身」断开控制台，却因不向下透传，把建台的任务甩给了真身解释器。真正的修法是给一个**隐藏但存在**的控制台——启动器与真身都继承这同一个隐藏台，谁也不弹窗。

**孤儿根因**：Windows 进程没有「父死子亡」的默认语义。语音服务是独立进程（自己的进程组），父进程（主程序）死了它照活。显存绑定在服务进程的 GPU 地址空间，进程不死，显存就不还。要回收，必须有一个比「父进程退出回调」更硬的抓手——而 Windows 内核恰好提供：把进程挂进 **Job 对象**后，Job 句柄关闭时内核会杀掉 Job 内整棵树，这不受主程序是否还能执行代码影响。

旧的清理脚本也救不了这个局面：重启时的清理只按 `main.py` 命令行匹配进程，根本匹配不到 `serve.py` 拉起的服务，所以孤儿清不掉、显存还不了，只能人去任务管理器手动杀——这正是「谁起的谁关」约定没有内核级兜底时的典型下场。

两个术语首次出现，各给一句展开：**Job 对象**是 Windows 内核的一种容器对象，把一组进程绑在一起，容器关闭时里面的进程全部终止——好比把服务进程和真身解释器关进同一个笼子，笼门一关全死；**孤儿进程**是父进程已退出但子进程还活着的进程，本篇里即主程序被关、语音服务仍在后台占显存的那一个。

**形态 C 根因**：`_SERVICE_LOCK` 的持有区间覆盖了「起服务」这一长耗时动作，而读锁入口与起服务共用同一把锁——锁的粒度错配，把局部串行放大成全局串行 [6]。

**形态 D 根因**：腾显存动作与「谁在合成」绑定，而不是与「任何要占用 GPU 的本地推理」绑定；且设备判定发生在子进程边界内，无法感知主进程已占用的显存，于是 LM Studio 驻留期间静默退 CPU，CPU / CUDA 两条路径波形不同源 [7]。

## 五、正确修法：Job 绑定 + CREATE_NO_WINDOW

黑窗一侧，启动服务时给进程创建标志 `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`（仅 Windows），全链路隐藏控制台：

```text
# podcast_maker/tts_engine.py:495 —— 拉起本地语音服务
# 用 CREATE_NO_WINDOW（隐藏控制台）而不是 DETACHED_PROCESS：DETACHED 下
# 服务自身没有控制台，venv 启动器（Scripts\python.exe）再拉真身解释器时
# 不透传这个标志，真身发现自己没台可继承就自建一个新控制台——黑窗从合成
# 开工一直挂到收工。隐藏控制台则全链路都有台可继承，谁也弹不出来。
flags = 0
if os.name == "nt":
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
proc = subprocess.Popen([py, serve, "--host", host, "--port", str(port)],
                        cwd=svc, stdout=fh, stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL, creationflags=flags)
```

孤儿一侧，服务进程起来后立刻挂进 Job 对象，设 `KILL_ON_JOB_CLOSE`：

```text
# podcast_maker/tts_engine.py:385 —— Job 对象绑定
_JOB_KILL_ON_CLOSE = 0x2000      # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
_JOB_EXTENDED_LIMIT_INFO = 9     # JobObjectExtendedLimitInformation

def _job_assign(proc, log=None):
    """Windows：把服务进程挂进一个随主进程存亡的 Job 对象。
    服务是独立进程（自己的隐藏控制台，没有 Job 绑定时父进程死了它照活），
    主程序若被强杀（关窗、崩溃、任务管理器），它会带着已加载的权重变孤儿，
    几个 G 显存一直占着。挂进 Job 并设 KILL_ON_JOB_CLOSE 后，内核在收走
    主进程时自动关闭 Job 句柄，一并终止 Job 里整棵进程树（venv 启动器拉起
    的真身解释器自动继承成员资格）——显存必还，不留孤儿。"""
    k32 = ctypes.windll.kernel32
    job = k32.CreateJobObjectW(None, None)
    info.BasicLimitInformation.LimitFlags = _JOB_KILL_ON_CLOSE
    k32.SetInformationJobObject(job, _JOB_EXTENDED_LIMIT_INFO,
                                ctypes.byref(info), ctypes.sizeof(info))
    ph = k32.OpenProcess(0x0100 | 0x0001, False, proc.pid)
    k32.AssignProcessToJobObject(job, ctypes.c_void_p(int(ph)))
    return job   # 句柄关闭交给 _job_close
```

挂 Job 之前，`_job_assign` 先把 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` 写进 `EXTENDED_LIMIT_INFORMATION` 结构的 `BasicLimitInformation.LimitFlags`，再交给 `SetInformationJobObject`——这段 ctypes 结构（`IO_COUNTERS` / `BASIC_LIMIT` / `EXT_LIMIT`）就是 Windows 要求的入参形状，缺了它内核不认这个标志：

```text
# podcast_maker/tts_engine.py:410-431 —— Job 扩展限额结构（ctypes）
class EXT_LIMIT(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", BASIC_LIMIT),   # 内含 LimitFlags
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]
# :445  info.BasicLimitInformation.LimitFlags = _JOB_KILL_ON_CLOSE
# :458  AssignProcessToJobObject(job, ph)  # 服务进程挂进 Job
```

句柄的关闭由 `_job_close` 独立负责，正常收工是「先 `_kill(proc)` 再关句柄」双保险；异常路径下句柄随主进程被内核收走，同样触发 `KILL_ON_JOB_CLOSE`：

```text
# podcast_maker/tts_engine.py:466-472 —— Job 句柄关闭（双保险）
def _job_close(job):
    """关掉 Job 句柄。KILL_ON_JOB_CLOSE 生效时，句柄一关内核清掉整棵进程树。
    正常收工路径先 _kill(proc) 再关句柄，双保险；句柄无效或非 Windows 什么都不做。"""
    if job and os.name == "nt":
        ctypes.windll.kernel32.CloseHandle(job)
```

服务进程本身由 `venv_python()` 拉起（:480）——这正是一、四节说的 venv 启动器中间层：主程序调 `_spawn_service`，它取 venv 解释器路径再去 `Popen` 真身服务，三层进程（主程序 → venv 启动器 → 真身解释器 → 语音服务）整条挂进同一个 Job，谁都不漏。

挂柄时还有两个细节值得记：`_job_assign` 优先取 `Popen` 在 Windows 上存好的原始进程柄 `proc._handle`（:451），免得再去 `OpenProcess`——后者要 `SET_QUOTA|TERMINATE` 权限才能挂 Job；若 `AssignProcessToJobObject` 失败，则先 `CloseHandle(job)` 再返回 `None`（:458-460），绝不留下一个半绑定的 Job 句柄。

两处都做了退化保护：非 Windows 平台 `_job_assign` 返回 `None`，行为退回从前，只少这层保险，不挡合成；内核调用失败同样返回 `None`，不抛异常。`KILL_ON_JOB_CLOSE` 是 Job 的限制标志，Job 句柄一关闭，内核即杀掉 Job 内所有进程——这正是它比「父进程退出回调」硬的地方：主程序被强杀时没机会跑任何代码，内核照样收树。

**形态 C · 起服务移出业务锁**：`acquire_service`（:566）改用 `starting` 状态位 + 条件变量（`_SERVICE_LOCK` :264、`_SERVICE_CV` :268、`_SERVICE["starting"]` :270）：起服务移到锁外，只放一个线程去起，其余在「启动中」上等待；`release_service` 在启动完成后才裁决是否停机，避免「刚起好、引用计数已归零、无人停」的泄漏 [6]。

```text
# podcast_maker/tts_engine.py:566 —— acquire_service 起服务移出锁
# 旧：_spawn_service(含 90s _wait_ready) 整个包在 _SERVICE_LOCK 内，
#     读锁入口一并等待 → 整页卡死。
# 新：starting 状态位 + 条件变量；只放一个线程去起，其余在「启动中」上等。
with _SERVICE_LOCK:
    if _SERVICE["starting"]:
        while _SERVICE["starting"]:
            _SERVICE_CV.wait()          # 已在起，排队等，不抢锁
        return _SERVICE["handle"]
    _SERVICE["starting"] = True
# —— 锁外起服务 ——
handle = _spawn_service(cfg, log)        # 90s _wait_ready 不占读锁
...
```

**形态 D · 标定与音色工具补腾显存**：`unload_llm_models()`（:193）接入 `api_voice_calibrate`（合成前，:1169）；新增 `web_ui._prep_voice_tool`（:1518），把腾显存与 `--device cuda` 一并加进四处音色工具 spawn；`tts_engine.ensure_voice_profiles`（:867）子进程命令行同步补 `--device cuda` [7]。同时把「生成设备」烙进校准表与标尺记录：`duration_model.calibrate`（:365）增 `device` / `backend` 两参随系数落盘，`Calibration._normalize`（:160）/`summary`（:185）在有值时带出；`tts_engine.running_device`（:141）向 `/health` 取设备、只认 `cuda` / `cpu` 两个真值 [8]。换设备即丢弃旧样本、本次直接起算，EMA 不混、L2 不并 [8]。

## 六、验证：四条测试钉

`tests/test_tts_engine.py` 在 v1.3.0 增设 Job 绑定 4 项钉，把上面的保证变成可回归的判据：

- `test_service_slot_has_job`（:734）：服务状态槽必须有 `job` 位、且初始为空——挂载前的契约，防「忘了挂 Job 却以为挂了」。
- `test_job_close_none_is_noop`（:738）：关 `None` 句柄不抛即过——退化路径（非 Windows / 挂载失败返回 None）不挡合成。
- `test_kill_on_job_close_reaps_child`（:741）：**核心保证**——句柄一关，内核杀掉 Job 里的子进程，不留孤儿。复现逻辑：以 `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` 起一个 `time.sleep(30)` 的子进程，挂进 Job，随后关句柄；8 秒内轮询断言 `proc.poll()` 返回非 `None`（进程已死）。它验证的不是「能杀」，而是「父程序已没机会跑代码时，内核仍收树」——这才是孤儿问题的真正抓手。
- `test_job_assign_dead_process_returns_none`（:765）：死进程（已 `wait` 结束）挂不进 Job 时返回 `None` 而非抛异常——挂载失败不挡合成，也不漏杀。

实验设计可复现：拉起服务 → 记录 pid 与显存占用 → 强杀主程序 → 观测服务进程是否还在、显存是否归还。判定「服务进程树消失 + 显存归零」为 PASS。v1.3.0 该批测试随全仓 **1311 项**单测一并通过。

**起服务锁与设备落表（v2.10.0）**：

- `tests/test_tts_engine.py::TestRunningDevice`（:131）4 条：真实设备与后端、占位「未加载」返回空、服务离线返回空、探测异常返回空 [8]。
- `tests/test_duration_model.py::TestCalibrateDevice`（:147）6 条：设备与后端随系数落盘、同设备样本累加、换设备丢弃旧样本、本次缺设备沿用上一条、`summary` 带出设备与后端、旧数据不凭空出现该键 [8]。
- `tests/test_preview_standard.py::TestVoiceToolPrep`（:587）3 条：腾显存后加 `--device cuda`、已带该参数则不重复加、四处音色工具 spawn 全部经过该函数；`TestVoiceCalibrate`（:679）本地引擎 1 条：先腾显存、设备与后端随系数落表 [7]。
- 腾显存与设备落表落地后复跑全量 **1596** 通过（skipped=1）[7]。

## 七、结语：一句话收束

本地 TTS 的显存越占越多，不是模型漏了释放调用，而是 Windows 进程默认「父死子不亡」、控制台默认「要弹就弹」——用 Job 对象把回收权交给内核、用 CREATE_NO_WINDOW 把控制台藏进继承链，两类副作用一次归零，且非 Windows 安静退化、不挡合成。

顺带一提，这次修法没有动服务的拉起与释放时机——仍是首次合成开工才 spawn、batch 收工 `release_service` 照常停服还显存；Job 只是主程序死亡时的内核保险，正常路径该谁关谁关，不抢戏、不耦合。

v2.10.0 又补两处：起服务移出业务锁，不让 90 秒等待串行化整页读锁；标定与音色工具补腾显存并烙设备身份，让标定与成片、`ref_base` 始终同源同波形——显存管理从「进程级回收」进一步收到「每次本地推理前的设备归位」。

## 引用与出处说明

| 编号 | 论点 | 出处 |
|---|---|---|
| [1] | 黑窗根因：DETACHED 不透传、真身自建控制台；CREATE_NO_WINDOW 全链路继承 | `podcast_maker/tts_engine.py:496-499` |
| [2] | 孤儿根因：独立进程无「父死子亡」语义，显存随进程存活 | `podcast_maker/tts_engine.py:392-396`（`_job_assign` 文档） |
| [3] | Job 绑定实现：`_JOB_KILL_ON_CLOSE` / `_job_assign` / `AssignProcessToJobObject` | `podcast_maker/tts_engine.py:385-462` |
| [4] | 启动服务 flags：`CREATE_NEW_PROCESS_GROUP \| CREATE_NO_WINDOW` | `podcast_maker/tts_engine.py:495-511` |
| [5] | 测试钉：Job 绑定 4 项（v1.3.0 增设）+ 全仓 1311 项通过 | `podcast-maker · CHANGELOG.md · v1.3.0 · 测试段`；`tests/test_tts_engine.py:734-773` |

| [6] | 起服务锁死整页：acquire_service 把 _spawn_service(含 90s _wait_ready) 包在 _SERVICE_LOCK 内，读锁入口陪等；改为 starting 状态位 + 条件变量，起服务移出锁 | podcast-maker · CHANGELOG.md · v2.10.0 · 条目「一次起服务锁死整页状态接口」<br>`podcast_maker/tts_engine.py:acquire_service`(:566)/`_SERVICE_LOCK`(:264) |
| [7] | 标定与音色工具未腾显存：unload_llm_models 只接 synthesize；子进程设备判定退 CPU、CPU/CUDA 波形不同源；修复接入 api_voice_calibrate + web_ui._prep_voice_tool + ensure_voice_profiles --device cuda；全量 1596 通过 | podcast-maker · CHANGELOG.md · v2.10.0 · 条目「标定与音色工具未腾显存，参考音频可能在 CPU 上生成」<br>`podcast_maker/tts_engine.py:unload_llm_models`(:193)；`podcast_maker/web_ui.py:_prep_voice_tool`(:1518) |
| [8] | 校准表 / 标尺记录生成设备落表：duration_model.calibrate 增 device/backend 随系数落盘、换设备丢弃旧样本；tts_engine.running_device 向 /health 取设备；全量 1596 通过 | podcast-maker · CHANGELOG.md · v2.10.0 · 条目「校准表与标尺记录生成设备，换档即失效」<br>`podcast_maker/duration_model.py:calibrate`(:365)；`podcast_maker/tts_engine.py:running_device`(:141) |

## 延伸阅读

- `tests/test_tts_engine.py`：Job 绑定四条测试即用本文结论作判据，与本文互为印证。
- `podcast_maker/tts_engine.py` 服务拉起与 `_job_close`：句柄生命周期与退化路径的完整实现。

---

*最后更新：2026-10-10（论证：黑窗/孤儿两类失败形态 → 旧凑法 DETACHED/手动 kill 各自踏空 → Windows 控制台继承与进程无父死子亡语义两根因 → Job 绑定 + CREATE_NO_WINDOW 双修法 → 4 项测试钉；v2.10.0 增起服务移出业务锁、标定与音色工具补腾显存并烙设备身份；文献佐证 8 条均取自真实代码与 CHANGELOG；四检：真实性 PASS / 底层逻辑 PASS / 空推论 PASS / 循环论证 PASS）*
