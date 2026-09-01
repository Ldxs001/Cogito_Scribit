# -*- coding: utf-8 -*-
"""
《我思故我写 · 排版解析》书稿拼接脚本
将导读 + 5 篇排版文章拼接为单一书稿 Markdown。
用法: python assemble.py [输出路径]
零依赖（标准库）。入书规范参考 Cogito_Scribit STRUCTURE_GUIDE。
"""
import sys, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 书的结构（顺序即书的顺序；五层排版按流水线排序）
# 路径基准：ROOT = typesetting/book；frontmatter 在 ROOT 内，正文在 ROOT 上级（typesetting/articles/，走 fallback）
STRUCTURE = [
    ("frontmatter/00_版权页.md", "版权页"),
    ("frontmatter/00_导读.md", "导读"),
    ("articles/成书排版（一）：先定样式，再写正文.md", "排版 01 · 先定样式，再写正文"),
    ("articles/成书排版（二）：单篇入书，元素去留.md", "排版 02 · 单篇入书，元素去留"),
    ("articles/成书排版（三）：骨架排版——四部、导读与章序.md", "排版 03 · 骨架排版"),
    ("articles/成书排版（四）：页面排版——从屏幕到纸面.md", "排版 04 · 页面排版"),
    ("articles/成书排版（五）：元数据排版——字数、章数与版本号.md", "排版 05 · 元数据排版"),
    ("frontmatter/附录A_统一术语表.md", "附录 A 统一术语表"),
    ("frontmatter/附录B_排版速查.md", "附录 B 排版速查"),
]

def strip_spdx(text):
    """剥离 SPDX 头（HTML 注释块），保留正文"""
    return re.sub(r'<!--.*?-->', '', text, flags=re.S).lstrip('\n')

def assemble():
    parts = []
    for rel, _label in STRUCTURE:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            # 正文在 typesetting/articles/（ROOT 上一级）
            path = os.path.join(ROOT, '..', rel)
        with io.open(path, encoding='utf-8') as f:
            text = f.read()
        body = strip_spdx(text).strip()
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
