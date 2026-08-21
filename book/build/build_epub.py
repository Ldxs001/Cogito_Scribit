# -*- coding: utf-8 -*-
"""
《我思故我写》零依赖 EPUB3 生成器
EPUB3 本质 = ZIP 包 + XHTML 内容 + OPF 元数据 + TOC。
用标准库 zipfile 手写，无需 ebooklib/pandoc。
用法: python build_epub.py [全书.md] [输出.epub]
"""
import sys, io, os, zipfile, uuid
from md2html import md_to_html

BOOK_TITLE = "我思故我写——一本 AI 写成的书：AI 时代的方法论、边界与人类自洽"
BOOK_AUTHOR = "wUwproject"
BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "cogito-liber-v1"))

EPUB_NS = {
    'container': 'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"',
    'opf': 'xmlns="http://www.idpf.org/2007/opf" version="3.0"',
    'xhtml': 'xmlns="http://www.w3.org/1999/xhtml"',
}

def split_sections(md_text):
    """按一级标题（# ）切分章节——每篇/组件一章"""
    lines = md_text.split('\n')
    sections = []
    cur_title, cur_body = None, []
    for line in lines:
        if line.startswith('# '):
            if cur_title:
                sections.append({'id': f'chap{len(sections)+1:03d}', 'title': cur_title, 'body': '\n'.join(cur_body)})
            cur_title = line[2:].strip()
            cur_body = [line]
        else:
            if cur_body is not None:
                cur_body.append(line)
    if cur_title:
        sections.append({'id': f'chap{len(sections)+1:03d}', 'title': cur_title, 'body': '\n'.join(cur_body)})
    if not sections:  # 兜底：无一级标题时按原逻辑
        raw = md_text.split('\n\n---\n\n')
        for i, part in enumerate(raw):
            title = '未命名'
            for line in part.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            sections.append({'id': f'chap{i+1:03d}', 'title': title, 'body': part})
    return sections

def make_xhtml(section):
    body = md_to_html(section['body'])
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html {EPUB_NS['xhtml']} lang="zh-CN" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/">
<head>
<meta charset="utf-8"/>
<title>{section['title']}</title>
<link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body}
</body>
</html>'''

def make_opf(sections):
    manifest = '\n'.join(
        f'    <item id="{s["id"]}" href="{s["id"]}.xhtml" media-type="application/xhtml+xml"/>'
        for s in sections)
    manifest += '\n    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    manifest += '\n    <item id="css" href="style.css" media-type="text/css"/>'
    spine = '\n'.join(f'    <itemref idref="{s["id"]}"/>' for s in sections)
    nav_points = '\n'.join(
        f'      <navPoint id="nav{s["id"]}" playOrder="{i+1}"><navLabel><text>{s["title"]}</text></navLabel><content src="{s["id"]}.xhtml"/></navPoint>'
        for i, s in enumerate(sections))
    return f'''<?xml version="1.0" encoding="utf-8"?>
<package {EPUB_NS['opf']} unique-identifier="BookId">
  <metadata {EPUB_NS['opf']}>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">{BOOK_TITLE}</dc:title>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{BOOK_AUTHOR}</dc:creator>
    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="BookId">{BOOK_ID}</dc:identifier>
    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">zh-CN</dc:language>
    <dc:rights xmlns:dc="http://purl.org/dc/elements/1.1/">CC BY-SA 4.0</dc:rights>
    <meta property="dcterms:modified">2026-08-12T00:00:00Z</meta>
  </metadata>
  <manifest>
{manifest}
  </manifest>
  <spine toc="ncx">
{spine}
  </spine>
</package>'''

def make_ncx(sections):
    points = '\n'.join(
        f'    <navPoint id="nav{s["id"]}" playOrder="{i+1}"><navLabel><text>{s["title"]}</text></navLabel><content src="{s["id"]}.xhtml"/></navPoint>'
        for i, s in enumerate(sections))
    return f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="{BOOK_ID}"/><meta name="dtb:depth" content="1"/></head>
  <docTitle><text>{BOOK_TITLE}</text></docTitle>
  <navMap>
{points}
  </navMap>
</ncx>'''

def make_container():
    return '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

EPUB_CSS = """
body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.8; }
h1 { font-size: 1.6em; margin-top: 1.5em; }
h2 { font-size: 1.3em; }
blockquote { border-left: 3px solid #999; margin: .8em 0; padding: .3em 1em; color: #666; }
table { border-collapse: collapse; width: 100%; margin: .8em 0; }
th, td { border: 1px solid #bbb; padding: .3em .5em; word-break: keep-all; vertical-align: top; }
table.ref-table { table-layout: fixed; }
table.ref-table th:nth-child(1), table.ref-table td:nth-child(1) { width: 8%; }
table.ref-table th:nth-child(2), table.ref-table td:nth-child(2) { width: 47%; }
table.ref-table th:nth-child(3), table.ref-table td:nth-child(3) { width: 45%; }
table.ref-table th, table.ref-table td { overflow-wrap: anywhere; }
table td .ref-piece, table th .ref-piece { display: block; white-space: normal;
  word-break: keep-all; overflow-wrap: break-word; line-height: 1.7; }
pre { background: #f5f5f5; padding: .6em; overflow-x: auto; font-size: .85em; }
code { font-size: .9em; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }
.flow { margin: .8em 0; padding: .7em .9em;
        background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.flow-phase { font-weight: bold; color: #2a6fd6; margin: .5em 0 .2em; }
.flow-step { background: #f0f4fa; border: 1px solid #ccc; border-radius: 4px;
             padding: .25em .6em; margin: .2em 0; line-height: 1.5; }
.flow-edge { color: #555; padding: .15em 0 .15em 1.5em; font-size: .95em; }
.flow-inline-arrow { color: #2a6fd6; font-weight: bold; margin: 0 .25em; }
.flow-arrow { color: #2a6fd6; text-align: center; line-height: 1.3; font-weight: bold;
              padding: .1em 0; }
.flow-edge .edge-fall { color: #2a6fd6; font-weight: bold; }
"""

def build_epub(md_path, out_path):
    with io.open(md_path, encoding='utf-8') as f:
        md_text = f.read()
    sections = split_sections(md_text)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', make_container())
        z.writestr('OEBPS/content.opf', make_opf(sections))
        z.writestr('OEBPS/toc.ncx', make_ncx(sections))
        z.writestr('OEBPS/style.css', EPUB_CSS)
        for s in sections:
            z.writestr(f'OEBPS/{s["id"]}.xhtml', make_xhtml(s))
    print(f'EPUB 已生成: {out_path}（{len(sections)} 章）')

if __name__ == '__main__':
    import os
    md = sys.argv[1] if len(sys.argv) > 1 else 'output/全书.md'
    out = sys.argv[2] if len(sys.argv) > 2 else 'output/book.epub'
    build_epub(md, out)
