from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.user_service import UserService
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    email: str = None

@router.post("/register", status_code=201)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    existing = await service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = await service.create_user(user_data.username, user_data.password, user_data.email)
    return {"id": str(user.id), "username": user.username}
