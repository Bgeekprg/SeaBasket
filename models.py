from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    DECIMAL,
    TEXT,
    Enum,
    TIMESTAMP,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from database import Base


class Role(PyEnum):
    admin = "admin"
    customer = "customer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phoneNumber = Column(String(13), unique=True, index=True)
    password = Column(String(80), nullable=False)
    profilePic = Column(String(255), nullable=True)
    role = Column(Enum(Role), nullable=False, default=Role.customer)
    status = Column(Boolean, default=True)
    isVerified = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    categoryName = Column(String(100), nullable=False)
    status = Column(Boolean, default=True)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(TEXT, nullable=True)
    stockQuantity = Column(Integer, default=0)
    price = Column(DECIMAL(10, 2), nullable=False)
    categoryId = Column(Integer, ForeignKey("categories.id"), nullable=True)
    productUrl = Column(String(255), nullable=True)
    discount = Column(Integer, nullable=True)
    rating = Column(DECIMAL(3, 2), nullable=True)
    isAvailable = Column(Boolean, default=True)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    category = relationship("Category", backref="products", cascade="all,delete")


class ProductImage(Base):
    __tablename__ = "productImages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    imageUrl = Column(String(255), nullable=False)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    product = relationship("Product", backref="images", cascade="all, delete")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    user = relationship("User", backref="carts", cascade="all,delete")
    product = relationship("Product", backref="carts", cascade="all,delete")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Boolean, default=True)
    totalAmount = Column(DECIMAL(10, 2), nullable=False)
    orderStatus = Column(
        Enum("pending", "shipped", "delivered", "cancelled", name="order_status"),
        default="pending",
    )
    paymentStatus = Column(
        Enum("pending", "paid", "failed", "refunded", name="payment_status"),
        default="pending",
    )
    shippingAddress = Column(TEXT, nullable=False)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    user = relationship("User", backref="orders", cascade="all,delete")


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey("orders.id"), nullable=False)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(DECIMAL(10, 2), nullable=False)
    discount = Column(DECIMAL(5, 2), default=0)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())
    updatedAt = Column(
        TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    order = relationship("Order", backref="order_details", cascade="all,delete")
    product = relationship("Product", backref="order_details", cascade="all,delete")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(DECIMAL(3, 2), nullable=True)
    reviewText = Column(TEXT, nullable=True)
    createdAt = Column(TIMESTAMP, default=func.current_timestamp())

    product = relationship("Product", backref="reviews", cascade="all,delete")
    user = relationship("User", backref="reviews", cascade="all,delete")