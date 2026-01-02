#!/usr/bin/env python3
"""
Script to reset admin password in the restaurant database
"""
import sys
import asyncio
import asyncpg
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_admin_password():
    """Reset admin password to 'password'"""

    # Get database credentials from user
    db_host = input("Enter database host (default: localhost): ") or "localhost"
    db_port = input("Enter database port (default: 5432): ") or "5432"
    db_name = input("Enter database name (default: restaurant_db): ") or "restaurant_db"
    db_user = input("Enter database user (default: restaurant_admin): ") or "restaurant_admin"
    db_password = input("Enter database password: ")

    new_password = input("\nEnter new password for admin user (default: password): ") or "password"

    try:
        # Connect to database
        print(f"\nConnecting to database {db_name}...")
        conn = await asyncpg.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password
        )

        # Hash the new password
        hashed_password = pwd_context.hash(new_password)

        # Update admin user password
        result = await conn.execute(
            """
            UPDATE users
            SET hashed_password = $1
            WHERE username = 'admin'
            """,
            hashed_password
        )

        # Verify the update
        admin_user = await conn.fetchrow(
            "SELECT username, email, role FROM users WHERE username = 'admin'"
        )

        if admin_user:
            print(f"\n✅ Password successfully reset for user '{admin_user['username']}'")
            print(f"   Email: {admin_user['email']}")
            print(f"   Role: {admin_user['role']}")
            print(f"   New Password: {new_password}")
            print(f"\nYou can now login with:")
            print(f"   Username: admin")
            print(f"   Password: {new_password}")
        else:
            print("\n❌ Admin user not found in database")

        await conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Restaurant Management - Admin Password Reset")
    print("=" * 60)
    asyncio.run(reset_admin_password())
