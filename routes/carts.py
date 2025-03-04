from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import or_, text, DateTime
from database import SessionLocal
from routes.auth import get_current_user
from models import Cart, Product

router = APIRouter(prefix="/cart", tags=["Carts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class CartItems(BaseModel):
    id: int
    productId: int
    userId: int
    name: str
    quantity: int
    price: float
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True


@router.get("/", response_model=List[CartItems])
async def get_cart(request: Request, db: db_dependency, user: user_dependency):
    cart_items = (
        db.query(Cart, Product.name, Product.price)
        .join(Product, Cart.productId == Product.id)
        .filter(Cart.userId == user["id"])
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Items are available in cart.",
        )

    response = [
        CartItems(
            id=cart_item.id,
            productId=cart_item.productId,
            userId=cart_item.userId,
            name=product_name,
            quantity=cart_item.quantity,
            price=product_price,
            createdAt=cart_item.createdAt,
            updatedAt=cart_item.updatedAt,
        )
        for cart_item, product_name, product_price in cart_items
    ]

    return response


@router.get("/add_product/{product_id}")
async def add_product_in_cart(
    request: Request, db: db_dependency, product_id: int, user: user_dependency
):
    db.begin()
    try:
        existing_cart_item = (
            db.query(Cart)
            .filter(Cart.userId == user["id"], Cart.productId == product_id)
            .first()
        )
        localization = request.state.localization
        if existing_cart_item:
            existing_cart_item.quantity += 1
            db.commit()
            db.refresh(existing_cart_item)
            return {
                "message": localization.gettext("cart_updated"),
                "cart_item": existing_cart_item,
            }
        else:
            new_cart_item = Cart(userId=user["id"], productId=product_id, quantity=1)
            db.add(new_cart_item)
            db.commit()
            db.refresh(new_cart_item)
            return {
                "message": localization.gettext("added_to_cart"),
                "cart_item": new_cart_item,
            }
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("failed_to_add_in_cart"),
        )


@router.delete("/remove/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_from_cart(
    cart_id: int, request: Request, db: db_dependency, user: user_dependency
):
    localization = request.state.localization
    db.begin()
    user_id = user["id"]
    try:
        cart_item = db.execute(
            text(f"select * from carts where userId={user_id} and id={cart_id}")
        )
        if cart_item:
            db.execute(text(f"delete from carts where id ={cart_id}"))
            db.commit()
            return {"message": localization.gettext("removed_from_cart")}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=localization.gettext("product_not_found_in_cart"),
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            # detail=localization.gettext("failed_to_remove_from_cart"),
            detail=f"{e}",
        )


@router.put("/decrease_qty/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def decrease_product_quantity(
    request: Request, cart_id: int, db: db_dependency, user: user_dependency
):
    localization = request.state.localization
    cart_item = db.query(Cart).filter(Cart.id == cart_id).first()
    if cart_item and cart_item.userId == user["id"]:
        if (cart_item.quantity - 1) < 1:
            db.execute(text(f"delete from carts where id ={cart_id}"))
            db.commit()
        else:
            cart_item.quantity = cart_item.quantity - 1
            db.commit()
            return {
                "message": localization.gettext("decrease_product_cart_quantity"),
                "item": cart_item,
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("product_not_found_in_cart"),
        )
