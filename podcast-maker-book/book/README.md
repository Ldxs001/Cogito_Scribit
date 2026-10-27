<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
-->

# 我写故我播——一本 AI 犯过错的书

**边界的实测、缺陷的坐标与因地制宜的裁量**

> 本目录是《我写故我播》的**书稿构件区**。正文源稿不在这里——它在册根 `articles/`（唯一源），本目录只放前置件、结语、附录与构建管线。这是族系（`typesetting/` 规范）的统一目录语言：正文在册外源稿区，书内件在 `book/`。

## 构件

```
book/
├── README.md                  ← 本文件
├── cover.svg                  ← 封面矢量源
├── cover.png                  ← 1200×630 社媒图
├── cover_wechat.png           ← 900×383
├── frontmatter/
│   ├── 00_版权页.md
│   ├── 00_序言.md
│   └── 00_阅读指南.md          ← 含「缺陷坐标表」：47 篇逐篇标缺陷主体
├── 99_结语.md
├── appendix/                  ← 七件，A/B/C 与《我思故我写》同名同位
│   ├── 术语表.md               # A
│   ├── 工具索引.md             # B
│   ├── 参考文献.md             # C
│   ├── 实测数字速查.md         # D
│   ├── CHANGELOG锚点索引.md    # E
│   ├── 模型底座.md             # F
│   └── 提示词逻辑体系.md       # G
└── build/
    ├── assemble.py            ← 拼接全书（66 章）
    ├── build.py               ← 主入口：assemble → HTML → EPUB
    ├── md2html.py             ← 零依赖 MD→HTML（含图片、流程图、公式）
    ├── build_epub.py          ← 零依赖 EPUB3（配图内嵌）
    ├── count_words.py         ← 六口径字数，⑥出版折算对外
    ├── output/                ← 产物（入仓：全书 md / book.html / book.epub / assets）
    └── PDF/make_pdf.py        ← 印刷版 PDF（封面 + 正文，Playwright）
```

## 构建

```bash
# 全量构建：全书 md + HTML + EPUB
cd book && python build/build.py

# 只拼全书
python book/build/assemble.py

# 字数（六口径，⑥为对外出版折算）
python book/build/count_words.py

# 印刷版 PDF（需 playwright / pillow / pymupdf + 思源黑体）
cd book/build/PDF && python make_pdf.py
```

产物落 `book/build/output/`：`我写故我播全书.md` / `book.html` / `book.epub` / `assets/`。

## 三条硬约束

1. **章题只加前缀，不改原标题**——源稿 H1 即书内章题。本书单篇入书，不存在第二套标题。
2. **成书无摘要、无日期戳、无版本脚注**——`assemble.py` 的 `strip_writing_traces` 负责剥离；章间不注入分隔线。
3. **《我思故我写》与本书平行同级**——一切产出物禁用主从式称谓；引用一律署《我思故我写》＋篇号。

## 协议

CC BY-SA 4.0。正文源稿与本书构件同协议，可自由传播，须署名 wUwproject。
