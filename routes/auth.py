from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, constr, validators
from typing import Optional, Annotated

from sqlalchemy import or_
from database import SessionLocal
from sqlalchemy.orm import Session
from models import *
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

load_dotenv()
router = APIRouter(prefix="/auth", tags=["auth"])
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class UserCreate(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role = Role.customer


def validation(user: UserCreate, db: db_dependency):
    existingUser = db.query(User).filter(User.email == user.email).first()
    if existingUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already in use!"
        )


def create_access_token(user: User):

    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
    }
    payload.update({"exp": datetime.now() + timedelta(minutes=60)})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: db_dependency):
    db.begin()
    try:
        validated = validation(user, db)
        if validated != None:
            return validation

        new_user = User(
            name=user.name,
            email=user.email,
            password=bcrypt_context.hash(user.password),
            role=user.role,
        )
        db.add(new_user)
        db.commit()
        return {"message": "User registered successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
async def login_user(
    db: db_dependency, data: dict = Depends(OAuth2PasswordRequestForm)
):
    user = (
        db.query(User)
        .filter(or_(User.email == data.username, User.phoneNumber == data.username))
        .first()
    )
    if user and bcrypt_context.verify(data.password, user.password):
        token = create_access_token(user)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
