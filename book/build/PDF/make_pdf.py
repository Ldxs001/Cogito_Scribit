# -*- coding: utf-8 -*-
"""《我思故我写》打印版 PDF 全流程生成脚本。

流程：book/build/output/book.html → 打印版 HTML（去 dark / 思源黑体
@font-face / 注入封面页 / 注入字体声明 / 打印 CSS）→ Playwright 渲染 PDF。

产物：book_print.pdf（思源黑体 Type3 矢量字形，零字体嵌入、零分发争议）
用法：cd book/build/PDF && python make_pdf.py
前置：pip install playwright && python -m playwright install chromium
      本目录须有 SourceHanSansSC-Regular/Medium/Bold.otf（@font-face 引用）
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(BASE, '..', 'output', 'book.html'))
TMP_HTML = os.path.join(BASE, 'book_print.tmp.html')
OUT = os.path.join(BASE, 'book_print.pdf')

FONT_BODY = '"SourceHanPrint", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
FONT_MONO = '"DejaVu Sans Mono", "SourceHanPrint", Consolas, monospace'

FONT_FACE = """@font-face {
  font-family: "SourceHanPrint";
  src: url("SourceHanSansSC-Regular.otf") format("opentype");
  font-weight: normal;
}
@font-face {
  font-family: "SourceHanPrint";
  src: url("SourceHanSansSC-Medium.otf") format("opentype");
  font-weight: 500;
}
@font-face {
  font-family: "SourceHanPrint";
  src: url("SourceHanSansSC-Bold.otf") format("opentype");
  font-weight: bold;
}"""

PRINT_CSS = """@media print {
  /* 封面独占一页（A4 内容高约 261mm，留余量防换页） */
  .pdf-cover { min-height: 250mm; break-after: page; }
  body { max-width: none; }
  /* 书籍标准分页：版权页/序言/阅读指南/每篇/结语/附录各自独立起页 */
  h1 { break-before: page; }
  pre, .flow, .flow-tree, .flow-treegroup, .flow-cols, .flow-layers, table { break-inside: avoid; }
  .flow-step, .flow-layer, tr { break-inside: avoid; }
}"""

# 封面页：配色与原 cover.svg 一致（深蓝渐变 #12224A→#081630 + 金色标
# #C9A45C + 浅字 #E8EDF8），字体全走 SourceHanPrint
COVER = """<div class="pdf-cover">
  <div class="pdf-cover-inner">
    <div class="pdf-cover-kicker">COGITO · SCRIBO</div>
    <div class="pdf-cover-title">我思故我写</div>
    <div class="pdf-cover-sub">一本 AI 写成的书</div>
    <div class="pdf-cover-sub2">AI 时代的方法论、边界与人类自洽</div>
    <div class="pdf-cover-line"></div>
    <div class="pdf-cover-meta">wUwproject · CC BY-SA 4.0 · 免费公开</div>
    <div class="pdf-cover-ver">v1.1.0 · 2026 年 8 月</div>
    <div class="pdf-cover-note">本书文字（含书名、标题、正文、图表标注）使用思源黑体（Source Han Sans SC）渲染，字体采用 SIL OFL 1.1 开源许可。</div>
  </div>
</div>"""

COVER_CSS = """.pdf-cover { display: flex; align-items: center; justify-content: center; text-align: center;
  background: linear-gradient(180deg, #12224A 0%, #081630 100%); color: #E8EDF8; }
.pdf-cover-inner { width: 100%; }
.pdf-cover-kicker { font-size: 22px; letter-spacing: .6em; color: #C9A45C; margin-bottom: 28px; font-weight: 500; }
.pdf-cover-title { font-size: 64px; font-weight: bold; color: #E8EDF8; letter-spacing: .18em; margin-bottom: 20px; }
.pdf-cover-sub { font-size: 26px; color: #D8DFEC; letter-spacing: .3em; margin-bottom: 10px; }
.pdf-cover-sub2 { font-size: 18px; color: #96A5C3; letter-spacing: .12em; margin-bottom: 34px; }
.pdf-cover-line { width: 200px; height: 1px; background: rgba(201,164,92,.55); margin: 0 auto 30px; }
.pdf-cover-meta { font-size: 15px; color: #96A5C3; letter-spacing: .08em; margin-bottom: 8px; }
.pdf-cover-ver { font-size: 13px; color: #7C8BB0; margin-bottom: 40px; }
.pdf-cover-note { font-size: 10.5px; color: #8FA0BF; line-height: 1.7; padding: 0 8%; }"""


def build_print_html():
    with io.open(SRC, encoding='utf-8') as f:
        t = f.read()
    # 1) 去掉 dark 媒体查询（打印强制 light）
    t = re.sub(r'@media \(prefers-color-scheme: dark\) \{.*?\n\}', '', t, flags=re.S)
    # 2) 字体栈干净替换（从原始 book.html 出发，避免叠加）
    t = t.replace('"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif', FONT_BODY)
    t = t.replace('Consolas, "Courier New", monospace', FONT_MONO)
    t = t.replace('"PingFang SC", "Microsoft YaHei"', FONT_BODY)  # 兜底形态
    # 3) 注入 @font-face + 封面 CSS + 打印 CSS
    t = t.replace('</style>', FONT_FACE + '\n' + COVER_CSS + '\n' + PRINT_CSS + '\n</style>', 1)
    # 4) 注入封面页（body 开头，TOC 之前）
    t = re.sub(r'(<body[^>]*>)', r'\1\n' + COVER, t, count=1)
    with io.open(TMP_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    print('打印版 HTML 已生成:', TMP_HTML)
    print('dark 块残留:', '@media (prefers-color-scheme: dark)' in t,
          '| YaHei 残留:', 'Microsoft YaHei' in t,
          '| 封面注入:', 'pdf-cover-title' in t,
          '| 声明注入:', 'SIL OFL 1.1' in t)


def render_pdf():
    html_url = 'file:///' + TMP_HTML.replace('\\', '/')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_url, wait_until='networkidle')
        page.evaluate('document.fonts.ready.then(() => true)')
        page.wait_for_timeout(2000)
        fonts = page.evaluate('''() => {
            const used = [];
            for (const f of document.fonts) {
                if (f.status === 'loaded') used.push(f.family + ':' + f.weight);
            }
            return used.slice(0, 10);
        }''')
        print('已加载字体:', fonts)
        page.pdf(path=OUT, format='A4',
                 margin={'top': '18mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'},
                 print_background=True)
        browser.close()
    print('PDF 已生成:', OUT)
    os.remove(TMP_HTML)  # 中间产物不留（可随时再生成）
    print('临时 HTML 已清理:', TMP_HTML)


if __name__ == '__main__':
    build_print_html()
    render_pdf()
