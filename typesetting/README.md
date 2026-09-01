<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
-->

# Typesetting — 排版规范与排版解析册

> wUwproject 的 AI 成书排版规范与排版方法论文档集。CC BY-SA 4.0。

## 仓库定位

本目录收录 Cogito_Scribit 成书过程中的**排版规范**与**排版方法论**：单篇写作规范（STYLE_GUIDE）、转化入书排版规范（STRUCTURE_GUIDE）与成书排版系列文章（articles/）。2026-09-01 自仓库根拆出并汇编姊妹册，规范文件历史提交保留（git mv）。

## 排版解析（姊妹卷）

本目录 5 篇排版方法论文章已汇编为册子《**我思故我写 · 排版解析——五层排版如何把一篇文章变成一本书**》（typ-v1.0.0，约 1.7 万字，CC BY-SA 4.0）——母书《我思故我写》的姊妹卷：母书回答"为什么"、架构解析册回答"怎么做"、本册回答"怎么排"。

| 项 | 入口 |
|----|------|
| 在线阅读整本册子（GitHub Pages） | <https://ldxs001.github.io/Cogito_Scribit/typesetting/book/> |
| 下载 PDF / HTML / EPUB | 发行版 **typ-v1.0.0**（[GitHub](https://github.com/Ldxs001/Cogito_Scribit/releases/tag/typ-v1.0.0) / Gitee 同 tag，含 PDF 打印版） |
| 册子源码（版权页/导读/附录 A/B + 封面 + 落地页） | [`book/`](book/) |
| 构建管线（MD → HTML/EPUB/PDF，复用母书管线） | `book/build/`（`python build.py` 一键构建） |

收录内容：版权页 + 导读（五层排版路径 + 映射表）+ 排版 01~05（源稿 / 元素 / 骨架 / 页面 / 元数据五层排版）+ 附录 A 统一术语表 + 附录 B 排版速查。

## 文档列表

| 文档 | 对应内容 | 类别 |
|------|---------|------|
| [STYLE_GUIDE.md](STYLE_GUIDE.md) | 单篇写作规范（版式 / 结构骨架 / 描述方式 / 命题纪律 / 四项检测） | 规范 |
| [STRUCTURE_GUIDE.md](STRUCTURE_GUIDE.md) | 转化入书排版规范（转化规则 / 同步清单 / 字数 / 版本号 / 构建管线 / PDF 打印版式） | 规范 |
| [成书排版（一）：先定样式，再写正文](articles/成书排版（一）：先定样式，再写正文.md) | 源稿排版——写作端与渲染端的契约 | 文章 |
| [成书排版（二）：单篇入书，元素去留](articles/成书排版（二）：单篇入书，元素去留.md) | 元素排版——入书元素的去留判据 | 文章 |
| [成书排版（三）：骨架排版——四部、导读与章序](articles/成书排版（三）：骨架排版——四部、导读与章序.md) | 骨架排版——四部、导读与章序 | 文章 |
| [成书排版（四）：页面排版——从屏幕到纸面](articles/成书排版（四）：页面排版——从屏幕到纸面.md) | 页面排版——分页 / 字体 / 封面 / 页码 | 文章 |
| [成书排版（五）：元数据排版——字数、章数与版本号](articles/成书排版（五）：元数据排版——字数、章数与版本号.md) | 元数据排版——字数口径 / 章数 / 版本号 | 文章 |

## 目录结构

```
typesetting/
├── README.md                   # 本导读
├── STYLE_GUIDE.md              # 单篇写作规范
├── STRUCTURE_GUIDE.md          # 转化入书排版规范
├── articles/                   # 排版系列文章（册子正文源稿）
│   └── 成书排版（一）~（五）.md
└── book/                       # 排版解析册（版权页/导读/附录/封面/落地页/构建管线）
    ├── index.html              # 在线阅读落地页（GitHub Pages）
    ├── cover.png               # 书封（1200×630）
    ├── cover_wechat.png        # 微信宣传图（900×383）
    ├── frontmatter/            # 版权页 / 导读 / 附录 A 术语表 / 附录 B 排版速查
    └── build/                  # 构建管线（assemble/md2html/make_pdf/count_words/gen_covers）
```

## 维护约定

- 本目录随 Cogito_Scribit 仓库维护，Gitee / GitHub 双平台同步
- 规范标准一旦固定不再变动——改规范 = 改文档 + 改渲染器/脚本 + 全量 rebuild
- 册子正文与仓库其他单篇同格式：SPDX 头 + 尾部 `*最后更新*` 脚注，CC BY-SA 4.0
- 文章与规范中的例子均来自真实条文与真实踩坑记录
