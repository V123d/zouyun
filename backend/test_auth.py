import asyncio
from app.database import AsyncSessionLocal
from app.routers.auth_router import register_user
from app.schemas.user_schema import UserCreate

async def test():
    async with AsyncSessionLocal() as db:
        try:
            user_in = UserCreate(username="testuser", password="testpassword123")
            res = await register_user(user_in=user_in, db=db)
            print("Success", res.username)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())
