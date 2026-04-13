import asyncio
from sqlalchemy import text
from copaw.db.postgresql import async_engine

async def check_table():
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_dify_connectors')"
            ))
            exists = result.scalar()
            if exists:
                print("✅ ai_dify_connectors 表存在")
            else:
                print("❌ ai_dify_connectors 表不存在，需要执行: alembic upgrade head")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
    finally:
        await async_engine.dispose()

asyncio.run(check_table())
