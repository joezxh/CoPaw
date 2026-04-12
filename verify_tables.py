#!/usr/bin/env python3
"""验证所有模型表名是否已正确更新"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from copaw.db.models import Base

# 获取所有表名
tables = list(Base.metadata.tables.keys())

print("=" * 60)
print("数据库表名验证")
print("=" * 60)

# 检查sys_前缀的表
sys_tables = sorted([t for t in tables if t.startswith('sys_')])
print(f"\n✓ 系统管理表 (sys_): {len(sys_tables)} 个")
for t in sys_tables:
    print(f"  - {t}")

# 检查ai_前缀的表
ai_tables = sorted([t for t in tables if t.startswith('ai_')])
print(f"\n✓ AI业务表 (ai_): {len(ai_tables)} 个")
for t in ai_tables:
    print(f"  - {t}")

# 检查是否有未加前缀的表
other_tables = [t for t in tables if not t.startswith(('sys_', 'ai_'))]
if other_tables:
    print(f"\n✗ 警告: 发现 {len(other_tables)} 个未加前缀的表:")
    for t in other_tables:
        print(f"  - {t}")
else:
    print(f"\n✓ 所有表都已正确添加前缀!")

print(f"\n总计: {len(tables)} 个表")
print("=" * 60)

# 验证关键表是否存在
required_sys_tables = [
    'sys_users', 'sys_roles', 'sys_permissions', 'sys_departments',
    'sys_user_sessions', 'sys_audit_logs', 'sys_tenants'
]

required_ai_tables = [
    'ai_tasks', 'ai_workflows', 'ai_dify_connectors'
]

print("\n关键表检查:")
all_ok = True
for table in required_sys_tables + required_ai_tables:
    if table in tables:
        print(f"  ✓ {table}")
    else:
        print(f"  ✗ {table} - 缺失!")
        all_ok = False

if all_ok:
    print("\n✓ 所有关键表都存在!")
else:
    print("\n✗ 有表缺失,请检查!")
    sys.exit(1)
