from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from routes.auth import get_current_user
from models import User
from routes.auth import bcrypt_context
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    profilePic: Optional[str] = None


class ChangePassword(BaseModel):
    oldPassword: str
    newPassword: str


class ResetPassword(BaseModel):
    email: EmailStr


@router.get("/profile")
async def get_user_profile(request: Request, db: db_dependency, user: user_dependency):
    localization = request.state.localization
    profile = db.query(User).filter(User.id == user["id"]).first()
    if profile:
        return profile
    return {"error": localization.gettext("user_not_found")}


@router.put("/update-profile", response_model=UserUpdate)
async def update_user_profile(
    user_data: UserUpdate, db: db_dependency, cur_user: user_dependency
):
    user = db.query(User).filter(User.id == cur_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_data.phoneNumber:
        phone_taken = (
            db.query(User).filter(User.phoneNumber == user_data.phoneNumber).first()
        )

        if phone_taken and phone_taken.id != cur_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is already taken by another user.",
            )

    if user_data.name:
        user.name = user_data.name
    if user_data.email:
        user.email = user_data.email
    if user_data.phoneNumber:
        user.phoneNumber = user_data.phoneNumber
    if user_data.profilePic:
        user.profilePic = user_data.profilePic

    db.commit()
    db.refresh(user)

    return user


@router.put("/change-password")
async def change_password(
    change_password_data: ChangePassword,
    db: db_dependency,
    user: user_dependency,
):
    user = db.query(User).filter(User.id == user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not bcrypt_context.verify(change_password_data.oldPassword, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect"
        )

    user.password = bcrypt_context.hash(change_password_data.newPassword)

    db.commit()
    db.refresh(user)

    return {"message": "Password updated successfully"}
