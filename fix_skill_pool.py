#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修改 _index_skills 方法：
从全局 working/skill_pool 目录扫描，而不是工作空间下
"""
import pathlib

p = pathlib.Path('scripts/batch_index.py')
c = p.read_text(encoding='utf-8')

# 替换 _index_skills 方法
old_method = '''    async def _index_skills(self, workspace_dir: Path) -> int:
        """索引Skill配置"""
        from copaw.db.models.storage_meta import SkillConfig
        from copaw.db.postgresql import get_database_manager

        skill_pool = workspace_dir / "skill_pool"
        if not skill_pool.exists():
            return 0

        # 确保工作空间记录存在
        workspace_uuid = await self._ensure_workspace_exists(workspace_dir.name)

        count = 0
        for skill_dir in skill_pool.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_json = skill_dir / "skill.json"
            if not skill_json.exists():
                continue

            with open(skill_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            from copaw.db.postgresql import get_database_manager

            db_manager = get_database_manager()
            async with db_manager.session() as session:
                skill = SkillConfig(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_uuid,
                    skill_name=data.get("name", skill_dir.name),
                    display_name=data.get("display_name"),
                    description=data.get("description"),
                    version=data.get("version", "1.0.0"),
                    source="local",
                )
                session.add(skill)
    
            count += 1

        return count'''

new_method = '''    async def _index_skills(self, workspace_dir: Path) -> int:
        """索引全局Skill配置"""
        from copaw.db.models.storage_meta import SkillConfig
        from copaw.db.postgresql import get_database_manager

        # 使用全局 skill_pool 目录
        skill_pool = Path("working/skill_pool")
        if not skill_pool.exists():
            return 0

        count = 0
        for skill_dir in skill_pool.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_json = skill_dir / "skill.json"
            if not skill_json.exists():
                continue

            with open(skill_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            db_manager = get_database_manager()
            async with db_manager.session() as session:
                skill = SkillConfig(
                    tenant_id=self.tenant_id,
                    skill_name=data.get("name", skill_dir.name),
                    display_name=data.get("display_name"),
                    description=data.get("description"),
                    version=data.get("version", "1.0.0"),
                    source="local",
                )
                session.add(skill)
    
            count += 1

        return count'''

c = c.replace(old_method, new_method)
p.write_text(c, encoding='utf-8')
print('✅ _index_skills 已修改为扫描全局 working/skill_pool 目录')
