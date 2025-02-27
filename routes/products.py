from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal
from models import Product


router = APIRouter(prefix="/products", tags=["Products"])


class ProductList(BaseModel):
    id: int
    name: str
    price: float
    discount: Optional[int]
    categoryId: int
    rating: Optional[float]


class ProductUpdate(BaseModel):
    id: int = Field(...)
    name: Optional[str] = None
    description: Optional[str] = None
    stockQuantity: Optional[str] = None
    price: Optional[float] = None
    discount: Optional[int] = None
    categoryId: Optional[int] = None
    productUrl: Optional[str] = None
    isAvailable: Optional[bool] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


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

    products = query.with_entities(
        Product.id,
        Product.name,
        Product.price,
        Product.discount,
        Product.categoryId,
        Product.rating,
    ).all()
    return products


@router.get("/products/{id}")
async def get_product(id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == id).first()
    if product:
        return product
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product is not available!"
    )


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_new_product(
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
    try:
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
        return {"success": "product added Successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            # detail=f"Failed to add product: {str(e)}",
            detail="Failed to add product: Check your data.",
        )


@router.put("/update")
async def update_product(db: db_dependency, product: ProductUpdate):
    db.begin()
    try:

        if product.id:
            data = db.query(Product).filter(Product.id == product.id).first()
            if data:
                data.name = product.name
                data.categoryId = product.categoryId
                data.productUrl = product.productUrl
                data.description = product.description
                data.stockQuantity = product.stockQuantity
                data.price = product.price
                data.discount = product.discount
                data.isAvailable = product.isAvailable
                db.add(data)
                db.commit()
                db.refresh(data)
                return {"success": "product updated Successfully"}
            else:
                return {"error": "product not found"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product is not availbale"
            )
    except Exception as e:
        db.rollback()
        return {"error": f"{e}"}


@router.delete("/delete/{id}")
async def delete_product(db: db_dependency, id: int):
    db.begin()
    try:
        data = db.query(Product).filter(Product.id == id).first()
        if data:
            db.delete(data)
            db.commit()
            return {"success": "product deleted Successfully"}
        else:
            return {"error": "product not found"}
    except Exception as e:
        db.rollback()
        return {"error": f"{e}"}
