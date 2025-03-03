from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from routes.auth import get_current_user
from models import Order, OrderDetail, Review, Product
from routes.auth import bcrypt_context

router = APIRouter(prefix="/review_ratings", tags=["Review&Ratings"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class ReviewRequest(BaseModel):
    productId: int
    rating: float
    reviewText: str


@router.get("{product_id}")
async def get_review_ratings(product_id: int, db: db_dependency):
    reviews = db.query(Review).filter(Review.productId == product_id).all()
    return reviews


@router.post("/add_review&ratings")
async def add_review_ratings(
    request: Request, db: db_dependency, user: user_dependency, review: ReviewRequest
):
    db.begin()
    try:
        product = db.query(Product).filter(Product.id == review.productId).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        order = (
            db.query(OrderDetail)
            .join(Order)
            .filter(
                Order.userId == user["id"], OrderDetail.productId == review.productId
            )
            .first()
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You had not ordered this product so you are not allowed to give review.",
            )
        if review.rating < 1 or review.rating > 5:
            return "Rating should be between 0 and 5"

        new_review = Review(
            productId=review.productId,
            userId=user["id"],
            rating=round(review.rating, 1),
            reviewText=review.reviewText,
        )
        db.add(new_review)
        db.commit()
        await get_average_rating(db, review.productId)

        return "Review and rating added successfully."
    except:
        db.rollback()


async def get_average_rating(db: db_dependency, product_id: int):
    reviews = db.query(Review).filter(Review.productId == product_id).all()
    if reviews:
        total_rating = sum([i.rating for i in reviews])
        avg_rating = round(total_rating / len(reviews), 2)

        product = db.query(Product).filter(Product.id == product_id).first()
        product.rating = avg_rating
        db.commit()
