# -*- coding: utf-8 -*-
"""
《我写故我播》零依赖 EPUB3 生成器
EPUB3 本质 = ZIP 包 + XHTML 内容 + OPF 元数据 + TOC。
用标准库 zipfile 手写，无需 ebooklib/pandoc。
用法: python build_epub.py [全书.md] [输出.epub]
配图：从 assets_dir（默认自动探测 <md所在目录>/../articles/assets 等）拷入
      OEBPS/images/，重写 src 为 images/<basename>，并在 manifest 登记。
"""
import sys, io, os, re, zipfile, uuid, datetime
from md2html import md_to_html

BOOK_TITLE = "我写故我播——一本 AI 犯过错的书：边界的实测、缺陷的坐标与因地制宜的裁量"
BOOK_AUTHOR = "wUwproject"
# 独立 uuid5 命名空间：与《我思故我写》（cogito-liber-v1）区分，避免阅读器串书
BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "wowoboo-podcast-book-v1"))

EPUB_NS = {
    'container': 'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"',
    'opf': 'xmlns="http://www.idpf.org/2007/opf" version="3.0"',
    'xhtml': 'xmlns="http://www.w3.org/1999/xhtml"',
}

# 图片引用（只认 ![alt](assets/...) 形式，不误伤普通链接）
_IMG_REF = re.compile(r'(!\[[^\]]*\]\()(assets/)([^)\s]+)\)')
_MEDIA_TYPE = {
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
}

def _guess_assets_dir(md_path):
    """未显式传 assets_dir 时的探测链：<md目录>/assets → <md目录>/../articles/assets
    → 向上 3 层内找 articles/assets。找不到返回 None（EPUB 不带图）。"""
    d = os.path.dirname(os.path.abspath(md_path))
    cands = [
        os.path.join(d, 'assets'),
        os.path.normpath(os.path.join(d, '..', '..', 'articles', 'assets')),
        os.path.normpath(os.path.join(d, '..', '..', '..', 'articles', 'assets')),
    ]
    for c in cands:
        if os.path.isdir(c):
            return c
    return None

def collect_images(md_text):
    """返回本册实际引用的图片文件名列表（去重、保序）"""
    names, seen = [], set()
    for _pre, _dir, path in _IMG_REF.findall(md_text):
        base = os.path.basename(path)
        if base not in seen:
            seen.add(base)
            names.append(base)
    return names

def split_sections(md_text):
    """按一级标题（# ）切分章节——每篇/组件一章（跳过代码块内的 # 注释行）"""
    lines = md_text.split('\n')
    sections = []
    cur_title, cur_body = None, []
    in_code = False
    for line in lines:
        stripped = line.strip()
        # 代码块开关：``` 切换状态（围栏长度 3+）
        if stripped.startswith('```'):
            in_code = not in_code
        if not in_code and line.startswith('# '):
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

def make_opf(sections, images=()):
    manifest = '\n'.join(
        f'    <item id="{s["id"]}" href="{s["id"]}.xhtml" media-type="application/xhtml+xml"/>'
        for s in sections)
    manifest += '\n    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    manifest += '\n    <item id="css" href="style.css" media-type="text/css"/>'
    for i, name in enumerate(images, 1):
        ext = os.path.splitext(name)[1].lower()
        mt = _MEDIA_TYPE.get(ext, 'application/octet-stream')
        manifest += f'\n    <item id="img{i:03d}" href="images/{name}" media-type="{mt}"/>'
    spine = '\n'.join(f'    <itemref idref="{s["id"]}"/>' for s in sections)
    modified = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    return f'''<?xml version="1.0" encoding="utf-8"?>
<package {EPUB_NS['opf']} unique-identifier="BookId">
  <metadata {EPUB_NS['opf']}>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">{BOOK_TITLE}</dc:title>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{BOOK_AUTHOR}</dc:creator>
    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="BookId">{BOOK_ID}</dc:identifier>
    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">zh-CN</dc:language>
    <dc:rights xmlns:dc="http://purl.org/dc/elements/1.1/">CC BY-SA 4.0</dc:rights>
    <meta property="dcterms:modified">{modified}</meta>
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
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
pre { background: #f5f5f5; padding: .6em; overflow-x: auto; font-size: .85em; }
code { font-size: .9em; }
.math { font-family: "Times New Roman", Georgia, serif;
        font-style: italic; white-space: nowrap; }
.math sup, .math sub { font-style: normal; font-size: .72em; }
.math-block { text-align: center; margin: .8em 0; padding: .6em .9em;
              background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.math-block .math { font-size: 1.1em; white-space: normal; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }
.flow { margin: .8em 0; padding: .7em .9em;
        background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.flow-phase { font-weight: bold; color: #2a6fd6; margin: .5em 0 .2em; }
.flow-step { background: #f0f4fa; border: 1px solid #ccc; border-radius: 4px;
             padding: .25em .6em; margin: .2em 0; line-height: 1.5; }
.flow-step.lv1 { background: rgba(160,166,172,.10); }
.flow-step.lv2 { background: rgba(122,148,178,.10); }
.flow-step.lv3 { background: rgba(126,158,138,.10); }
.flow-step.lv4 { background: rgba(158,138,116,.10); }
.flow-step.lv5 { background: rgba(158,150,168,.10); }
.flow-edge { color: #555; padding: .15em 0 .15em 1.5em; font-size: .95em; }
.flow-note { color: #777; font-size: .88em; padding: .15em 0; text-align: center; }
.flow-chain { display: flex; align-items: stretch; justify-content: center;
              flex-wrap: wrap; gap: .4em; margin: .8em 0;
              padding: .7em .9em; background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.flow-chain-title { align-self: center; font-weight: bold; color: #2a6fd6;
                    font-size: 1.05em; margin-right: .4em;
                    padding: .3em .6em; background: #e8f0fb; border-radius: 6px; }
.flow-cnode { display: flex; flex-direction: column; justify-content: center;
              min-width: 5.5em; text-align: center; }
.flow-cnode .flow-step { margin: 0; }
.flow-cnode .flow-note { margin-top: .2em; }
.flow-carr { align-self: center; color: #2a6fd6; font-weight: bold; font-size: 1.15em; }
.flow-layers { margin: .8em 0; padding: .6em .8em;
               background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.flow-layer { border: 1px solid #ccc; border-radius: 6px; margin: .5em 0;
              padding: .4em .6em; background: #fafbfd; }
.flow-layer.lv1 { background: rgba(160,166,172,.10); }
.flow-layer.lv2 { background: rgba(122,148,178,.10); }
.flow-layer.lv3 { background: rgba(126,158,138,.10); }
.flow-layer.lv4 { background: rgba(158,138,116,.10); }
.flow-layer.lv5 { background: rgba(158,150,168,.10); }
.flow-layer-name { font-weight: bold; color: #2a6fd6; margin-bottom: .2em; }
.flow-layer-item { line-height: 1.6; }
.flow-layer-key { color: #555; font-weight: bold; margin-right: .3em; }
.flow-tree { margin: .8em 0; padding: .6em .8em;
             background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px;
             font-family: Consolas, "Courier New", monospace;
             font-size: .9em; line-height: 1.7; }
.flow-tnode { padding: .05em 0; white-space: nowrap; }
.flow-tmark { color: #888; margin-right: .35em; }
.flow-tnode.dir .flow-ttext { font-weight: bold; }
.flow-step.ellipsis-step { color: #999; }
.flow-treegroup { border: 1px solid #ccc; border-radius: 8px;
                  margin: .25em 0; padding: .35em .7em;
                  font-family: Consolas, "Courier New", monospace;
                  font-size: .9em; line-height: 1.7; }
.flow-treegroup.lv1 { background: rgba(160,166,172,.10); }
.flow-treegroup.lv2 { background: rgba(122,148,178,.10); }
.flow-treegroup.lv3 { background: rgba(126,158,138,.10); }
.flow-treegroup.lv4 { background: rgba(158,138,116,.10); }
.flow-treegroup.lv5 { background: rgba(158,150,168,.10); }
.flow-tree-row { padding: .08em 0; white-space: pre; }
.flow-tree-row.lv1 { background: rgba(160,166,172,.07); }
.flow-tree-row.lv2 { background: rgba(122,148,178,.07); }
.flow-tree-row.lv3 { background: rgba(126,158,138,.07); }
.flow-tree-row.lv4 { background: rgba(158,138,116,.07); }
.flow-tree-row.lv5 { background: rgba(158,150,168,.07); }
.flow-tnode.lv1 { background: rgba(160,166,172,.07); }
.flow-tnode.lv2 { background: rgba(122,148,178,.07); }
.flow-tnode.lv3 { background: rgba(126,158,138,.07); }
.flow-tnode.lv4 { background: rgba(158,138,116,.07); }
.flow-tnode.lv5 { background: rgba(158,150,168,.07); }
.flow-tree-row .flow-tmark { color: #888; }
.flow-cols { display: flex; gap: 1.2em; margin: .8em 0;
             padding: .7em .9em; background: #f4f6fa; border: 1px solid #ccc; border-radius: 8px; }
.flow-col { flex: 1; min-width: 0; }
.flow-col .flow-step { margin: .3em 0; }
.flow-col .flow-edge { padding-left: 0; text-align: center; color: #777; }
.flow-inline-arrow { color: #2a6fd6; font-weight: bold; margin: 0 .25em; }
.flow-arrow { color: #2a6fd6; text-align: center; line-height: 1.3; font-weight: bold;
              padding: .1em 0; }
.flow-edge .edge-fall { color: #2a6fd6; font-weight: bold; }
"""

def build_epub(md_path, out_path, assets_dir=None):
    with io.open(md_path, encoding='utf-8') as f:
        md_text = f.read()

    # 配图 sink 归一到 images/，并收集实际引用清单
    images = collect_images(md_text)
    src_dir = assets_dir or _guess_assets_dir(md_path)
    if images and not src_dir:
        print(f'警告：正文引用 {len(images)} 张图，但未找到 assets 目录，EPUB 将缺图')
        images = []
    md_for_epub = _IMG_REF.sub(lambda m: f'{m.group(1)}images/{m.group(3)})', md_text)

    sections = split_sections(md_for_epub)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', make_container())
        z.writestr('OEBPS/content.opf', make_opf(sections, images))
        z.writestr('OEBPS/toc.ncx', make_ncx(sections))
        z.writestr('OEBPS/style.css', EPUB_CSS)
        for s in sections:
            z.writestr(f'OEBPS/{s["id"]}.xhtml', make_xhtml(s))
        missing = []
        for name in images:
            src = os.path.join(src_dir, name)
            if os.path.isfile(src):
                z.write(src, f'OEBPS/images/{name}')
            else:
                missing.append(name)
    print(f'EPUB 已生成: {out_path}（{len(sections)} 章 / 配图 {len(images)} 张）')
    if missing:
        print(f'警告：{len(missing)} 张图源文件缺失: {missing[:5]}')

if __name__ == '__main__':
    md = sys.argv[1] if len(sys.argv) > 1 else 'output/我写故我播全书.md'
    out = sys.argv[2] if len(sys.argv) > 2 else 'output/book.epub'
    build_epub(md, out)
