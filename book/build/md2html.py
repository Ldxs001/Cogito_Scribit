# -*- coding: utf-8 -*-
"""
《我思故我写》零依赖 Markdown → HTML 转换器
支持：标题(#/##/###)、引用(>)、表格(|)、代码块(```)、粗体(**)、斜体(*)、
     列表(-/1.)、链接([text](url))、分隔线(---)、行内代码(`)
输出：内联 CSS 的完整 HTML 文档（禁外部 CDN、资源内联——用户铁律）
"""
import re, html as html_mod

def _escape_skip_entities(text):
    """html.escape 但跳过已存在的 HTML 实体（如 &#124; &amp; &nbsp;）以避免双重转义"""
    return re.sub(r'&(?!(?:#[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);)', '&amp;', text)

def _inline(text):
    """行内元素转换"""
    t = _escape_skip_entities(text)
    # 行内代码（先转义保护）
    code_spans = []
    def _save_code(m):
        code_spans.append(m.group(1))
        return f'\x00CODE{len(code_spans)-1}\x00'
    t = re.sub(r'`([^`]+)`', _save_code, t)
    # 链接
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    # 粗体
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    # 斜体
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    # 恢复行内代码
    for i, c in enumerate(code_spans):
        t = t.replace(f'\x00CODE{i}\x00', f'<code>{c}</code>')
    return t

def _format_cell(content):
    """处理表格单元格内的多段内容：<br> 分隔的每段用 <span> 包裹，
    让 CSS 可以对每段分别控制 nowrap/keep-all。"""
    # _inline 已转义了 & 实体，但保留了 <br> 字符
    if '<br>' in content:
        parts = content.split('<br>')
        # 注意：parts 里如果已经被 _inline 转义，里面的 < 可能被转成 &lt;
        # 这里只需做包装，不重新转义
        pieces = []
        for p in parts:
            p = p.strip()
            if p:
                pieces.append(f'<span class="ref-piece">{p}</span>')
        return ''.join(pieces)
    return content


def _table(rows):
    """表格：rows = 分割后的行列表"""
    # 过滤分隔行（|------|、|:---:| 等整行连字符/冒号/竖线形式）
    sep_re = re.compile(r'^\s*\|?[\s:|-]+\|?\s*$')
    body = [r for r in rows if not sep_re.match(r)]
    if not body:
        return ''
    html_rows = []
    ref_class = ''
    first_cells = None
    for i, r in enumerate(body):
        cells = [c.strip() for c in r.strip().strip('|').split('|')]
        if i == 0:
            first_cells = cells
        tag = 'th' if i == 0 else 'td'
        html_rows.append('<tr>' + ''.join(f'<{tag}>{_format_cell(_inline(c))}</{tag}>' for c in cells) + '</tr>')
    # 引用编号索引表（表头=编号|文献|出处）统一固定列宽比例
    if first_cells and len(first_cells) == 3 and first_cells[0] == '编号' and first_cells[1] == '文献':
        ref_class = ' class="ref-table"'
    return f'<table{ref_class}><thead>' + html_rows[0] + '</thead><tbody>' + ''.join(html_rows[1:]) + '</tbody></table>'

def _is_flow_block(code):
    """判断代码块是否为流程图，满足其一即转 flow：
    1. 含框线字符 (│ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ─) 或 【】 阶段标题（结构化框图）
    2. 含 ↓↑→▼ 箭头且箭头行 >= 2（单向链，如 正常执行 → 阻断 → 锁文件）
    目录树（├── 无箭头）与代码示例（= { } import 等）保持 pre。
    """
    lines = [l for l in code.split('\n') if l.strip()]
    if len(lines) < 2:
        return False
    box_chars = '│┌┐└┘├┤┬┴─'
    has_box = any(any(c in l for c in box_chars) for l in lines)
    has_phase = any('【' in l and '】' in l for l in lines)
    if has_box or has_phase:
        return True
    # 单向链：含 ↓↑→▼ 的行 >= 2
    arrow_lines = sum(1 for l in lines if any(c in l for c in '↓↑→▼'))
    if arrow_lines >= 2:
        # 排除纯代码（含 = { } import def 等代码特征）
        code_like = sum(1 for l in lines if any(k in l for k in ('=', '{', '}', 'import ', 'def ', 'print(', '()', 'return ')))
        if code_like <= len(lines) // 3:
            return True
    return False


def _inline_arrows(text):
    """将文本内所有方向箭头（→ ↓ ↑ ↔ ⇄ ▼ ◀ ▶）统一包成
    flow-inline-arrow span（蓝色加粗），与独立箭头视觉一致。"""
    return re.sub(r'([→↓↑↔⇄▼◀▶])', r'<span class="flow-inline-arrow">\1</span>', text)


def _split_chain_cell(text):
    """渲染单个链单元格（如 记住 → 合适引用 / （人形图书馆）→（画龙点睛））"""
    p1, p2 = _split_first_arrow(text)
    if p2 is not None:
        return f'{_inline_arrows(p1)} <span class="flow-inline-arrow">→</span> <span class="edge-fall">{_inline_arrows(p2)}</span>'
    return _inline_arrows(text)


def _is_chain_main(code):
    """判断是否为"主链 + 对齐注释"结构（运用图）：
    需多行（>=2 行）；第一行含 >=2 个 → 且箭头间隔小（连续链，无列分隔）。
    对比式（差距图）第一行箭头间隔大（>=4 空格列分隔）。
    单行链（编排链 → 遍历 → 执行）只有 1 行，不算主链式。"""
    lines = [l for l in code.split('\n') if l.strip()]
    if len(lines) < 2:
        return False
    first = lines[0]
    idxs = [m.start() for m in re.finditer(r'→', first)]
    if len(idxs) < 2:
        return False
    for i in range(len(idxs) - 1):
        if re.search(r'\s{4,}', first[idxs[i]:idxs[i+1]]):
            return False  # 有列分隔 = 对比式
    return True


def _chain_to_html(code):
    """主链 + 对齐注释 → HTML 横向链（每环节节点 = step + 注释在下方）。
    示例：运用 = 规划 → 执行 → 验证 → 承担
              ｜      ｜      ｜      ｜
             做判断  行动    闭环    负责
    语义：运用 = (规划 → 执行 → 验证 → 承担)，"运用 =" 是链标题，
    四个环节是链上节点，注释在环节下方。
    渲染：标题（flow-chain-title）+ 四个横向节点 + → 连接。"""
    lines = [l.rstrip() for l in code.split('\n') if l.strip()]
    lines = [re.sub(r'─+→', '→', l) for l in lines]
    chain = lines[0]
    # 等号前缀 = 链标题（运用 = 规划 → ... → 运用 是标题，规划→执行→验证→承担 是链）
    title = ''
    body = chain
    if '=' in chain:
        eq = chain.find('=')
        title = chain[:eq+1].strip()  # "运用 ="
        body = chain[eq+1:].strip()
    parts = [p.strip() for p in body.split('→') if p.strip()]
    # 注释行：跳过竖线对齐行，找空格分隔行
    notes = []
    for l in lines[1:]:
        if '｜' in l or '│' in l:
            continue
        segs = [p.strip() for p in re.split(r'\s{2,}', l) if p.strip()]
        if len(segs) >= 2:
            notes = segs
    n = max(len(parts), len(notes))
    out = ['<div class="flow-chain">']
    if title:
        out.append(f'<div class="flow-chain-title">{_inline_arrows(title)}</div>')
    for i in range(n):
        out.append('<div class="flow-cnode">')
        if i < len(parts):
            out.append(f'<div class="flow-step">{_split_chain_cell(parts[i])}</div>')
        if i < len(notes):
            out.append(f'<div class="flow-note">{_inline_arrows(notes[i])}</div>')
        out.append('</div>')
        if i < n - 1:
            out.append('<div class="flow-carr">→</div>')
    out.append('</div>')
    return '\n'.join(out)


def _multi_col_to_html(code):
    """并排多列图 → HTML：
    - 主链式（运用 = 规划 → 执行 → 验证 → 承担 + 注释对齐）→ 横向链
    - 对比式（记住→合适引用 | 说出→运用 两列）→ flex 双列
    按 >=4 连续空格切成列，逐列垂直组装，保留多列结构。"""
    if _is_chain_main(code):
        return _chain_to_html(code)
    lines = [l.rstrip() for l in code.split('\n') if l.strip()]
    # 每行按列分隔切成 cells
    rows_cells = []
    for l in lines:
        # 先归一化长横线箭头
        l2 = re.sub(r'─+→', '→', l)
        l2 = re.sub(r'─+', '', l2)
        cells = [c.strip() for c in re.split(r'\s{4,}', l2) if c.strip()]
        rows_cells.append(cells)
    ncols = max(len(c) for c in rows_cells)
    out = ['<div class="flow-cols">']
    for c in range(ncols):
        out.append('<div class="flow-col">')
        for cells in rows_cells:
            if c < len(cells):
                cell = cells[c]
                # 注释行（含括号）→ edge；纯文本（差距 A）→ note；含 → → step
                if '→' in cell:
                    out.append(f'<div class="flow-step">{_split_chain_cell(cell)}</div>')
                elif '（' in cell or '(' in cell:
                    out.append(f'<div class="flow-edge">{_inline_arrows(cell)}</div>')
                else:
                    out.append(f'<div class="flow-note">{_inline_arrows(cell)}</div>')
        out.append('</div>')
    out.append('</div>')
    return '\n'.join(out)


def _is_multi_column(code):
    """检测并排多列布局：某行内两个箭头之间隔了 >=4 个连续空格
    （列分隔，如 记住→合适引用          说出→运用）。
    单行连续链（编排链 → 遍历 → 执行 → 下一轮）箭头间无大段空白，不算多列。"""
    lines = [l for l in code.split('\n') if l.strip()]
    if len(lines) < 2:  # 单行链不算多列
        return False
    for l in lines:
        idxs = [m.start() for m in re.finditer(r'[→↓]', l)]
        for i in range(len(idxs) - 1):
            gap = l[idxs[i]:idxs[i+1]]
            if re.search(r'\s{4,}', gap):  # 箭头间含 >=4 连续空格 = 列分隔
                return True
    return False


def _is_flow_block(code, lang=''):
    """判断代码块类型，三态：
    'flow'  - 未标注语言 + 含指向性符号 + 单列链 → 转 HTML 流程图
    'cols'  - 未标注语言 + 并排多列对比图 → 转 HTML 双列布局
    None    - 标注语言（代码）或无箭头 → 保持 <pre>
    """
    if lang:  # 显式标注语言 = 代码
        return None
    lines = [l for l in code.split('\n') if l.strip()]
    if not lines:
        return None
    dir_chars = '→↓↑↔⇄▼◀▶'
    if not any(any(c in l for c in dir_chars) for l in lines):
        return None
    if _is_multi_column(code):
        return 'cols'  # 并排多列（对比式）→ HTML 双列
    # 多行 + 第一行连续箭头主链 + 下方对齐注释 → 主链式 'cols'
    if _is_chain_main(code):
        return 'cols'
    return 'flow'


def _split_first_arrow(text):
    """按第一个 → 拆分，返回 (前段, 后段)，→ 被完整保留在中间。"""
    idx = text.find('→')
    if idx < 0:
        return text, None
    return text[:idx].strip(), text[idx+1:].strip()


def _flow_to_html(code):
    """将 ASCII 流程图代码块渲染为 HTML 流程容器。
    规则：
    - 跳过空行
    - 去框线装饰字符 (│ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ─)，保留实际文本
    - 【...】识别为阶段标题
    - ↓ ↑ → ▼ 仅含箭头字符的行识别为箭头
    - └─ / ├─ 等引导分支说明行识别为 flow-edge
    - 其他文本作为步骤卡片（按原缩进级别映射为 padding-left）
    """
    out = ['<div class="flow">']
    box_chars = '│｜┌┐└┘├┤┬┴─'  # 含半角 U+2502 与全角 U+FF5C 竖线
    arrow_chars_all = '↓↑→▼'

    for raw in code.split('\n'):
        # 0) 框线行预判：整行只由框线/箭头字符组成 → 连接线
        l_strip = raw.strip()
        if not l_strip:
            continue
        if all(c in box_chars + arrow_chars_all + ' ' for c in l_strip):
            # 纯框线（┌──┐ / └──┬──┘ / ──── / │ │）：丢弃或转箭头
            if any(c in l_strip for c in '┬┴▼↓↑'):
                out.append('<div class="flow-arrow">▼</div>' if '┬' in l_strip or '▼' in l_strip else '<div class="flow-arrow">↓</div>')
            continue
        # 0.2) 长横线箭头归一化：────→ ／ ────┬ 等 → 统一 →
        l_strip = re.sub(r'─+→', '→', l_strip)
        l_strip = re.sub(r'─+', '', l_strip)
        # 0.5) 分支前缀检测（├─ / └─ 引导的说明行，非纯框线）
        if l_strip.startswith('├─') or l_strip.startswith('└─'):
            content = l_strip[2:].strip(' -─│')
            if content:
                depth = (len(raw) - len(raw.lstrip())) // 2 * 14
                p1, p2 = _split_first_arrow(content)
                if p2 is not None:
                    out.append(f'<div class="flow-edge" style="margin-left:{depth}px">{_inline_arrows(p1)} <span class="flow-inline-arrow">→</span> <span class="edge-fall">{_inline_arrows(p2)}</span></div>')
                else:
                    out.append(f'<div class="flow-edge" style="margin-left:{depth}px">{content}</div>')
            continue
        # 1) 去前后空白
        l = raw.strip()
        if not l:
            continue
        # 2) 去框线装饰字符（首尾循环去除）
        l2 = l
        while l2 and l2[0] in box_chars + ' ':
            l2 = l2[1:]
        while l2 and l2[-1] in box_chars + ' ':
            l2 = l2[:-1]
        if not l2:
            continue
        # 3) 阶段标题
        if l2.startswith('【') and '】' in l2:
            phase = l2[l2.find('【'):l2.rfind('】')+1]
            out.append(f'<div class="flow-phase">{phase}</div>')
            continue
        # 4) 纯箭头/连接线行（剥框线后只剩箭头字符 → 箭头；只剩框线 → 丢弃）
        if all(c in box_chars + arrow_chars_all for c in l2):
            if any(c in l2 for c in arrow_chars_all):
                out.append(f'<div class="flow-arrow">{l2}</div>')
            continue
        # 5) 缩进级别
        leading = len(raw) - len(raw.lstrip())
        depth = (leading // 2) * 14
        # 5.5) 长横线箭头归一化（剥框线后）：────→ → →
        l2 = re.sub(r'─+→', '→', l2)
        l2 = re.sub(r'─+', '', l2)
        # 6) 行内箭头拆分（所有文本统一染色箭头）
        p1, p2 = _split_first_arrow(l2)
        if p2 is not None:
            out.append(f'<div class="flow-step" style="margin-left:{depth}px">{_inline_arrows(p1)} <span class="flow-inline-arrow">→</span> <span class="edge-fall">{_inline_arrows(p2)}</span></div>')
        else:
            out.append(f'<div class="flow-step" style="margin-left:{depth}px">{_inline_arrows(l2)}</div>')
    out.append('</div>')
    return '\n'.join(out)


def md_to_html(md_text):
    lines = md_text.split('\n')
    out = []
    i = 0
    n = len(lines)
    seq = 0
    while i < n:
        line = lines[i]
        # 代码块
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()  # ```python → 'python'；``` → ''
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            code_text = '\n'.join(buf)
            kind = _is_flow_block(code_text, lang)
            if kind == 'flow':
                out.append(_flow_to_html(code_text))
            elif kind == 'cols':
                out.append(_multi_col_to_html(code_text))
            else:
                out.append('<pre><code>' + html_mod.escape(code_text) + '</code></pre>')
            continue
        # 标题（带锚点 id，供目录跳转）
        m = re.match(r'^(#{1,4})\s+(.*)$', line)
        if m:
            level = len(m.group(1))
            seq += 1
            out.append(f'<h{level} id="h{seq}">{_inline(m.group(2))}</h{level}>')
            i += 1
            continue
        # 分隔线
        if re.match(r'^\s*---+\s*$', line):
            out.append('<hr/>')
            i += 1
            continue
        # 引用块
        if line.startswith('>'):
            buf = []
            while i < n and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('>').strip())
                i += 1
            out.append('<blockquote>' + _inline(' '.join(buf)) + '</blockquote>')
            continue
        # 表格（连续 | 行）
        if line.strip().startswith('|'):
            buf = [line]
            i += 1
            while i < n and lines[i].strip().startswith('|'):
                buf.append(lines[i]); i += 1
            out.append(_table(buf))
            continue
        # 无序列表
        if re.match(r'^\s*-\s+', line):
            buf = []
            while i < n and re.match(r'^\s*-\s+', lines[i]):
                buf.append(_inline(re.sub(r'^\s*-\s+', '', lines[i]))); i += 1
            out.append('<ul>' + ''.join(f'<li>{x}</li>' for x in buf) + '</ul>')
            continue
        # 有序列表
        if re.match(r'^\s*\d+\.\s+', line):
            buf = []
            while i < n and re.match(r'^\s*\d+\.\s+', lines[i]):
                buf.append(_inline(re.sub(r'^\s*\d+\.\s+', '', lines[i]))); i += 1
            out.append('<ol>' + ''.join(f'<li>{x}</li>' for x in buf) + '</ol>')
            continue
        # 空行
        if not line.strip():
            i += 1
            continue
        # 普通段落（合并到空行/块前）
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not lines[i].startswith(('#', '>', '|', '-', '```')) \
              and not re.match(r'^\s*\d+\.\s+', lines[i]) and not re.match(r'^\s*---+\s*$', lines[i]):
            buf.append(lines[i]); i += 1
        out.append('<p>' + _inline(' '.join(buf)) + '</p>')
    return '\n'.join(out)

CSS = """
:root { color-scheme: light dark; }
body { font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
       max-width: 780px; margin: 0 auto; padding: 2rem 1.2rem 4rem;
       line-height: 1.8; font-size: 16px; }
h1 { font-size: 1.7rem; border-bottom: 2px solid #ccc; padding-bottom: .4rem; margin-top: 2.5rem; }
h2 { font-size: 1.4rem; border-bottom: 1px solid #ddd; padding-bottom: .3rem; margin-top: 2rem; }
h3 { font-size: 1.15rem; margin-top: 1.5rem; }
h4 { font-size: 1rem; }
blockquote { border-left: 4px solid #999; margin: 1rem 0; padding: .4rem 1rem;
             background: rgba(128,128,128,.08); color: #666; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .92rem;
        table-layout: auto; }
th, td { border: 1px solid #bbb; padding: .4rem .6rem; text-align: left;
         word-break: keep-all; overflow-wrap: break-word; vertical-align: top; }
th { background: rgba(128,128,128,.12); }
/* 引用编号索引表：三列固定列宽比例（编号≈6字符 / 文献 / 出处），与全局表格同宽 */
table.ref-table { table-layout: fixed; }
table.ref-table th:nth-child(1), table.ref-table td:nth-child(1) { width: 8%; }
table.ref-table th:nth-child(2), table.ref-table td:nth-child(2) { width: 47%; }
table.ref-table th:nth-child(3), table.ref-table td:nth-child(3) { width: 45%; }
/* 引用索引表内长文件名才允许任意断行 */
table.ref-table th, table.ref-table td { overflow-wrap: anywhere; }
/* 表格内多段文本（<br> 分隔）每段独立，保证一个原子信息不会被列宽拆字 */
table td .ref-piece, table th .ref-piece {
  display: block;
  white-space: normal;
  word-break: keep-all;
  overflow-wrap: break-word;
  line-height: 1.7;
}
pre { background: rgba(128,128,128,.1); padding: .8rem; border-radius: 6px;
      overflow-x: auto; font-size: .88rem; }
code { background: rgba(128,128,128,.12); padding: .1em .35em; border-radius: 3px; font-size: .9em; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 2rem 0; }
a { color: #2a6fd6; text-decoration: none; }
a:hover { text-decoration: underline; }
/* 流程图 */
.flow { margin: 1rem 0; padding: .9rem 1.1rem;
        background: rgba(128,128,128,.06);
        border: 1px solid rgba(128,128,128,.3);
        border-radius: 10px; }
.flow-phase { font-weight: bold; color: #2a6fd6; margin: .6rem 0 .2rem;
              font-size: 1.02em; }
.flow-step { background: rgba(128,128,128,.08); border: 1px solid #ccc;
             border-radius: 6px; padding: .3rem .7rem; margin: .25rem 0;
             line-height: 1.6; }
.flow-edge { color: #555; padding: .15rem 0 .15rem 1.4rem; font-size: .92em;
             line-height: 1.5; }
.flow-note { color: #777; font-size: .88em; padding: .15rem 0; text-align: center; }
/* 主链式对齐图（运用 = 规划 → 执行 → 验证 → 承担 + 注释） */
.flow-chain { display: flex; align-items: stretch; justify-content: center;
              flex-wrap: wrap; gap: .4rem; margin: 1rem 0;
              padding: .9rem 1.1rem; background: rgba(128,128,128,.06);
              border: 1px solid rgba(128,128,128,.3); border-radius: 10px; }
.flow-chain-title { align-self: center; font-weight: bold; color: #2a6fd6;
                    font-size: 1.05em; margin-right: .4rem;
                    padding: .3rem .6rem; background: rgba(42,111,214,.08);
                    border-radius: 6px; }
.flow-cnode { display: flex; flex-direction: column; justify-content: center;
              min-width: 5.5rem; text-align: center; }
.flow-cnode .flow-step { margin: 0; }
.flow-cnode .flow-note { margin-top: .2rem; }
.flow-carr { align-self: center; color: #2a6fd6; font-weight: bold; font-size: 1.15em;
             padding: 0 .15rem; }
/* 并排多列对比图（flex 双列） */
.flow-cols { display: flex; gap: 1.2rem; margin: 1rem 0;
             padding: .9rem 1.1rem; background: rgba(128,128,128,.06);
             border: 1px solid rgba(128,128,128,.3); border-radius: 10px; }
.flow-col { flex: 1; min-width: 0; }
.flow-col .flow-step { margin: .3rem 0; }
.flow-col .flow-edge { padding-left: 0; text-align: center; color: #777; }
@media (max-width: 600px) { .flow-cols { flex-direction: column; } }
.flow-edge .edge-fall { color: #2a6fd6; font-weight: bold; }
/* 行内箭头：与独立箭头同色同权重，视觉统一 */
.flow-inline-arrow { color: #2a6fd6; font-weight: bold; margin: 0 .25em; }
/* 箭头行：纯箭头无背景无边框（↓/▼ 独立行） */
.flow-arrow { color: #2a6fd6; text-align: center; line-height: 1.4;
              font-weight: bold; padding: .1rem 0; }
.flow-arrow::before { content: ""; }
.toc { background: rgba(128,128,128,.06); border: 1px solid #ddd; border-radius: 8px;
       padding: 1.2rem 1.4rem; margin: 1rem 0 2rem; }
.toc-title { font-size: 1.15rem; font-weight: bold; margin-bottom: .6rem; }
.toc a { display: block; padding: .18rem 0; color: #2a6fd6; text-decoration: none; }
.toc a:hover { text-decoration: underline; }
.toc a.toc-l2 { padding-left: 1.4rem; font-size: .92rem; color: #666; }
@media (max-width: 600px) { body { font-size: 15px; padding: 1rem .8rem 3rem; } table { font-size: .8rem; } }
@media (prefers-color-scheme: dark) {
  body { background: #1a1a1a; color: #ddd; }
  h1, h2 { border-color: #444; }
  blockquote { color: #aaa; background: rgba(255,255,255,.05); }
  th, td { border-color: #555; }
  a { color: #6ba4ff; }
  .toc { border-color: #444; background: rgba(255,255,255,.04); }
  .toc a.toc-l2 { color: #aaa; }
  .flow { border-color: #444; background: rgba(255,255,255,.04); }
  .flow-step { border-color: #444; background: rgba(255,255,255,.05); }
  .flow-edge { color: #999; }
  .flow-note { color: #888; }
  .flow-cols { border-color: #444; background: rgba(255,255,255,.04); }
  .flow-chain { border-color: #444; background: rgba(255,255,255,.04); }
  .flow-phase { color: #6ba4ff; }
}
"""

def build_toc(md_text):
    """目录：基于全文标题（h1/h2 两级），锚点与 md_to_html 的 h{seq} 对应。
    必须跳过代码块内的 # 行（md_to_html 代码块不生成锚点），保证序号严格一致。"""
    heads = []
    in_code = False
    for line in md_text.split('\n'):
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r'^(#{1,4})\s+(.*?)\s*$', line)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip()))
    if not heads:
        return ''
    items, seq = [], 0
    for level, text in heads:
        seq += 1  # 与 md_to_html 标题锚点序号严格一致
        if level > 2:
            continue
        cls = 'toc-l1' if level == 1 else 'toc-l2'
        items.append(f'<a class="{cls}" href="#h{seq}">{html_mod.escape(re.sub(r"[`*]", "", text))}</a>')
    return ('<div class="toc"><div class="toc-title">目录</div>' + ''.join(items) + '</div>')

def wrap_document(title, body_html):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html_mod.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{body_html}
</body>
</html>'''

def convert(md_text, title='我思故我写'):
    body = md_to_html(md_text)
    toc = build_toc(md_text)
    return wrap_document(title, toc + body)
