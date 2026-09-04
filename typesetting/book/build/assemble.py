# -*- coding: utf-8 -*-
"""
《我思故我写 · 排版解析》书稿拼接脚本
将导读 + 6 篇排版文章拼接为单一书稿 Markdown。
用法: python assemble.py [输出路径]
零依赖（标准库）。入书规范参考 Cogito_Scribit STRUCTURE_GUIDE。

入书清洗（STRUCTURE_GUIDE 去留规则的管线级硬约束，typ-v1.1.0）：
- 剥 SPDX 头（strip_spdx）
- 剥章头「摘要 + 更新行/生成时间」blockquote（成书无摘要/日期戳）
- 剥篇尾「*最后更新：…*」脚注（成书无版本戳）
- 章题统一为母书族系格式 `NN｜标题`（母书为 `第 X 部 · NN｜标题`，姊妹卷无部）
"""
import sys, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 书的结构（顺序即书的顺序；排版 01~05 五层按流水线排序，排版 06 为收束篇殿后）
# 元组第三项 = 成书章题（None = 保留源 H1，用于版权页/导读/附录）
STRUCTURE = [
    ("frontmatter/00_版权页.md", "版权页", None),
    ("frontmatter/00_导读.md", "导读", None),
    ("articles/成书排版（一）：先定样式，再写正文.md", "排版 01 · 先定样式，再写正文", "01｜成书排版：先定样式，再写正文"),
    ("articles/成书排版（二）：单篇入书，元素去留.md", "排版 02 · 单篇入书，元素去留", "02｜成书排版：单篇入书，元素去留"),
    ("articles/成书排版（三）：骨架排版——四部、导读与章序.md", "排版 03 · 骨架排版", "03｜成书排版：骨架排版——四部、导读与章序"),
    ("articles/成书排版（四）：页面排版——从屏幕到纸面.md", "排版 04 · 页面排版", "04｜成书排版：页面排版——从屏幕到纸面"),
    ("articles/成书排版（五）：元数据排版——字数、章数与版本号.md", "排版 05 · 元数据排版", "05｜成书排版：元数据排版——字数、章数与版本号"),
    ("articles/AI任务执行的完整流程——明确位置、对齐粒度、穷举正反例.md", "排版 06 · AI 任务执行的完整流程", "06｜AI 任务执行的完整流程——明确位置、对齐粒度、穷举正反例"),
    ("appendix/统一术语表.md", "附录 A 统一术语表", None),
    ("appendix/排版速查.md", "附录 B 排版速查", None),
]

def strip_spdx(text):
    """剥离 SPDX 头（HTML 注释块），保留正文"""
    return re.sub(r'<!--.*?-->', '', text, flags=re.S).lstrip('\n')

# 写作痕迹判据：篇尾版本戳 / 章头日期戳行
_FOOTNOTE_RE = re.compile(r'^\*最后更新：.*\*\s*$', re.M)
_STAMP_RE = re.compile(r'^\s*>\s*(更新：|生成时间：)', re.M)

def strip_writing_traces(body):
    """剥离写作痕迹：章头「摘要+更新行/生成时间」blockquote 与篇尾「最后更新」脚注。
    判据锚定：仅当章 H1 后紧跟的 blockquote 含日期戳行（更新：/生成时间：）才整块剥离——
    导读/附录的开篇 blockquote 无日期戳行，不受影响。"""
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
            if _STAMP_RE.search('\n'.join(lines[j:k])):
                # 连带剥掉紧随的分隔线（摘要的 ---，非正文内容）
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and lines[k].strip() == '---':
                    k += 1
                rest = lines[k:]
                while rest and not rest[0].strip():
                    rest.pop(0)
                lines = lines[:h1_idx + 1] + [''] + rest
    lines = [l for l in lines if not _FOOTNOTE_RE.match(l)]
    return '\n'.join(lines)

def retitle(body, title):
    """章题对齐：替换首个 H1 为成书章题"""
    lines = body.split('\n')
    for i, l in enumerate(lines):
        if l.startswith('# '):
            lines[i] = f'# {title}'
            break
    return '\n'.join(lines)

def assemble():
    parts = []
    for rel, _label, title in STRUCTURE:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            # 正文在 typesetting/articles/（ROOT 上一级）
            path = os.path.join(ROOT, '..', rel)
        with io.open(path, encoding='utf-8') as f:
            text = f.read()
        body = strip_writing_traces(strip_spdx(text)).strip()
        if title:
            body = retitle(body, title)
        parts.append(body)
    # 章间不注入 '---'：h1 已强制每章新页（break-before: page）
    return '\n\n'.join(parts)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'output', '排版解析全书.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    book = assemble()
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(book)
    print(f'书稿已拼接: {out}（{len(book):,} 字符，{len(STRUCTURE)} 个部分）')

if __name__ == '__main__':
    main()
