# -*- coding: utf-8 -*-
"""
《我写故我播》书稿拼接脚本（系根类骨架：前置件 3 + 部导读 8 + 正文 47 + 结语 1 + 附录 7 = 66 章）
将版权页/序言/阅读指南 + 八部导读 + 47 篇正文（按篇号部序）+ 结语 + 七附录拼接为单一书稿 Markdown；未写篇生成占位章，产出后自动替换。
用法: python assemble.py [输出路径]
零依赖（标准库）。入书规范参考族系规范之家 `typesetting/`：STRUCTURE_GUIDE.md（族系转化规范）与 BOOK_GUIDE.md（成书规范）。

入书清洗（STRUCTURE_GUIDE 去留规则的管线级硬约束）：
- 剥 SPDX 头（strip_spdx）
- 剥章头「摘要 + 更新行/生成时间」blockquote（成书无摘要/日期戳；连带其紧随分隔线）
- 剥篇尾「*最后更新：…*」脚注（成书无版本戳；连带其前一条结构线——脚注不在，为其而设的结构线不留）
- 章题统一为《我思故我写》族系格式 `第 X 部 · NN｜原标题`——**只加前缀，不重写原标题**
  （源稿 H1 即书内章题：本册单篇入书，公众号与入书同源，不存在第二套标题）
- 章间不注入分隔线（h1 已强制每章新页）
本册（源自排版册移植）无章尾编制说明戳记与正文节间分隔线，故不设对应清洗函数（架构册差异见 STRUCTURE_GUIDE §八.1）。
"""
import sys, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # book/build -> book -> 项目根

# 书的结构（顺序即书的顺序：前置件 → 八部（各部导读+篇号正序）→ 结语 → 附录）
# 元组第三项 = 成书章题前缀（None = 保留源 H1，用于版权页/序言/阅读指南/部导读/附录/结语）
STRUCTURE = [
    ("book/frontmatter/00_版权页.md", "版权页", None),
    ("book/frontmatter/00_序言.md", "序言", None),
    ("book/frontmatter/00_阅读指南.md", "阅读指南", None),
    ("articles/00_部一_导读.md", "第 I 部 导读", None),
    ("articles/1_九步管线.md", "第 I 部 · 01", "第 I 部 · 01｜一个播客智能体的九步管线：脚本→声音→字幕→画面→产物"),
    ("articles/2_配置总表驱动.md", "第 I 部 · 02", "第 I 部 · 02｜配置总表如何同时驱动界面与管线：PARAM_SPEC 一处定义"),
    ("articles/3_存量配置自动搬迁.md", "第 I 部 · 03", "第 I 部 · 03｜存量配置自动搬迁：白名单过滤之前必须先改名"),
    ("articles/4_MODE_SPEC双语义.md", "第 I 部 · 04", "第 I 部 · 04｜一套配置管两种字幕模式：MODE_SPEC 接驳表的双语义"),
    ("articles/00_部二_导读.md", "第 II 部 导读", None),
    ("articles/5_约束解码不是万能.md", "第 II 部 · 05", "第 II 部 · 05｜约束解码不是万能的：schema 漏字段让承诺链永远红"),
    ("articles/6_检查段修补空补丁.md", "第 II 部 · 06", "第 II 部 · 06｜检查段修补为什么返回空补丁：PATCH_SCHEMA 三层加固"),
    ("articles/7_定点修补漏接词表.md", "第 II 部 · 07", "第 II 部 · 07｜定点修补漏接词表：约束解码在嵌套数组里的盲区"),
    ("articles/8_引语门禁.md", "第 II 部 · 08", "第 II 部 · 08｜引语标注无硬校验：一个 fail 级门禁怎么落地"),
    ("articles/9_首轮复读绕过查重.md", "第 II 部 · 09", "第 II 部 · 09｜首轮复读绕过查重：一个 else 分支吞掉整段工序"),
    ("articles/10_文体块分卡.md", "第 II 部 · 10", "第 II 部 · 10｜文体块分卡：八张素材卡怎么各自说话"),
    ("articles/11_字距规范化.md", "第 II 部 · 11", "第 II 部 · 11｜字距规范化：为什么落盘会删掉汉字与西文之间的空格"),
    ("articles/12_排图与压比.md", "第 II 部 · 12", "第 II 部 · 12｜排图与压比：期数为什么不能交给模型自由发挥"),
    ("articles/00_部三_导读.md", "第 III 部 导读", None),
    ("articles/13_本地TTS显存管理.md", "第 III 部 · 13", "第 III 部 · 13｜本地 TTS 显存管理：从黑窗、孤儿进程到 Job 对象"),
    ("articles/14_音色漂移检测.md", "第 III 部 · 14", "第 III 部 · 14｜音色漂移检测：从三维合验到五族合验"),
    ("articles/15_种子确定性派生.md", "第 III 部 · 15", "第 III 部 · 15｜种子确定性派生的双刃剑：坏句重跑不变怎么破"),
    ("articles/16_VoiceDesign草稿流.md", "第 III 部 · 16", "第 III 部 · 16｜VoiceDesign 造嗓草稿流：为什么先落草稿再入库"),
    ("articles/17_入库响度归一.md", "第 III 部 · 17", "第 III 部 · 17｜音频入库即响度归一：11.7 dB 极差收敛到 -23±0.22 dBFS"),
    ("articles/18_stdout纪律.md", "第 III 部 · 18", "第 III 部 · 18｜stdout 纪律：结果通道为什么只能有一行 JSON"),
    ("articles/19_声门三件套与傅里叶域分段.md", "第 III 部 · 19", "第 III 部 · 19｜声门三件套与傅里叶域分段：第 9 维的原理、公式与实测"),
    ("articles/20_ref_base版本账本.md", "第 III 部 · 20", "第 III 部 · 20｜ref_base 版本账本：换嗓串嗓事故的 sign 后缀与角色账本"),
    ("articles/00_部四_导读.md", "第 IV 部 导读", None),
    ("articles/21_BGM听不见.md", "第 IV 部 · 21", "第 IV 部 · 21｜BGM 听不见：素材 13.6 LU 参差 + 混音压低三十多分贝"),
    ("articles/22_本地BGM生成.md", "第 IV 部 · 22", "第 IV 部 · 22｜本地 BGM 生成：从二十分钟搭建到 10 秒出曲"),
    ("articles/23_清场误删成品.md", "第 IV 部 · 23", "第 IV 部 · 23｜成品被自己的清场删掉：finally 顺序的一次误杀"),
    ("articles/24_人声闪避混合试听.md", "第 IV 部 · 24", "第 IV 部 · 24｜人声闪避与混合试听：预览为什么走成片同一条管线"),
    ("articles/25_环境音决策层.md", "第 IV 部 · 25", "第 IV 部 · 25｜环境音决策层：LLM 只从封闭清单点名，五道防线 fail-closed 兜底"),
    ("articles/26_环境音执行层.md", "第 IV 部 · 26", "第 IV 部 · 26｜环境音执行层：mp3 过 concat demuxer 出坏流，句前 +0.00s 事故"),
    ("articles/27_BGM转译层.md", "第 IV 部 · 27", "第 IV 部 · 27｜BGM 转译层：中文描述怎么经 LLM 变成英文 caption，又怎么被 CoT 劫持"),
    ("articles/28_BGM三层结构转译契约.md", "第 IV 部 · 28", "第 IV 部 · 28｜BGM 三层结构转译契约：caption/lyrics/bpm·keyscale·timesignature 与中频塌陷 drone 墙"),
    ("articles/29_AI生成件响度归一.md", "第 IV 部 · 29", "第 IV 部 · 29｜AI 生成件响度归一：bgm_loudness 与峰均比超 22.5dB 的 allow_limited 放行"),
    ("articles/00_部五_导读.md", "第 V 部 导读", None),
    ("articles/30_字幕四份同源.md", "第 V 部 · 30", "第 V 部 · 30｜字幕四份同源：为什么我不从产物反解"),
    ("articles/31_三份字幕同源.md", "第 V 部 · 31", "第 V 部 · 31｜一期三份字幕同源生成：SRT/LRC/TXT 逐字节一致"),
    ("articles/32_单行字幕横滚.md", "第 V 部 · 32", "第 V 部 · 32｜单行字幕横滚：旧单行档把 104 字裁成 33 字"),
    ("articles/33_字幕断词.md", "第 V 部 · 33", "第 V 部 · 33｜字幕断词：一个 return hi 兜底硬切在词中间"),
    ("articles/34_ASS配色陷阱.md", "第 V 部 · 34", "第 V 部 · 34｜ASS 配色陷阱：\\&HAABBGGRR 直接喂 CSS 为什么变黑"),
    ("articles/35_静态层预烘焙.md", "第 V 部 · 35", "第 V 部 · 35｜静态层预烘焙：一期视频从 17.8 分钟到 4.8 分钟"),
    ("articles/00_部六_导读.md", "第 VI 部 导读", None),
    ("articles/36_进度条永远卡在0与100.md", "第 VI 部 · 36", "第 VI 部 · 36｜一个进度条为什么永远卡在 0% 和 100%？"),
    ("articles/37_开窗时序.md", "第 VI 部 · 37", "第 VI 部 · 37｜启动后浏览器先显示「连接不上」：开窗时序问题"),
    ("articles/38_配置页网格重排.md", "第 VI 部 · 38", "第 VI 部 · 38｜配置页网格重排：只改界面，不动配置项"),
    ("articles/39_GBK乱码toast.md", "第 VI 部 · 39", "第 VI 部 · 39｜GBK 乱码进 toast：PYTHONIOENCODING 为什么必须注入"),
    ("articles/40_配置项显隐.md", "第 VI 部 · 40", "第 VI 部 · 40｜配置项显隐：show_if 与 applyShowIf 怎么让界面跟着配置变"),
    ("articles/41_空壳下拉回落未选择.md", "第 VI 部 · 41", "第 VI 部 · 41｜空壳下拉切页回落成「未选择」：valOf 对一个无 option 的 SELECT 返回了什么"),
    ("articles/00_部七_导读.md", "第 VII 部 导读", None),
    ("articles/42_AIGC合规标识.md", "第 VII 部 · 42", "第 VII 部 · 42｜AIGC 合规标识落地：元数据、语音声明、字幕偏移"),
    ("articles/43_更新日志写成技术文.md", "第 VII 部 · 43", "第 VII 部 · 43｜更新日志写成技术文章：现象、根因、修法、验证"),
    ("articles/44_测试钉子.md", "第 VII 部 · 44", "第 VII 部 · 44｜测试钉子：如何防止修好的 bug 长回来"),
    ("articles/00_部八_导读.md", "第 VIII 部 导读", None),
    ("articles/45_工程如何落地.md", "第 VIII 部 · 45", "第 VIII 部 · 45｜工程如何落地：画地图定位、功能解耦、分层与统一各级推动点位"),
    ("articles/46_方法论复用.md", "第 VIII 部 · 46", "第 VIII 部 · 46｜《我思故我写》方法论在播客现场的复用：前置规范、统一推动点位、名词不解释、槽位减法"),
    ("articles/47_文明退化语义丢失.md", "第 VIII 部 · 47", "第 VIII 部 · 47｜文明退化从丢失语义开始：当 LLM 成了人际交流的中间翻译"),
    ("book/99_结语.md", "结语", None),
    # 附录位次（族系"同名同位"）：A/B/C 与《我思故我写》逐位一致，异名项顺延
    ("book/appendix/术语表.md", "附录 A 术语表", None),
    ("book/appendix/工具索引.md", "附录 B 工具索引", None),
    ("book/appendix/参考文献.md", "附录 C 参考文献", None),
    ("book/appendix/实测数字速查.md", "附录 D 实测数字速查", None),
    ("book/appendix/CHANGELOG锚点索引.md", "附录 E CHANGELOG 锚点索引", None),
    ("book/appendix/模型底座.md", "附录 F 模型底座", None),
    ("book/appendix/提示词逻辑体系.md", "附录 G 提示词逻辑体系", None),
]

def strip_spdx(text):
    """剥离 SPDX 头（HTML 注释块），保留正文"""
    return re.sub(r'<!--.*?-->', '', text, flags=re.S).lstrip('\n')

# 写作痕迹判据：篇尾版本戳 / 章头日期戳行 / 章头摘要块
_FOOTNOTE_RE = re.compile(r'^\*最后更新：.*\*\s*$', re.M)
_STAMP_RE = re.compile(r'^\s*>\s*(更新：|生成时间：)', re.M)
# 摘要块判据：本册摘要写作 "> 摘要：…" 且无日期戳行，上面的 _STAMP_RE 不命中
# → 单独锚定块首行（导读/附录的开篇 blockquote 不以"摘要"起头，不受影响）
_SUMMARY_RE = re.compile(r'^>\s*摘要[：:]')

def strip_writing_traces(body):
    """剥离写作痕迹：章头「摘要+更新行/生成时间」blockquote 与篇尾「最后更新」脚注。
    判据锚定：① 章 H1 后紧跟的 blockquote 含日期戳行（更新：/生成时间：）；
    ② 或该 blockquote 首行以 `> 摘要` 起头（成书无摘要，对齐《我思故我写》）——
    两者满足其一即整块剥离。导读/附录的开篇 blockquote 两者都不命中，不受影响。"""
    lines = body.split('\n')
    h1_idx = next((i for i, l in enumerate(lines) if l.startswith('# ')), None)
    if h1_idx is not None:
        j = h1_idx + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].lstrip().startswith('>'):
            k = j
            while k < len(lines) and (lines[k].lstrip().startswith('>') or not lines[k].strip()):
                k += 1
            hit = (_STAMP_RE.search('\n'.join(lines[j:k]))
                   or _SUMMARY_RE.match(lines[j].lstrip()))
            if hit:
                # 连带剥掉紧随的分隔线（摘要的 ---，非正文内容）
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and lines[k].strip() == '---':
                    k += 1
                rest = lines[k:]
                while rest and not rest[0].strip():
                    rest.pop(0)
                lines = lines[:h1_idx + 1] + [''] + rest
    res = []
    for l in lines:
        if _FOOTNOTE_RE.match(l):
            # 脚注连带其前一条结构线一起去（成书无版本戳；结构线为脚注而设，脚注不在则不留）
            for j in range(len(res) - 1, -1, -1):
                if not res[j].strip():
                    continue
                if res[j].strip() == '---':
                    del res[j]
                break
            continue
        res.append(l)
    return '\n'.join(res)

def retitle(body, title):
    """章题对齐（族系转化规则 1.1）：`{部前缀}｜{原标题}`。
    只换部前缀，**不重写原标题**——源稿 H1 即书内章题（本册单篇入书，
    公众号与入书同源，不存在第二套标题）。
    注意：源稿 H1 本身就是 `第X部 · NN｜标题` 形态（前缀由写作期给定），
    故须先剥掉源前缀（`｜` 之前的部分）再拼新前缀，否则会叠成双前缀。"""
    lines = body.split('\n')
    prefix = title.split('｜')[0].strip()
    for i, l in enumerate(lines):
        if l.startswith('# '):
            src = l[2:].strip()
            if '｜' in src:
                src = src.split('｜', 1)[1].strip()
            lines[i] = '# %s｜%s' % (prefix, src) if src else '# %s' % prefix
            break
    return '\n'.join(lines)

def assemble():
    parts = []
    missing = []
    for rel, _label, title in STRUCTURE:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            # 未写篇：生成占位章（成书时 articles/{slug}.md 产出后由 assemble 自动替换）
            _t = title or rel
            parts.append('# ' + _t + '\n\n> 本篇待写（占位章）。成书时将由定时任务产出 `' + rel + '` 后由 assemble 自动替换为正文；本章不计入字数统计。')
            missing.append(rel)
            continue
        with io.open(path, encoding='utf-8') as f:
            text = f.read()
        body = strip_writing_traces(strip_spdx(text)).strip()
        if title:
            body = retitle(body, title)
        parts.append(body)
    # 章间不注入 '---'：h1 已强制每章新页（break-before: page）
    print('[assemble] 全书 %d 段，其中 %d 段为占位（缺文件）：' % (len(STRUCTURE), len(missing)))
    for m in missing:
        print('  - 占位: ' + m)
    return '\n\n'.join(parts)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'book', 'build', 'output', '我写故我播全书.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    book = assemble()
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(book)
    print('书稿已拼接: %s（%s 字符，%d 个部分）' % (out, format(len(book), ','), len(STRUCTURE)))

if __name__ == '__main__':
    main()
