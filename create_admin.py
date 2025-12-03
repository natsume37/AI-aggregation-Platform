import asyncio
from app.core.database import AsyncSessionLocal
from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        existing = await user_crud.get_by_username(db, "root")
        if existing:
            print("Admin user already exists. Updating...")
            existing.hashed_password = get_password_hash("root")
            existing.is_superuser = True
            existing.is_admin = True
            existing.must_change_password = True
            existing.is_active = True
            
            db.add(existing)
            await db.commit()
            print("Admin user updated: root / root")
            return

        user_in = UserCreate(
            username="root",
            email="1957074599",
            password="root", 
            is_superuser=True,
            is_active=True,
            is_admin=True,
            must_change_password=True
        )
        user = await user_crud.create(db, user_in)
        print(f"Admin created: {user.username} / root")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(create_admin())