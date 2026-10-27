# -*- coding: utf-8 -*-
"""生成《我写故我播》社媒封面两件套。

产物：
  book/cover.png          1200×630（GitHub/Gitee 仓库头图、Release 配图）
  book/cover_wechat.png    900×383（公众号卡片比例）

版式与《我思故我写》 cover.png 同源——深蓝渐变 #12224A→#081630 + 金色标
#C9A45C，逐像素沿用其几何（顶线 y=88、中线 y=365、标题 y=190、页脚 y=548），
只换文案。矢量源见同级 cover.svg（两处文字必须同步改，F17 一并核）。

字体：优先环境变量 PMB_FONT_DIR，否则回退族系共享字体目录（思源黑体 OTF
不入本册仓库，只借用）。
用法：cd book && python build/gen_covers.py
前置：pip install pillow
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..'))          # book/
FONT_DIR = os.environ.get('PMB_FONT_DIR') or os.path.normpath(
    os.path.join(HERE, '..', '..', '..', 'typesetting', 'book', 'build', 'PDF'))

GOLD = (201, 164, 92)
LIGHT = (232, 237, 248)
MUTED = (150, 165, 195)
TOP = (18, 34, 74)
BOTTOM = (8, 22, 48)

F_BOLD = os.path.join(FONT_DIR, 'SourceHanSansSC-Bold.otf')
F_MED = os.path.join(FONT_DIR, 'SourceHanSansSC-Medium.otf')
F_REG = os.path.join(FONT_DIR, 'SourceHanSansSC-Regular.otf')

# —— 文案（与 cover.svg 逐行对应，改一处必须改两处）——
MARK = 'PODCAST AGENT · FIELD NOTES'
TITLE = '我写故我播'
SUB1 = '一本 AI 犯过错的书'
SUB2 = '边界的实测、缺陷的坐标与因地制宜的裁量'
FOOT = 'wUwproject · v1.0.0 · CC BY-SA 4.0 · 免费公开'


def gradient(draw, w, h):
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)


def center(draw, text, font, y, fill, w, track=0):
    """按真字距（tracking，单位与 SVG letter-spacing 一致）逐字排版居中。

    不用「插空格」模拟字距——空格宽常是字号的 0.3 倍，会撑成稀排。
    """
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + track * max(0, len(text) - 1)
    x = (w - total) / 2
    for ch, cw in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += cw + track


def make_cover(w, h, out):
    img = Image.new('RGB', (w, h), TOP)
    d = ImageDraw.Draw(img)
    gradient(d, w, h)
    s = min(w / 1200.0, h / 630.0)  # 等比缩放取短板：900×383 若按宽度算会溢出下边界

    def sc(px):
        return int(px * s)

    d.line([(sc(336), sc(88)), (sc(864), sc(88))], fill=GOLD, width=max(1, sc(2)))
    center(d, MARK, ImageFont.truetype(F_MED, sc(34)), sc(100), GOLD, w, track=sc(6))
    center(d, TITLE, ImageFont.truetype(F_BOLD, sc(110)), sc(190), GOLD, w, track=sc(8))
    d.line([(sc(444), sc(365)), (sc(756), sc(365))], fill=GOLD, width=max(1, sc(3)))
    center(d, SUB1, ImageFont.truetype(F_MED, sc(32)), sc(385), LIGHT, w, track=sc(4))
    center(d, SUB2, ImageFont.truetype(F_REG, sc(28)), sc(448), LIGHT, w)
    center(d, FOOT, ImageFont.truetype(F_REG, sc(20)), sc(548), MUTED, w)

    img.save(out)
    print('OK %s (%dx%d)' % (out, w, h))


if __name__ == '__main__':
    for f in (F_BOLD, F_MED, F_REG):
        if not os.path.exists(f):
            raise SystemExit('字体缺失：%s\n请设 PMB_FONT_DIR 指向思源黑体 OTF 目录' % f)
    make_cover(1200, 630, os.path.join(OUT, 'cover.png'))
    make_cover(900, 383, os.path.join(OUT, 'cover_wechat.png'))
