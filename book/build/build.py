# -*- coding: utf-8 -*-
"""
《我思故我写》构建主入口
用法: python build.py
流程: assemble → 全书.md → HTML(预览) + EPUB(发布)
输出: build/output/
"""
import os, sys, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assemble import assemble
from md2html import convert
from build_epub import build_epub

def main():
    out_dir = os.path.join(ROOT, 'build', 'output')
    os.makedirs(out_dir, exist_ok=True)

    # 1. 拼接全书
    book = assemble()
    md_path = os.path.join(out_dir, '全书.md')
    with io.open(md_path, 'w', encoding='utf-8') as f:
        f.write(book)
    print(f'[1/3] 拼接完成: {md_path}（{len(book):,} 字符）')

    # 2. HTML 预览
    html_path = os.path.join(out_dir, '我思故我写.html')
    html_doc = convert(book, '我思故我写——一本 AI 写成的书')
    with io.open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f'[2/3] HTML 预览: {html_path}')

    # 3. EPUB
    epub_path = os.path.join(out_dir, '我思故我写.epub')
    build_epub(md_path, epub_path)
    print(f'[3/3] 构建完成。输出目录: {out_dir}')

if __name__ == '__main__':
    main()
