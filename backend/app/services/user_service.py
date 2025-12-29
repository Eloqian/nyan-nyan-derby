from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from typing import Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def create_user(self, username: str, password: str, email: str = None) -> User:
        hashed = pwd_context.hash(password)
        user = User(username=username, hashed_password=hashed, email=email)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
