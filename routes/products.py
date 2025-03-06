from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from database import SessionLocal
from models import OrderDetail, Product, ProductImage
from routes.auth import get_current_user


router = APIRouter(prefix="/products", tags=["Products"])


class ProductList(BaseModel):
    id: int
    name: str
    price: float
    discount: Optional[int]
    categoryId: int
    rating: Optional[float]



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_required(user):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can perform"
        )


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProductList])
async def get_products_list(
    db: db_dependency,
    category: int = None,
    name: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rating: float = None,
    discount: int = None,
    sort_by: str = None,
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(Product)

    if category:
        query = query.filter(Product.categoryId == category)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if discount is not None:
        query = query.filter(Product.discount >= discount)
    if sort_by is not None:
        if sort_by == "price_low":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_high":
            query = query.order_by(Product.price.desc())
        elif sort_by == "name":
            query = query.order_by(Product.name.asc())
    query = query.filter(Product.isAvailable == True)
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    products = query.with_entities(
        Product.id,
        Product.name,
        Product.price,
        Product.discount,
        Product.categoryId,
        Product.rating,
    ).all()
    return products


@router.get("/{id}")
async def get_product_details(id: int, db: db_dependency, request: Request):
    localization = request.state.localization

    product = db.query(Product).filter(Product.id == id).first()
    if product:
        product_images = (
            db.query(ProductImage).filter(ProductImage.productId == id).all()
        )

        images = [image.imageUrl for image in product_images]

        product_details = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "discount": product.discount,
            "categoryId": product.categoryId,
            "rating": product.rating,
            "isAvailable": product.isAvailable,
            "imageUrl": product.productUrl,
            "images": images,
        }
        return product_details

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=localization.gettext("product_not_found"),
    )


@router.get(
    "/trending", status_code=status.HTTP_200_OK, response_model=List[ProductList]
)
async def get_trending_products(db: db_dependency, limit: int = 5):

    trending_products = (
        db.query(Product)
        .filter(Product.isAvailable == True)
        .order_by(Product.rating.desc())
        .limit(limit)
        .all()
    )
    return trending_products




@router.get("/product_images/{product_id}")
async def get_product_images(request: Request, db: db_dependency, product_id: int):
    localization = request.state.localization
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization.gettext("product_not_found"),
        )
    images = db.query(ProductImage).filter(ProductImage.productId == product_id).all()
    if images:
        return images
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=localization.gettext("product_images_not_found"),
    )

