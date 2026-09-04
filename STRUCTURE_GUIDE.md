<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
-->

# STRUCTURE_GUIDE — Cogito_Scribit 仓结构与族系规范（完结封版）

> 母书《我思故我写》v1.2.0 为**完结封版**：`book/` 内容不再变更，本文件只记录封版时刻的结构基线与族系统一规范，供两册姊妹卷对齐。

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

## 二、族系统一规范（三册共用，姊妹卷必须对齐）

### 1. 书内骨架（assemble 装配顺序）

```
版权页 → 前置件（导读 | 母书为序言+阅读指南）→ 正文（收束篇殿后）
→ 99_结语.md（结语，正文后、附录前）→ appendix/ 附录
```

- **99_结语为三册标配**：母书封版时已有；姊妹卷 v1.4.0（排版）/ v1.3.0（架构）起补齐。收束篇保持正文末篇不动，结语是书的收束章，两者职能不重复
- **附录在 `book/appendix/`**（内容名文件），frontmatter 只留前置件
- **PDF 管线在 `book/build/PDF/make_pdf.py`**（字体与产物随位）；封面三件套 `cover.png / cover.svg / cover_wechat.png` 在 `book/`

### 2. 仓级文件四类判定

| 类 | 职责 | 文件（每册统一命名） | 进书？ |
|----|------|---------------------|--------|
| A 书内内容 | 成书章节 | frontmatter / 正文 / 99_结语 / appendix | ✅ assemble 装配 |
| B 仓级规范 | 给维护者 | STRUCTURE_GUIDE.md（入书规范）；STYLE_GUIDE.md 全族系唯一一份，在 typesetting/（排版规范源，不重复） | ❌ |
| C 仓级对外 | 给读者/发行 | README.md（仓导航）、成册说明_<卷名>.md（发行说明）、index.html（**仓根**落地页） | ❌ |
| D 杂物 | 一次性/遗留 | 一律进 `archive/`（归档优于删除），不留在仓根 | ❌ |

### 3. 版本日志口径

版权页「## 版本」节为**一行式书籍口径**：一版一行，说清"这版改了什么、规模变化"。根因分析、几何数值、门禁扫描等工程细节只进 commit / Release notes / 成册说明，**不进书**——书籍修订日志不是更新日志。

### 4. 排版规范

全族系共用 `typesetting/STYLE_GUIDE.md`（十/十一章：目录页码列铁律、门禁扫描口径等），母书/排版册/架构册出片一律以它为唯一规范源，差异仅剩各书配置（书名/版本字/字体族/阈值按书标定）。
