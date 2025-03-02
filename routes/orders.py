from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from routes.auth import get_current_user
from models import Cart, Order, OrderDetail, Product

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=5, max_length=500)


@router.get("/")
async def get_orders(
    request: Request, db: db_dependency, user: user_dependency, order_id: int = None
):
    localization = request.state.localization
    if order_id:
        orders = db.query(Order).filter(Order.id == order_id).first()
        if orders is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=localization.gettext("order_not_found"),
            )
        return orders

    orders = db.query(Order).filter(Order.userId == user["id"]).all()
    if orders:
        return orders
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=localization.gettext("order_not_found")
        )


@router.get("/order_details/{id}")
async def get_order_details(
    id: int,
    request: Request,
    db: db_dependency,
    user: user_dependency,
):
    localization = request.state.localization
    order_details = db.query(OrderDetail).filter(OrderDetail.orderId == id).all()
    if order_details != None:
        return order_details
    else:
        raise HTTPException(
            status_code=404, detail=localization.gettext("order_not_found")
        )


@router.post("/confirm_order")
async def confirm_order(
    request: Request, db: db_dependency, order_data: OrderCreate, user: user_dependency
):
    localization = request.state.localization

    cart_items = db.query(Cart).filter(Cart.userId == user["id"]).all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=localization.gettext("cart_empty"),
        )

    total_amount = 0
    order_details = []

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.productId).first()
        # Check for product existence and sufficient stock
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=localization.gettext("product_not_found"),
            )
        if product.stockQuantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=localization.gettext("insufficient_stock").format(product.name),
            )
        subtotal = float(product.price * item.quantity)
        total_amount += subtotal

        order_details.append(
            OrderDetail(
                productId=item.productId,
                quantity=item.quantity,
                price=product.price,
                discount=0,
            )
        )

    try:
        new_order = Order(
            userId=user["id"],
            totalAmount=total_amount,
            shippingAddress=order_data.shipping_address,
            status=True,
            orderStatus="pending",
            paymentStatus="pending",
        )
        db.add(new_order)
        db.flush()  # Assign an order ID to new_order

        for detail in order_details:
            detail.orderId = new_order.id
            db.add(detail)

        db.query(Cart).filter(Cart.userId == user["id"]).delete()

        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.productId).first()
            product.stockQuantity -= item.quantity

        db.commit()
        db.refresh(new_order)

        return new_order

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/update_status/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_order_status(
    request: Request,
    order_id: int,
    status: str,
    db: db_dependency,
    user: user_dependency,
):
    localization = request.state.localization
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(
            status_code=404, detail=localization.gettext("order_not_found")
        )
    if order.userId != user["id"] and user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to update this order"
        )

    if status not in ["pending", "shipped", "delivered", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    order.orderStatus = status
    db.commit()
    return {"message": localization.gettext("order_status_update_success")}


@router.put("/update_payment/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_payment_status(
    order_id: int,
    payment_status: str,
    db: db_dependency,
    user: user_dependency,
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.userId != user["id"] and user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to update this order"
        )

    if payment_status not in ["pending", "paid", "failed", "refunded"]:
        raise HTTPException(status_code=400, detail="Invalid payment status")

    order.paymentStatus = payment_status
    db.commit()
    return {"message": "Payment status updated successfully"}
