#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整修复 batch_index.py 的缩进问题"""
import pathlib

p = pathlib.Path('scripts/batch_index.py')
lines = p.read_text(encoding='utf-8').splitlines(keepends=True)

# 修复第 136 行：async with 缩进
if 'async with db_manager.session() as session:' in lines[135]:
    lines[135] = '        async with db_manager.session() as session:\n'

# 修复 137-146 行：session 内的代码缩进（应该是 12 个空格）
for i in range(136, 146):
    if lines[i].strip():
        # 移除所有前导空格，然后添加正确的缩进
        lines[i] = '            ' + lines[i].lstrip()

# 修复第 147 行：count += 1 应该在 for 循环内（8个空格）
if 'count += 1' in lines[146]:
    lines[146] = '            count += 1\n'

p.write_text(''.join(lines), encoding='utf-8')
print('✅ 缩进已修复')
