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

def _table(rows):
    """表格：rows = 分割后的行列表"""
    # 过滤分隔行（|------|、|:---:| 等整行连字符/冒号/竖线形式）
    sep_re = re.compile(r'^\s*\|?[\s:|-]+\|?\s*$')
    body = [r for r in rows if not sep_re.match(r)]
    if not body:
        return ''
    html_rows = []
    for i, r in enumerate(body):
        cells = [c.strip() for c in r.strip().strip('|').split('|')]
        tag = 'th' if i == 0 else 'td'
        html_rows.append('<tr>' + ''.join(f'<{tag}>{_inline(c)}</{tag}>' for c in cells) + '</tr>')
    return '<table><thead>' + html_rows[0] + '</thead><tbody>' + ''.join(html_rows[1:]) + '</tbody></table>'

def _is_flow_block(code):
    """判断代码块是否为流程图：含 ↓ / → 流程箭头，且行数 >= 3"""
    lines = [l for l in code.split('\n') if l.strip()]
    if len(lines) < 3:
        return False
    arrow_count = sum(1 for l in lines if any(c in l for c in '↓↑→'))
    return arrow_count >= 2


def _flow_to_html(code):
    """将 ASCII 流程图代码块渲染为 HTML 流程容器。
    每行去掉前导空白，按行渲染；箭头行作为连接线。
    """
    lines = [l.rstrip() for l in code.split('\n')]
    # 计算统一缩进（去掉共同前导空白）
    stripped = [l.strip() for l in lines if l.strip()]
    # 识别块级结构：步骤行（含文字）与箭头行
    out = ['<div class="flow">']
    for l in stripped:
        if not l:
            continue
        if any(c in l for c in '↓↑→'):
            # 箭头行
            for c in '↓↑→':
                if c in l:
                    arrow = c
                    rest = l.replace(c, '').strip(' -─|├└┌┐│')
                    if rest:
                        out.append(f'<div class="flow-edge">{arrow} {rest}</div>')
                    else:
                        out.append(f'<div class="flow-arrow">{arrow}</div>')
                    break
        else:
            # 步骤行（可能是标题/阶段/文本）
            l2 = l.strip('| ')
            if l2.startswith('【') and l2.endswith('】'):
                out.append(f'<div class="flow-phase">{l2}</div>')
            else:
                # 去框线装饰：│ ┌ ─ ┐ 等
                l3 = l2.strip('┌─┐└┘│├┤')
                if l3:
                    out.append(f'<div class="flow-step">{l3}</div>')
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
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            code_text = '\n'.join(buf)
            if _is_flow_block(code_text):
                out.append(_flow_to_html(code_text))
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
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .92rem; }
th, td { border: 1px solid #bbb; padding: .4rem .6rem; text-align: left;
         word-break: keep-all; overflow-wrap: anywhere; vertical-align: top; }
th { background: rgba(128,128,128,.12); }
pre { background: rgba(128,128,128,.1); padding: .8rem; border-radius: 6px;
      overflow-x: auto; font-size: .88rem; }
code { background: rgba(128,128,128,.12); padding: .1em .35em; border-radius: 3px; font-size: .9em; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 2rem 0; }
a { color: #2a6fd6; text-decoration: none; }
a:hover { text-decoration: underline; }
/* 流程图 */
.flow { margin: 1rem 0; padding: .4rem 0; }
.flow-phase { font-weight: bold; color: #2a6fd6; margin: .6rem 0 .2rem;
              font-size: 1.02em; }
.flow-step { background: rgba(128,128,128,.08); border: 1px solid #ccc;
             border-radius: 6px; padding: .3rem .7rem; margin: .25rem 0;
             line-height: 1.6; }
.flow-edge { color: #666; padding: .1rem 0 .1rem .4rem; font-size: .95em; }
.flow-arrow { color: #2a6fd6; text-align: center; line-height: 1.2;
              font-weight: bold; padding: .05rem 0; }
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
  .flow-step { border-color: #444; background: rgba(255,255,255,.05); }
  .flow-edge { color: #999; }
  .flow-phase { color: #6ba4ff; }
  .flow-arrow { color: #6ba4ff; }
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
