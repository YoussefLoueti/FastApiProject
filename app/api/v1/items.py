from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.model.item import Item
from app.model.user import User
from app.schemas import ItemCreate, ItemResponse, ItemWithOwner, StandardResponse
from app.service.elasticsearch_service import search_items as es_search_items
from app.service.elasticsearch_service import index_item
from app.redis_client import redis_manager
import json

router = APIRouter()

@router.post("/users/{user_id}/items/", response_model=StandardResponse)
async def create_item(user_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="User not found", data=None)
    db_item = Item(
        title=item.title,
        description=item.description,
        price=item.price,
        owner_id=user_id,
        is_default=False,
        can_delete=True
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    await index_item(db_item)
    await redis_manager.delete("all_items")
    result = ItemResponse.model_validate(db_item).model_dump(mode='json')
    return StandardResponse(code=200, message="successful", data=result)

@router.get("/items/", response_model=StandardResponse)
async def get_items(db: Session = Depends(get_db)):
    cache_key = "all_items"
    cached = await redis_manager.get_json(cache_key)
    if cached:
        return StandardResponse(code=200, message="successful", data=cached)
    items = db.query(Item).filter(Item.deleted_at == None).all()
    item_data = [ItemResponse.model_validate(item).model_dump(mode='json') for item in items]
    await redis_manager.set_json(cache_key, item_data)
    return StandardResponse(code=200, message="successful", data=item_data)

@router.get("/items/deleted", response_model=StandardResponse)
def get_deleted_items(db: Session = Depends(get_db)):
    items = db.query(Item).filter(Item.deleted_at.is_not(None)).all()
    item_data = [ItemResponse.model_validate(item).model_dump(mode='json') for item in items]
    return StandardResponse(code=200, message="successful", data=item_data)

@router.get("/items/{item_id}", response_model=StandardResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id, Item.deleted_at.is_(None)).first()
    if not item:
        return StandardResponse(code=404, message="Item not found", data=None)
    return StandardResponse(code=200, message="successful", data=ItemWithOwner.model_validate(item).model_dump(mode='json'))

@router.get("/users/{user_id}/items/", response_model=StandardResponse)
def get_user_items(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="User not found", data=None)
    items = db.query(Item).filter(Item.owner_id == user_id, Item.deleted_at.is_(None)).all()
    item_data = [ItemResponse.model_validate(item).model_dump(mode='json') for item in items]
    return StandardResponse(code=200, message="successful", data=item_data)

@router.put("/items/{item_id}", response_model=StandardResponse)
async def update_item(item_id: int, item_update: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id, Item.deleted_at.is_(None)).first()
    if not db_item:
        return StandardResponse(code=404, message="Item not found", data=None)
    db_item.title = item_update.title
    db_item.description = item_update.description
    db_item.price = item_update.price
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    await redis_manager.delete("all_items")
    result = ItemResponse.model_validate(db_item).model_dump(mode='json')
    return StandardResponse(code=200, message="successful", data=result)

#  Soft delete
@router.delete("/items/{item_id}/soft", response_model=StandardResponse)
async def soft_delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return StandardResponse(code=404, message="Item not found", data=None)
    if not item.can_delete:
        return StandardResponse(code=403, message="This item cannot be deleted", data=None)
    item.deleted_at = datetime.utcnow()
    db.commit()
    await redis_manager.delete("all_items")
    item_data = ItemResponse.model_validate(item).model_dump(mode='json')
    return StandardResponse(code=200, message="Item soft-deleted successfully", data=item_data)

#  Hard delete
@router.delete("/items/{item_id}/hard", response_model=StandardResponse)
async def hard_delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return StandardResponse(code=404, message="Item not found", data=None)
    if not item.can_delete:
        return StandardResponse(code=403, message="This item cannot be deleted", data=None)
    if item.deleted_at is None:
        return StandardResponse(code=400, message="Item must be soft deleted before hard delete.", data=None)
    item_data = ItemResponse.model_validate(item).model_dump(mode='json')
    db.delete(item)
    db.commit()
    await redis_manager.delete("all_items")
    return StandardResponse(code=200, message="Item hard-deleted successfully", data=item_data)

#  Restore item
@router.put("/items/{item_id}/restore", response_model=StandardResponse)
async def restore_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item or not item.deleted_at:
        return StandardResponse(code=404, message="Item not found or not soft-deleted", data=None)
    item.deleted_at = None
    db.commit()
    await redis_manager.delete("all_items")
    return StandardResponse(code=200, message="successful", data=None)

@router.get("/items/search/", response_model=StandardResponse)
async def search_items(query: str):
    results = await es_search_items(query)
    return StandardResponse(code=200, message="successful", data=results)
