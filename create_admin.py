import asyncio
from app.core.database import AsyncSessionLocal
from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


ADMIN_USERNAME = "root"
ADMIN_PASSWORD = "1234"


async def create_or_update_admin():
    async with AsyncSessionLocal() as db:
        # 查找 root 用户是否存在
        admin = await user_crud.get_by_username(db, ADMIN_USERNAME)

        hashed_pw = get_password_hash(ADMIN_PASSWORD)

        if admin:
            print("Admin user exists. Resetting password...")

            admin.hashed_password = hashed_pw
            admin.is_superuser = True
            admin.is_admin = True
            admin.is_active = True
            admin.must_change_password = False

            db.add(admin)
            await db.commit()

            print(f"Admin user updated: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
            return

        # 创建 root 用户
        admin_create = UserCreate(
            username=ADMIN_USERNAME,
            email="1957074599@qq.com",
            password=ADMIN_PASSWORD,
            is_superuser=True,
            is_active=True,
            is_admin=True,
            must_change_password=False,
        )

        admin = await user_crud.create(db, admin_create)
        await db.commit()

        print(f"Admin created: {admin.username} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(create_or_update_admin())
