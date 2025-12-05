"""
Script to link existing users with their restaurants
This fixes the bug where users created restaurants but their restaurant_id wasn't updated
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database URL
AUTH_DATABASE_URL = "postgresql+asyncpg://auth_admin:auth_pass_2024@localhost:5432/auth_db"
RESTAURANT_DATABASE_URL = "postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"

async def link_user_to_restaurant(username: str):
    """Link a user to their restaurant by username"""
    # Import models
    from services.auth_service.app.models import User
    from services.restaurant_service.app.models import Restaurant

    # Create engines
    auth_engine = create_async_engine(AUTH_DATABASE_URL, echo=False)
    restaurant_engine = create_async_engine(RESTAURANT_DATABASE_URL, echo=False)

    # Create sessions
    auth_session_maker = sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    restaurant_session_maker = sessionmaker(restaurant_engine, class_=AsyncSession, expire_on_commit=False)

    async with auth_session_maker() as auth_session, restaurant_session_maker() as restaurant_session:
        # Find user by username
        user_result = await auth_session.execute(
            select(User).where(User.username == username)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            print(f"❌ User '{username}' not found!")
            return

        print(f"✓ Found user: {user.username} (ID: {user.id})")
        print(f"  Current restaurant_id: {user.restaurant_id}")

        # Find all restaurants (in case there are multiple)
        restaurant_result = await restaurant_session.execute(
            select(Restaurant).order_by(Restaurant.created_at.desc())
        )
        restaurants = restaurant_result.scalars().all()

        if not restaurants:
            print("❌ No restaurants found in database!")
            return

        print(f"\n📋 Found {len(restaurants)} restaurant(s):")
        for i, restaurant in enumerate(restaurants, 1):
            print(f"  {i}. {restaurant.name} (ID: {restaurant.id})")

        # If only one restaurant, link automatically
        if len(restaurants) == 1:
            restaurant = restaurants[0]
            user.restaurant_id = restaurant.id
            await auth_session.commit()
            print(f"\n✓ Linked user '{username}' to restaurant '{restaurant.name}'")
            print(f"  Restaurant ID: {restaurant.id}")
        else:
            # Let user choose which restaurant
            print("\nMultiple restaurants found. Please choose:")
            choice = input("Enter restaurant number (or 'q' to quit): ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(restaurants):
                    restaurant = restaurants[idx]
                    user.restaurant_id = restaurant.id
                    await auth_session.commit()
                    print(f"\n✓ Linked user '{username}' to restaurant '{restaurant.name}'")
                    print(f"  Restaurant ID: {restaurant.id}")
                else:
                    print("❌ Invalid choice!")
            except ValueError:
                print("❌ Invalid input!")

    # Close engines
    await auth_engine.dispose()
    await restaurant_engine.dispose()


async def auto_link_all():
    """Automatically link all restaurant_admin users to the first available restaurant"""
    from services.auth_service.app.models import User
    from services.restaurant_service.app.models import Restaurant
    from shared.models.enums import UserRole

    # Create engines
    auth_engine = create_async_engine(AUTH_DATABASE_URL, echo=False)
    restaurant_engine = create_async_engine(RESTAURANT_DATABASE_URL, echo=False)

    # Create sessions
    auth_session_maker = sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    restaurant_session_maker = sessionmaker(restaurant_engine, class_=AsyncSession, expire_on_commit=False)

    async with auth_session_maker() as auth_session, restaurant_session_maker() as restaurant_session:
        # Find all restaurant_admin users without restaurant_id
        user_result = await auth_session.execute(
            select(User).where(
                User.role == UserRole.RESTAURANT_ADMIN,
                User.restaurant_id == None
            )
        )
        users = user_result.scalars().all()

        if not users:
            print("✓ No users need to be linked!")
            return

        print(f"Found {len(users)} user(s) without restaurant_id:")
        for user in users:
            print(f"  - {user.username} ({user.email})")

        # Get the first restaurant
        restaurant_result = await restaurant_session.execute(
            select(Restaurant).order_by(Restaurant.created_at.desc())
        )
        restaurant = restaurant_result.scalars().first()

        if not restaurant:
            print("❌ No restaurant found to link to!")
            return

        print(f"\nLinking all users to restaurant: {restaurant.name} (ID: {restaurant.id})")

        for user in users:
            user.restaurant_id = restaurant.id
            print(f"  ✓ Linked {user.username}")

        await auth_session.commit()
        print(f"\n✓ Successfully linked {len(users)} user(s)!")

    # Close engines
    await auth_engine.dispose()
    await restaurant_engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        asyncio.run(link_user_to_restaurant(username))
    else:
        print("No username provided. Auto-linking all restaurant_admin users...")
        asyncio.run(auto_link_all())
