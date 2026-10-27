# -*- coding: utf-8 -*-
"""
《我写故我播》构建主入口
用法: python build.py
流程: assemble → 我写故我播全书.md → HTML(预览) + EPUB(发布)
输出: book/build/output/
"""
import os, sys, io, shutil

BOOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # book
PROJ_ROOT = os.path.dirname(BOOK_ROOT)                                   # podcast-maker-book
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assemble import assemble
from md2html import convert
from build_epub import build_epub

BOOK_TITLE = '我写故我播——一本 AI 犯过错的书：边界的实测、缺陷的坐标与因地制宜的裁量'
ASSETS_SRC = os.path.join(PROJ_ROOT, 'articles', 'assets')

def main():
    out_dir = os.path.join(BOOK_ROOT, 'build', 'output')
    os.makedirs(out_dir, exist_ok=True)

    # 0. 配图资产随产物落位（HTML/PDF 靠相对路径 assets/ 解析；EPUB 自行内嵌）
    if os.path.isdir(ASSETS_SRC):
        dst_assets = os.path.join(out_dir, 'assets')
        if os.path.isdir(dst_assets):
            shutil.rmtree(dst_assets)
        shutil.copytree(ASSETS_SRC, dst_assets)
        n = len(os.listdir(dst_assets))
        print(f'[0/3] 配图资产: {n} 个 → {dst_assets}')
    else:
        print(f'[0/3] 警告：未找到配图目录 {ASSETS_SRC}')

    # 1. 拼接全书
    book = assemble()
    md_path = os.path.join(out_dir, '我写故我播全书.md')
    with io.open(md_path, 'w', encoding='utf-8') as f:
        f.write(book)
    print(f'[1/3] 拼接完成: {md_path}（{len(book):,} 字符）')

    # 2. HTML 预览
    html_path = os.path.join(out_dir, 'book.html')
    html_doc = convert(book, BOOK_TITLE)
    with io.open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f'[2/3] HTML 预览: {html_path}')

    # 3. EPUB（图片自内嵌到 OEBPS/images/）
    epub_path = os.path.join(out_dir, 'book.epub')
    build_epub(md_path, epub_path, assets_dir=ASSETS_SRC)
    print(f'[3/3] 构建完成。输出目录: {out_dir}')

if __name__ == '__main__':
    main()
