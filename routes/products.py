from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal
from models import Product
from routes.auth import get_current_user


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
    stockQuantity: Optional[int] = None
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
async def get_product(id: int, db: db_dependency, request: Request):
    localization = request.state.localization

    product = db.query(Product).filter(Product.id == id).first()
    if product:
        return product
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=localization.gettext("product_not_found"),
    )


@router.post("/add", status_code=status.HTTP_201_CREATED)
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
        admin_required(user)

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
        return {"success": localization.gettext("product_added_successfully")}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{localization.gettext('failed_to_add_product')}: {str(e)}",
        )


@router.put("/update")
async def update_product(
    request: Request, db: db_dependency, product: ProductUpdate, user: user_dependency
):
    localization = request.state.localization
    db.begin()
    try:
        admin_required(user)

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
                detail=f"{localization.gettext('failed_to_add_product')}: {str(e)}",
            )

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update product: {str(e)}"}


@router.delete("/delete/{id}")
async def delete_product(
    request: Request, db: db_dependency, id: int, user: user_dependency
):
    localization = request.state.localization
    db.begin()
    try:
        admin_required(user)
        data = db.query(Product).filter(Product.id == id).first()
        if data:
            db.delete(data)
            db.commit()
            return {"success": localization.gettext("product_deleted")}
        else:
            return {"error": localization.gettext("product_not_found")}
    except Exception as e:
        db.rollback()
        return {"error": localization.gettext(f"{e}")}


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
