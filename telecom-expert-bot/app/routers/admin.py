from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.models.user import User, UserCreate, UserResponse, TokenResponse, LoginRequest, UserRole
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_master_role,
)
from app.db.database import get_db
from app.config import settings

router = APIRouter(tags=["auth & admin"])


@router.post("/auth/register", response_model=dict)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    user_resp = UserResponse.model_validate(user)
    return {"status": "success", "data": user_resp.model_dump(), "message": "User registered successfully"}


@router.post("/auth/login", response_model=dict)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    user_resp = UserResponse.model_validate(user)
    return {
        "status": "success",
        "data": {"access_token": token, "token_type": "bearer", "user": user_resp.model_dump()},
        "message": "Login successful",
    }


@router.get("/auth/me", response_model=dict)
async def get_me(current_user=Depends(get_current_user)):
    user_resp = UserResponse.model_validate(current_user)
    return {"status": "success", "data": user_resp.model_dump(), "message": "OK"}


@router.get("/admin/users", response_model=dict)
async def list_users(
    current_user=Depends(require_master_role),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {
        "status": "success",
        "data": [UserResponse.model_validate(u).model_dump() for u in users],
        "message": "OK",
    }


@router.delete("/admin/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user=Depends(require_master_role),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    return {"status": "success", "data": None, "message": "User deleted"}
