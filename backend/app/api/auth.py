from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.user_service import UserService
from app.core.security import create_access_token, SECRET_KEY, ALGORITHM
from app.models.user import User
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class UserCreate(BaseModel):
    username: str
    password: str
    email: str = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_admin: bool = False

@router.post("/register", status_code=201, response_model=UserResponse)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    existing = await service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = await service.create_user(user_data.username, user_data.password, user_data.email)
    return UserResponse(id=str(user.id), username=user.username, email=user.email, is_admin=user.is_admin)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    user = await service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    service = UserService(session)
    user = await service.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(id=str(current_user.id), username=current_user.username, email=current_user.email, is_admin=current_user.is_admin)
