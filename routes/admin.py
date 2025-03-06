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


class ProductUpdate(BaseModel):
    id: int = Field(...)
    name: Optional[str] = None
    description: Optional[str] = None
    stockQuantity: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[int] = None
    categoryId: Optional[int] = None
    productUrl: Optional[str] = None
    isAvailable: Optional[bool] = None


class ProductImagesCreate(BaseModel):
    productId: int = Field(...)
    imageUrl: str = Field(..., min_length=5)


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


@router.post("/product", status_code=status.HTTP_201_CREATED)
async def add_new_product(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    product_name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    image_url: str = Form(default=None),
    discount: int = Form(...),
    is_available: bool = Form(...),
):
    localization = request.state.localization
    try:
        admin_required(localization, user)

        product = Product(
            name=product_name,
            categoryId=category_id,
            productUrl=image_url,
            description=description,
            stockQuantity=quantity,
            price=price,
            discount=discount,
            isAvailable=is_available,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return {"success": localization.gettext("product_added")}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{localization.gettext('failed_to_add_product')}: {str(e)}",
        )


@router.put("/product")
async def update_product(
    request: Request, db: db_dependency, product: ProductUpdate, user: user_dependency
):
    localization = request.state.localization
    admin_required(localization, user)

    data = db.query(Product).filter(Product.id == product.id).first()

    if data:
        if product.name != None:
            data.name = product.name
        if product.categoryId != None:
            data.categoryId = product.categoryId
        if product.productUrl != None:
            data.productUrl = product.productUrl
        if product.description != None:
            data.description = product.description
        if product.stockQuantity != None:
            data.stockQuantity = product.stockQuantity
        if product.price != None:
            data.price = product.price
        if product.discount != None:
            data.discount = product.discount
        if product.isAvailable != None:
            data.isAvailable = product.isAvailable

        db.add(data)
        db.commit()
        db.refresh(data)
        return {"success": localization.gettext("product_updated")}

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{localization.gettext('product_not_found')}",
        )


@router.delete("/product/{id}")
async def delete_product(
    request: Request, db: db_dependency, id: int, user: user_dependency
):
    localization = request.state.localization
    db.begin()
    try:
        admin_required(localization, user)
        data = db.query(Product).filter(Product.id == id).first()
        if data:
            order_details = (
                db.query(OrderDetail).filter(OrderDetail.productId == id).first()
            )
            if order_details:
                return {"error": localization.gettext("product_has_orders")}

            db.delete(data)
            db.commit()
            return {"success": localization.gettext("product_deleted")}
        else:
            return {"error": localization.gettext("product_not_found")}
    except Exception as e:
        db.rollback()
        return {"error": localization.gettext(f"{e}")}


@router.post("/product_images")
async def add_product_images(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    product_images: ProductImagesCreate,
):
    localization = request.state.localization
    admin_required(localization, user)
    product = db.query(Product).filter(Product.id == product_images.productId).first()
    if product:
        image = ProductImage(
            productId=product_images.productId, imageUrl=product_images.imageUrl
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return {"success": localization.gettext("product_image_add_success")}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("product_not_found"),
        )


@router.delete("/product_images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_images(
    image_id: int, request: Request, user: user_dependency, db: db_dependency
):
    admin_required(localization, user)
    localization = request.state.localization
    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if image:
        db.execute(text(f"delete from productImages where id={image.id}"))
        db.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("product_images_not_found"),
        )
