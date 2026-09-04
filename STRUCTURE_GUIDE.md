<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
-->

# STRUCTURE_GUIDE — Cogito_Scribit 仓结构与族系规范（完结封版）

> 母书《我思故我写》v1.2.0 为**完结封版**：`book/` 内容不再变更，本文件只记录封版时刻的结构基线，供两册姊妹卷对齐。
> **族系通用成书规范（书籍/文件夹/文件三结构）的唯一规范源已上移至仓根 [`成书规范.md`](成书规范.md)**——本文件不再复制族系条目，只保留封版时刻的结构基线；两册姊妹卷同样以《成书规范》为准。

## 一、仓结构基线（封版时刻）

```
Cogito_Scribit/
├── README.md                  # 仓导航（体系入口 + 阅读顺序）
├── 方法论体系总览.md           # 21 篇文章的体系总纲（文章层地图）
├── 成册说明_我思故我写.md      # 发行说明（对外，不进书）
├── STRUCTURE_GUIDE.md         # 本文件
├── LICENSE / index.html / assets/
├── 01~10 系列 *.md            # 21 篇源文章（文章层）
├── archive/                   # 一次性报告与遗留杂物归档
├── book/                      # 母书成书（封版）
│   ├── README.md              # 构建管线说明
│   ├── cover.png / cover.svg / cover_wechat.png
│   ├── frontmatter/           # 00_版权页 / 00_序言 / 00_阅读指南
│   ├── part1~part4/           # 四部正文（各含部导读）
│   ├── 99_结语.md             # 结语（正文后、附录前装配）
│   ├── appendix/              # 附录 A/B/C
│   └── build/                 # assemble / build / md2html / count_words / build_epub / PDF/
└── typesetting/               # 排版册（独立版本 typ-v*，随排版规则演进）
```

## 二、族系统一规范 → 已上移

三册共用的成书规范（书内骨架、四类判定、版本日志口径、排版规范源指引）已于 2026-09-04 收编为仓根 **《成书规范.md》v1.0**，作为族系唯一规范源。本节原详细条目不再在此维护，查规范一律读《成书规范.md》；本文件后续只记录母书仓特有内容与历史教训。
