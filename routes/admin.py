from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from routes.auth import get_current_user
from models import *

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class UserList(BaseModel):
    id: int
    name: str
    email: str
    phoneNumber: Optional[str] = None
    profilePic: Optional[str] = None
    role: str
    status: bool
    isVerified: bool
    createdAt: datetime
    updatedAt: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    profilePic: Optional[str] = None
    status: Optional[bool] = None


def admin_required(localization, user):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=localization.gettext("admin_required"),
        )


@router.get("/users", response_model=List[UserList])
async def read_users(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    user_id: int = None,
    page: int = 1,
    page_size: int = 10,
):
    localization = request.state.localization
    admin_required(localization, user)

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        return [user]

    query = db.query(User).order_by(User.id.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    users = query.all()

    return [
        UserList(
            id=user.id,
            name=user.name,
            email=user.email,
            phoneNumber=user.phoneNumber,
            profilePic=user.profilePic,
            role=user.role,
            status=user.status,
            isVerified=user.isVerified,
            createdAt=user.createdAt,
            updatedAt=user.updatedAt,
        )
        for user in users
    ]


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    db: db_dependency,
    cur_user: user_dependency,
    user_update: UserUpdate,
):
    localization = request.state.localization
    admin_required(localization, cur_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("user_not_found"),
        )
    if user_update.phoneNumber:
        phone_taken = (
            db.query(User).filter(User.phoneNumber == user_update.phoneNumber).first()
        )

        if phone_taken and phone_taken.id != cur_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is already taken by another user.",
            )

    if user_update.name:
        user.name = user_update.name
    if user_update.email:
        user.email = user_update.email
    if user_update.phoneNumber:
        user.phoneNumber = user_update.phoneNumber
    if user_update.profilePic:
        user.profilePic = user_update.profilePic
    if user_update.status is not None:
        user.status = user_update.status

    db.commit()
    db.refresh(user)

    return user


@router.get("/orders")
async def get_all_orders(
    request: Request,
    db: db_dependency,
    user: user_dependency,
    order_id: int = None,
    page: int = 1,
    page_size: int = 10,
):
    localization = request.state.localization
    admin_required(localization, user)
    if order_id:
        orders = db.query(Order).filter(Order.id == order_id).first()
        if orders is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=localization.gettext("order_not_found"),
            )
        return orders

    order_count = db.query(Order).count()
    if order_count > 0:
        query = db.query(Order)
        query = query.order_by(Order.id.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        return query.all()

    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=localization.gettext("order_not_found")
        )
