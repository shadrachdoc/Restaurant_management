#!/usr/bin/env python3
"""
Script to fix admin user role to master_admin
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services" / "auth-service"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User
from shared.models.enums import UserRole

DATABASE_URL = "postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"


async def fix_admin_role():
    """Change admin role to master_admin"""

    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Find admin user
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ Admin user not found!")
            return

        # Update role to master_admin
        admin.role = UserRole.MASTER_ADMIN
        await session.commit()

        print(f"✅ Role updated successfully!")
        print(f"\nUser: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role.value}")
        print(f"\nLogin credentials:")
        print(f"  Username: admin")
        print(f"  Password: Admin@123456")
        print(f"\nYou can now access the Master Admin Dashboard at:")
        print(f"  http://localhost:5173/master-admin")

    await engine.dispose()


if __name__ == "__main__":
    print("🔧 Fixing Admin User Role...\n")
    asyncio.run(fix_admin_role())
