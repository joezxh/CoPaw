"""
Fix: Assign admin role to admin user
Run this script to fix the missing role assignment for the admin user.
"""
import asyncio
import uuid
from sqlalchemy import text
from copaw.db.postgresql import get_database_manager

async def fix_admin_role():
    """Assign admin role to admin user if not already assigned."""
    manager = get_database_manager()
    
    async with manager.session() as session:
        try:
            # Step 1: Get admin user ID
            result = await session.execute(
                text("SELECT id FROM sys_users WHERE username = 'admin'")
            )
            admin_user = result.scalar()
            
            if not admin_user:
                print("❌ Admin user not found!")
                return False
            
            print(f"✓ Found admin user: {admin_user}")
            
            # Step 2: Check if admin role exists
            result = await session.execute(
                text("SELECT id FROM sys_roles WHERE name = 'admin'")
            )
            admin_role = result.scalar()
            
            if not admin_role:
                # Create admin role
                admin_role = str(uuid.uuid4())
                await session.execute(text("""
                    INSERT INTO sys_roles (id, name, description, level, is_system_role, tenant_id, created_at, updated_at)
                    VALUES (:role_id, 'admin', 'System Administrator', 0, true, 'default-tenant', NOW(), NOW())
                """), {'role_id': admin_role})
                print(f"✓ Created admin role: {admin_role}")
            else:
                print(f"✓ Admin role exists: {admin_role}")
            
            # Step 3: Check if admin user already has admin role
            result = await session.execute(text("""
                SELECT 1 FROM sys_user_roles 
                WHERE user_id = :user_id AND role_id = :role_id
            """), {'user_id': str(admin_user), 'role_id': admin_role})
            
            if result.scalar():
                print("✓ Admin user already has admin role")
            else:
                # Assign admin role to admin user
                await session.execute(text("""
                    INSERT INTO sys_user_roles (user_id, role_id, assigned_at, tenant_id)
                    VALUES (:user_id, :role_id, NOW(), 'default-tenant')
                """), {
                    'user_id': str(admin_user),
                    'role_id': admin_role
                })
                print("✓ Assigned admin role to admin user")
            
            await session.commit()
            print("\n✅ Role assignment completed successfully!")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(fix_admin_role())
    exit(0 if success else 1)
