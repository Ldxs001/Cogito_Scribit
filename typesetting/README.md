# Typesetting（排版）

本目录收录 Cogito_Scribit 成书过程中的**写作规范**与**排版方法论**，并汇编为姊妹册《**我思故我写 · 排版解析**》。

## 姊妹册：《我思故我写 · 排版解析》

> 五层排版如何把一篇文章变成一本书——源稿怎么排、一章怎么去留、四部怎么立、纸面怎么切、数字怎么对。母书回答"为什么"、架构解析回答"怎么做"、本册回答"**怎么排**"。

| 项 | 值 |
|---|---|
| 册名 | 《我思故我写 · 排版解析——五层排版如何把一篇文章变成一本书》 |
| 版本 | **typ-v1.0.0**（2026 年 9 月初版，9 章，约 1.7 万字） |
| 协议 | CC BY-SA 4.0 |
| 关系 | 母书《我思故我写》v1.2.0 的排版侧姊妹卷；与《架构解析》arch-v1.0.0 同体系 |

**下载**（`book/build/output/` + `book/build/PDF/`）：

| 格式 | 路径 |
|---|---|
| HTML（在线阅读） | `book/build/output/book.html` |
| EPUB | `book/build/output/book.epub` |
| PDF（打印版，36 页） | `book/build/PDF/book_print.pdf` |
| 书封 / 微信宣传图 | `book/cover.png`（1200×630）/ `book/cover_wechat.png`（900×383） |

## 目录结构

```
typesetting/
├── STYLE_GUIDE.md      # 单篇写作规范：版式（表格/图/公式）+ 结构骨架 + 描述方式 + 命题纪律 + 四项检测
├── STRUCTURE_GUIDE.md  # 转化入书排版规范：转化规则 + 同步清单 + 字数/版本号 + 构建管线 + PDF 打印版式
├── articles/           # 排版系列文章（册子正文源稿）
│   └── 成书排版（一）~（五）.md
└── book/               # 姊妹册《排版解析》（frontmatter + 正文汇编 + 构建管线 + 封面）
    ├── frontmatter/    # 版权页 / 导读 / 附录 A 术语表 / 附录 B 排版速查
    ├── build/          # 构建管线（assemble/md2html/make_pdf/count_words/gen_covers）
    ├── cover.png       # 书封
    └── cover_wechat.png # 微信宣传图
```

## 阅读顺序

1. **《排版解析》册**（book/ 汇编）：版权页 → 导读（五层排版路径 + 映射表）→ 排版 01~05（源稿/元素/骨架/页面/元数据）→ 附录 A/B
2. **规范本体**：`STYLE_GUIDE.md`（写单篇时看）、`STRUCTURE_GUIDE.md`（入书时看）——册子正文是这两份规范的展开叙述
3. **重建册子**：`cd typesetting/book/build && python build.py`（→ 排版解析全书.md / book.html / book.epub）→ `cd PDF && python make_pdf.py`（→ book_print.pdf）→ `python count_words.py` ⑥ 取数回填版权页

## 约定

- 规范标准一旦固定不再变动——改规范 = 改文档 + 改渲染器/脚本 + 全量 rebuild
- 册子正文与仓库其他单篇同格式：SPDX 头 + 尾部 `*最后更新*` 脚注，CC BY-SA 4.0
- 文章与规范中的例子均来自真实条文与真实踩坑记录
