from datetime import datetime, timedelta
import secrets
from typing import Annotated, List, Optional
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
    BackgroundTasks,
)
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from routes.auth import get_current_user
from models import User
from routes.auth import bcrypt_context
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
templates = Jinja2Templates(directory="./templates")

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_HOST_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD"),
    MAIL_FROM="userfastapi@gmail.com",
    MAIL_PORT=2525,
    MAIL_SERVER="sandbox.smtp.mailtrap.io",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class ForgotEmailSchema(BaseModel):
    email: List[EmailStr]


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


reset_tokens = {}


@router.post("/forgot_password")
async def forgot_password(
    email: EmailStr, request: Request, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = secrets.token_urlsafe(32)
    reset_tokens[reset_token] = {
        "email": email,
        "expires": datetime.now() + timedelta(hours=1),
    }

    reset_link = f"{request.base_url}users/reset-password/{reset_token}"

    html_content = f"Click the following link to reset your password: {reset_link}"

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html_content,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "Password reset email sent successfully"}


@router.get("/reset-password/{token}")
async def reset_password_get(token: str, request: Request):
    token_data = reset_tokens.get(token)
    if not token_data or token_data["expires"] < datetime.now():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    return templates.TemplateResponse(
        "reset_password.html", {"request": request, "token": token}
    )


@router.post("/reset-password")
async def reset_password_post(
    token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)
):
    token_data = reset_tokens.get(token)
    if not token_data or token_data["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = bcrypt_context.hash(new_password)
    db.commit()

    reset_tokens.pop(token, None)

    return {"message": "Password has been reset successfully"}
