from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import Category

router = APIRouter(prefix="/categories", tags=["Category"])


class CategoryCreate(BaseModel):
    categoryName: str
    status: Optional[bool] = True


class CategoryUpdate(BaseModel):
    categoryName: Optional[str]
    status: Optional[bool]


class CategoryResponse(BaseModel):
    id: int
    categoryName: str
    status: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/")
async def get_all_category(db: db_dependency):
    return db.query(Category).all()


@router.get("/{id}")
async def get_category(db: db_dependency, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


@router.post("/add")
async def create_category(db: db_dependency, category: CategoryCreate):
    db_category = Category(
        categoryName=category.categoryName,
        status=category.status,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/update/{id}")
def update_category(db: db_dependency, category_id: int, category: CategoryUpdate):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category:
        if category.categoryName:
            db_category.categoryName = category.categoryName
        if category.status is not None:
            db_category.status = category.status
        db.commit()
        db.refresh(db_category)
    return db_category


@router.delete("/delete/{id}")
def delete_category(db: db_dependency, category_id: int):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category
