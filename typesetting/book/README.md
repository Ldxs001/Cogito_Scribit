<!--
SPDX-License-Identifier: CC-BY-SA-4.0
Copyright (c) 2026 wUwproject
Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
See https://creativecommons.org/licenses/by-sa/4.0/ for details.
-->

# 我思故我写 · 排版解析——五层排版如何把一篇文章变成一本书

![书封](cover.png)

> **Cogito, Scribo.** 我思，故我写。
>
> 母书《我思故我写》的姊妹卷：母书回答"为什么"、架构解析册回答"怎么做"、本册回答"怎么排"——源稿、元素、骨架、页面、元数据五层排版的完整路径。

> **协议：本书整体采用 CC BY-SA 4.0**（署名-相同方式共享 4.0 国际）。详情见 `frontmatter/00_版权页.md`。

## 获取本册

| 方式 | 入口 |
|------|------|
| **在线阅读整本册子** | GitHub Pages：<https://ldxs001.github.io/Cogito_Scribit/typesetting/book/> |
| **下载 PDF / HTML / EPUB** | 发行版 **typ-v1.5.0**（[Gitee](https://gitee.com/wUwproject/Cogito_Scribit/releases/tag/typ-v1.5.0) / [GitHub](https://github.com/Ldxs001/Cogito_Scribit/releases/tag/typ-v1.5.0)，含 PDF 打印版） |
| **册子源码（Markdown）** | 本目录 `book/`（frontmatter：版权页 / 导读 / 附录 A / 附录 B） |
| **构建管线** | `build/`（`python build.py` 一键构建，复用母书管线） |

## 本册的结构

| 部分 | 目录 | 内容 |
|------|------|------|
| 版权页 | `frontmatter/00_版权页.md` | 版本、协议、署名 |
| 导读 | `frontmatter/00_导读.md` | 五层排版路径与映射表 |
| 正文八篇 | 仓库 `typesetting/articles/` | 五层排版（源稿/元素/骨架/页面/元数据）+ 规范排版（条文之家与族系工程）+ 管线排版（规则入脚本）+ 收束篇（AI 任务执行的完整流程） |
| 附录 A | `appendix/统一术语表.md` | 统一术语表 |
| 附录 B | `appendix/排版速查.md` | 排版速查 |

全册规模与版本见 `frontmatter/00_版权页.md`（当前 typ-v1.5.0，13 章）。

## 目录结构

```
book/
├── README.md               # 本册门面（本文件）
├── index.html              # 在线阅读落地页（GitHub Pages）
├── cover.png               # 书封（1200×630）
├── cover_wechat.png        # 微信宣传图（900×383）
├── frontmatter/            # 版权页 / 导读 / 附录 A 术语表 / 附录 B 排版速查
└── build/                  # 构建管线（assemble/md2html/make_pdf/count_words/gen_covers）
```

## 同系列

- 母书《我思故我写》：[`../../book/`](../../book/)
- 姊妹卷《架构解析》：<https://gitee.com/wUwproject/architecture>（GitHub 同名仓库）
- 源仓库双平台同步，内容一致，任选其一：
  - Gitee：<https://gitee.com/wUwproject/Cogito_Scribit>
  - GitHub：<https://github.com/Ldxs001/Cogito_Scribit>
