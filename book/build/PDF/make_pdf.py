# -*- coding: utf-8 -*-
"""《我思故我写》打印版 PDF 全流程生成脚本。

流程：
1. PIL 渲染封面 PNG（思源黑体 OTF 直接画入图片，150dpi A4）
2. book/build/output/book.html → 打印版 HTML（去 dark / 思源黑体
   @font-face / 打印 CSS）→ Playwright 渲染正文 PDF（@page 精确 18mm 边距）
3. PyMuPDF 合并：封面页 + 正文页

产物：book_print.pdf（封面独立 PDF 页 + 正文 Type3 思源黑体矢量字形，
零字体嵌入、零分发争议；封面与正文物理分离，不会互相污染）
用法：cd book/build/PDF && python make_pdf.py
前置：pip install playwright pillow pymupdf
      python -m playwright install chromium
      本目录须有 SourceHanSansSC-Regular/Medium/Bold.otf（封面 + @font-face）
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
BODY_PDF = os.path.join(BASE, 'book_print.body.pdf')
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

PRINT_CSS = """@page {
  size: A4;
  margin: 18mm 16mm;
}
@media print {
  /* 打印去掉 body padding/margin，边距由 @page 控制 */
  body { padding: 0 !important; max-width: none; margin: 0 !important; }
  /* 书籍标准分页：版权页/序言/阅读指南/每篇/结语/附录各自独立起页 */
  h1 { break-before: page; }
  /* 小节标题不落页末：标题与后续内容同页 */
  h2, h3, h4 { break-after: avoid; }
  /* 段落防孤立行（页首/页底最少 3 行） */
  p, li { orphans: 3; widows: 3; }
  /* 分隔线/修饰符不独占一页 */
  hr, .flow-arrow { break-inside: avoid; break-before: avoid; break-after: avoid; }
  pre, .flow, .flow-tree, .flow-treegroup, .flow-cols, .flow-layers, table { break-inside: avoid; }
  .flow-step, .flow-layer, tr { break-inside: avoid; }
}"""


def make_cover_png():
    """PIL 渲染 A4 封面图（300dpi 印刷标准，2480×3508）
    到 BASE/cover.png（PNG 无损——渐变数据是平滑插值，PNG 预测滤波
    压缩率极高，实测 0.17MB 比 JPEG q88 还小，且文字无振铃、
    渐变无 DCT 块伪影）。
    配色与原 cover.svg 一致（深蓝渐变 #12224A→#081630 + 金色标 #C9A45C），
    文字用思源黑体 OTF 直接画入图片（图片内文字，非字体分发）。
    注意：封面是位图，打印分辨率 = 像素 ÷ 8.27 英寸——300ppi 为印刷
    行业标准；600ppi 在 A4 阅读距离无感知增益。"""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 2480, 3508  # A4 @300dpi
    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    top = (18, 34, 74)   # #12224A
    bot = (8, 22, 48)    # #081630
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)],
                  fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    reg = os.path.join(BASE, 'SourceHanSansSC-Regular.otf')
    bold = os.path.join(BASE, 'SourceHanSansSC-Bold.otf')
    medium = os.path.join(BASE, 'SourceHanSansSC-Medium.otf')
    f_kicker = ImageFont.truetype(medium, 88)
    f_title = ImageFont.truetype(bold, 238)
    f_sub = ImageFont.truetype(reg, 109)
    f_sub2 = ImageFont.truetype(reg, 75)
    f_meta = ImageFont.truetype(reg, 59)
    f_ver = ImageFont.truetype(reg, 53)
    f_note = ImageFont.truetype(reg, 41)
    GOLD = (201, 164, 92)
    LIGHT = (232, 237, 248)
    SUB = (216, 223, 236)
    SUB2 = (150, 165, 195)
    META = (150, 165, 195)
    VER = (124, 139, 176)
    NOTE = (143, 160, 191)

    def center(text, font, y, fill):
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y), text, font=font, fill=fill)

    center('COGITO · SCRIBO', f_kicker, 519, GOLD)
    center('我思故我写', f_title, 759, LIGHT)
    center('一本 AI 写成的书', f_sub, 1181, SUB)
    center('AI 时代的方法论、边界与人类自洽', f_sub2, 1381, SUB2)
    draw.line([(W / 2 - 360, 1600), (W / 2 + 360, 1600)], fill=(201, 164, 92, 140), width=6)
    center('wUwproject · CC BY-SA 4.0 · 免费公开', f_meta, 2659, META)
    center('v1.1.0 · 2026 年 8 月', f_ver, 2841, VER)
    note = '本书文字（含书名、标题、正文、图表标注）使用思源黑体（Source Han Sans SC）渲染，字体采用 SIL OFL 1.1 开源许可。'
    nw = draw.textlength(note, font=f_note)
    draw.text(((W - nw) / 2, 3241), note, font=f_note, fill=NOTE)
    out = os.path.join(BASE, 'cover.png')
    img.save(out, 'PNG', optimize=True)
    print('封面 PNG 已生成（300dpi 2480×3508 无损）:', out)


def build_print_html():
    with io.open(SRC, encoding='utf-8') as f:
        t = f.read()
    # 1) 去掉 dark 媒体查询（打印强制 light）
    t = re.sub(r'@media \(prefers-color-scheme: dark\) \{.*?\n\}', '', t, flags=re.S)
    # 2) 字体栈干净替换（从原始 book.html 出发，避免叠加）
    t = t.replace('"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif', FONT_BODY)
    t = t.replace('Consolas, "Courier New", monospace', FONT_MONO)
    t = t.replace('"PingFang SC", "Microsoft YaHei"', FONT_BODY)  # 兜底形态
    # 3) 注入 @font-face + 打印 CSS
    t = t.replace('</style>', FONT_FACE + '\n' + PRINT_CSS + '\n</style>', 1)
    with io.open(TMP_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    print('打印版 HTML 已生成:', TMP_HTML)
    print('dark 块残留:', '@media (prefers-color-scheme: dark)' in t,
          '| YaHei 残留(回退链内):', 'Microsoft YaHei' in t,
          '| @page CSS:', '@page {' in t)


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
        page.pdf(path=BODY_PDF, prefer_css_page_size=True,
                 print_background=True)
        browser.close()
    # 合并：封面页（PIL PNG → A4 页）置于正文前
    import fitz
    cover_png = os.path.join(BASE, 'cover.png')
    body = fitz.open(BODY_PDF)
    cover = fitz.open()
    page = cover.new_page(width=595, height=842)  # A4 pt
    page.insert_image(fitz.Rect(0, 0, 595, 842), filename=cover_png)
    cover.insert_pdf(body)
    # deflate=True：PyMuPDF 嵌入 PNG 时存未压缩像素（~25MB），
    # Flate 重压后 ~3.9MB（垂直渐变行间重复，压缩率极高）
    cover.save(OUT, garbage=3, deflate=True)
    n = cover.page_count
    cover.close()
    body.close()
    os.remove(BODY_PDF)
    print(f'PDF 已生成（封面 + 正文 {n-1} 页 = 共 {n} 页）:', OUT)
    os.remove(TMP_HTML)  # 中间产物不留（可随时再生成）
    print('临时 HTML 已清理:', TMP_HTML)


if __name__ == '__main__':
    make_cover_png()
    build_print_html()
    render_pdf()
