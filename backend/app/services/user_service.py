from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from typing import Optional
from app.core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def create_user(self, username: str, password: str, email: str = None) -> User:
        hashed = get_password_hash(password)
        user = User(username=username, hashed_password=hashed, email=email)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_password(self, user: User, new_password: str) -> User:
        user.hashed_password = get_password_hash(new_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
