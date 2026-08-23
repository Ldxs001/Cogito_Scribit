# -*- coding: utf-8 -*-
"""
《我思故我写》书稿拼接脚本
将书级组件 + 四部文章 + 结语 + 附录拼接为单一书稿 Markdown。
用法: python assemble.py [输出路径]
零依赖（标准库）。
"""
import sys, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 书的结构（顺序即书的顺序）
STRUCTURE = [
    ("frontmatter/00_版权页.md", "版权页"),
    ("frontmatter/00_序言.md", "序言"),
    ("frontmatter/00_阅读指南.md", "阅读指南"),
    ("part1_约束/00_导读.md", "第 I 部导读"),
    ("part1_约束/01_重型技能构建的方法论沉淀：抑制LLM执行偏差的硬约束架构.md", "第 I 部 · 01"),
    ("part1_约束/02_重型技能构建的方法论沉淀：LLM技能构建阶段的工程化契约范式.md", "第 I 部 · 02"),
    ("part1_约束/03_重型技能构建的方法论沉淀：递归自举的元验证范式.md", "第 I 部 · 03"),
    ("part1_约束/04_重型技能构建的方法论沉淀：技能流水线编排范式.md", "第 I 部 · 04"),
    ("part1_约束/05_编排智能体 (Orchestrator)构建的方法论沉淀：链驱动Pipeline编排范式.md", "第 I 部 · 05"),
    ("part1_约束/06_领域智能体 (Domain Agent)构建的方法论沉淀：本地知识库智能体的自洽范式.md", "第 I 部 · 06"),
    ("part1_约束/07_重型技能构建的方法论沉淀：架构的减法与约束的加法——四条原则的元逻辑.md", "第 I 部 · 07"),
    ("part2_协作/00_导读.md", "第 II 部导读"),
    ("part2_协作/08_智能体协作构建的方法论沉淀：回到当下——有限决策范式的三体印证.md", "第 II 部 · 08"),
    ("part2_协作/08a_智能体协作构建的方法论沉淀：前置规范大于后置验证——最小尝试次数的分工与监督范式.md", "第 II 部 · 08a"),
    ("part2_协作/08b_智能体协作构建的方法论沉淀：填空的边界——空的收束、U型注意力与验证的分工.md", "第 II 部 · 08b"),
    ("part2_协作/08c_智能体协作构建的方法论沉淀：槽位的减法——三种场景的幻觉治理路径与四个论断.md", "第 II 部 · 08c"),
    ("part3_边界/00_导读.md", "第 III 部导读"),
    ("part3_边界/09_方法论体系构建的沉淀：穷举的宿命——稳定与随机的悖论.md", "第 III 部 · 09"),
    ("part3_边界/09a_方法论体系构建的沉淀：探测的边界——RAG检索鲁棒性的取舍范式.md", "第 III 部 · 09a"),
    ("part3_边界/09b_方法论体系构建的沉淀：配置推动的穷举一致性——统一推动点位与误差的哲学.md", "第 III 部 · 09b"),
    ("part3_边界/09c_方法论体系构建的沉淀：天然不对等与噪音抑制——语义匹配范式的不对等困境与推理免疫.md", "第 III 部 · 09c"),
    ("part3_边界/09d_方法论体系构建的沉淀：细碎处理与区域重构的成本切割——颗粒度与对齐的悖论.md", "第 III 部 · 09d"),
    ("part3_边界/09e_方法论体系构建的沉淀：提示词拉扯的边界——概率曲线的形状工程与定性精度的空耗.md", "第 III 部 · 09e"),
    ("part4_重估/00_导读.md", "第 IV 部导读"),
    ("part4_重估/10_认知重估的方法论沉淀：判断的让渡与翻译的打通——两种力气活的终结.md", "第 IV 部 · 10"),
    ("part4_重估/10a_认知重估的方法论沉淀：割圆术的边界——伦理牢笼与AI的宿命.md", "第 IV 部 · 10a"),
    ("part4_重估/10b_认知重估的方法论沉淀：语言被抹平——贫瘠的土地上能否开出鲜艳的花？.md", "第 IV 部 · 10b"),
    ("99_结语.md", "结语"),
    ("appendix/术语表.md", "附录 A 术语表"),
    ("appendix/工具索引.md", "附录 B 工具索引"),
    ("appendix/参考文献.md", "附录 C 参考文献"),
    ("appendix/方法论地图.md", "附录 D 方法论地图"),
    ("appendix/提示词示例.md", "附录 E 提示词示例"),
]

def strip_spdx(text):
    """剥离 SPDX 头（HTML 注释块），保留正文"""
    return re.sub(r'<!--.*?-->', '', text, flags=re.S).lstrip('\n')

def assemble():
    parts = []
    for rel, _label in STRUCTURE:
        path = os.path.join(ROOT, rel)
        with io.open(path, encoding='utf-8') as f:
            text = f.read()
        body = strip_spdx(text).strip()
        parts.append(body)
    return '\n\n---\n\n'.join(parts)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'output', '全书.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    book = assemble()
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(book)
    print(f'书稿已拼接: {out}（{len(book):,} 字符，{len(STRUCTURE)} 个部分）')

if __name__ == '__main__':
    main()
