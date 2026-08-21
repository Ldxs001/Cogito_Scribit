# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
p = r'C:\Users\sm001\WorkBuddy\Cogito_Scribit\book\appendix\参考文献.md'
t = io.open(p, encoding='utf-8').read()

# 09e [2] 简化（T5 论文长出处 → 简洁标准格式）
old = 'KB「LLM奠基理论」`1910.10683v4`（T5 论文 *Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer*，Raffel et al., JMLR 21, 2020——参考文献中的 Hinton 蒸馏条目，FTS 检索实证）'
new = 'KB「LLM奠基理论」`1910.10683v4`（T5 论文原文，FTS 检索实证）'
print('匹配:', old in t)
t2 = t.replace(old, new)
print('替换生效:', t2 != t)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t2)