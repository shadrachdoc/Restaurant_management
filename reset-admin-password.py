#!/usr/bin/env python3
"""
Script to reset the master admin password
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import from the correct paths
sys.path.insert(0, str(project_root / "services" / "auth-service"))
from app.models import User
from app.security import hash_password

DATABASE_URL = "postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"


async def reset_admin_password():
    """Reset admin password to default"""

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
            print("\nCreating new admin user...")

            # Create new admin
            new_password = "Admin@123456"
            hashed_pw = hash_password(new_password)

            from shared.models.enums import UserRole
            admin = User(
                username="admin",
                email="admin@restaurant.com",
                hashed_password=hashed_pw,
                full_name="System Administrator",
                role=UserRole.MASTER_ADMIN,
                is_active=True,
                is_verified=True
            )
            session.add(admin)
            await session.commit()

            print(f"✅ Admin user created!")
        else:
            # Reset password
            new_password = "Admin@123456"
            admin.hashed_password = hash_password(new_password)
            admin.is_active = True  # Ensure account is active
            await session.commit()

            print(f"✅ Password reset successfully for user: {admin.username}")

        print("\nLogin credentials:")
        print(f"  Username: admin")
        print(f"  Password: {new_password}")
        print(f"\nRole: {admin.role.value if hasattr(admin.role, 'value') else admin.role}")
        print(f"Email: {admin.email}")
        print(f"\nAccess the application at: http://localhost:5173/login")

    await engine.dispose()


if __name__ == "__main__":
    print("🔐 Resetting Master Admin Password...\n")
    asyncio.run(reset_admin_password())
