"""
Simple script to link existing users with their restaurants
This fixes the bug where users created restaurants but their restaurant_id wasn't updated
"""
import asyncio
import asyncpg

# Database URL - both services use the same database
DATABASE_URL = "postgresql://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"


async def link_users_to_restaurants():
    """Link all restaurant_admin users without restaurant_id to their restaurants"""

    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Find all users without restaurant_id (excluding master_admin and customers)
        users = await conn.fetch("""
            SELECT id, username, email, role::text as role
            FROM users
            WHERE restaurant_id IS NULL
              AND role::text != 'master_admin'
              AND role::text != 'customer'
        """)

        if not users:
            print("✓ No users need to be linked!")
            return

        print(f"Found {len(users)} user(s) without restaurant_id:")
        for user in users:
            print(f"  - {user['username']} ({user['email']})")

        # Get the first restaurant
        restaurant = await conn.fetchrow("""
            SELECT id, name
            FROM restaurants
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if not restaurant:
            print("❌ No restaurant found to link to!")
            return

        print(f"\nLinking all users to restaurant: {restaurant['name']} (ID: {restaurant['id']})")

        # Update each user
        for user in users:
            await conn.execute("""
                UPDATE users
                SET restaurant_id = $1
                WHERE id = $2
            """, restaurant['id'], user['id'])
            print(f"  ✓ Linked {user['username']}")

        print(f"\n✓ Successfully linked {len(users)} user(s)!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(link_users_to_restaurants())
