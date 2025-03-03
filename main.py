import locale
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request
from database import Base, SessionLocal, engine
import models
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from routes import auth, carts, categories, products, orders, review_ratings, users
from dotenv import load_dotenv
import json

models.Base.metadata.create_all(bind=engine)


app = FastAPI()
load_dotenv()


class Localization:
    def __init__(self, lang: str = "en"):
        self.lang = self.normalize_language(lang)
        self.messages = self.load_messages(self.lang)

    def normalize_language(self, lang: str) -> str:
        return lang.split("-")[0] if lang else "en"

    def load_messages(self, lang: str) -> dict:
        try:
            with open(f"locales/{lang}.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            if lang != "en":
                return self.load_messages("en")
            raise HTTPException(
                status_code=404, detail=f"Language file for {lang} not found."
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Failed to parse language file."
            )

    def gettext(self, message_key: str) -> str:
        return self.messages.get(message_key, message_key)


class LocalizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = request.headers.get("Accept-Language", "ja")

        localization = Localization(lang)
        request.state.localization = localization

        response = await call_next(request)
        return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.add_middleware(LocalizationMiddleware)
db_dependency = Annotated[Session, Depends(get_db)]


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(carts.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(review_ratings.router)
