from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from app.database import get_db
from app.model.user import User
from app.schemas import UserCreate, UserResponse, UserWithItems, StandardResponse
from app.redis_client import redis_manager
import json

router = APIRouter()

@router.post("/users/", response_model=StandardResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        return StandardResponse(code=400, message="Email already registered", data=None)
    db_user = User(
        name=user.name,
        email=user.email,
        is_default=False,
        can_delete=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # 🔁 Update the cache after adding the user
    users = db.query(User).filter(User.deleted_at == None).all()
    user_data = [UserResponse.model_validate(u).model_dump(mode='json') for u in users]
    await redis_manager.set_json("all_users", user_data)
    result = UserResponse.model_validate(db_user).model_dump(mode='json')
    return StandardResponse(code=200, message="successful", data=result)

@router.get("/users/", response_model=StandardResponse)
async def get_users(db: Session = Depends(get_db)):
    cache_key = "all_users"
    cached = await redis_manager.get_json(cache_key)
    if cached:
        return StandardResponse(code=200, message="successful", data=cached)
    users = db.query(User).filter(User.deleted_at == None).all()
    user_data = [UserResponse.model_validate(u).model_dump(mode='json') for u in users]
    await redis_manager.set_json(cache_key, user_data)
    return StandardResponse(code=200, message="successful", data=user_data)

@router.get("/users/deleted", response_model=StandardResponse)
def get_soft_deleted_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.deleted_at.is_not(None)).all()
    user_data = [UserResponse.model_validate(u).model_dump(mode='json') for u in users]
    return StandardResponse(code=200, message="successful", data=user_data)

@router.get("/users/{user_id}", response_model=StandardResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        return StandardResponse(code=404, message="User not found", data=None)
    return StandardResponse(code=200, message="successful", data=UserWithItems.model_validate(user).model_dump(mode='json'))

@router.delete("/users/{user_id}/soft", response_model=StandardResponse)
async def soft_delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="User not found", data=None)
    if not user.can_delete:
        return StandardResponse(code=403, message="This user cannot be deleted", data=None)
    user.deleted_at = datetime.utcnow()
    db.commit()
    await redis_manager.delete("all_users")
    user_data = UserResponse.model_validate(user).model_dump(mode='json')
    return StandardResponse(code=200, message="User soft-deleted successfully", data=user_data)

@router.delete("/users/{user_id}/hard", response_model=StandardResponse)
async def hard_delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return StandardResponse(code=404, message="User not found", data=None)
        if not user.can_delete:
            return StandardResponse(code=403, message="This user cannot be deleted", data=None)
        if user.deleted_at is None:
            return StandardResponse(code=400, message="User must be soft deleted before hard delete.", data=None)
        user_data = UserResponse.model_validate(user).model_dump(mode='json')
        db.delete(user)
        db.commit()
        await redis_manager.delete("all_users")
        return StandardResponse(code=200, message="User hard-deleted successfully", data=user_data)
    except Exception as e:
        # Optionally log the error here
        return StandardResponse(code=500, message=f"Internal Server Error: {str(e)}", data=None)

@router.put("/users/{user_id}/restore", response_model=StandardResponse)
async def restore_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.deleted_at:
        return StandardResponse(code=404, message="User not found or not soft-deleted", data=None)
    user.deleted_at = None
    db.commit()
    await redis_manager.delete("all_users")
    return StandardResponse(code=200, message="successful", data=None)
