from typing import Annotated
from fastapi import Depends, FastAPI
from database import Base, SessionLocal, engine
import models
from sqlalchemy.orm import Session
from routes import auth
from dotenv import load_dotenv

models.Base.metadata.create_all(bind=engine)


app = FastAPI()
load_dotenv()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


app.include_router(auth.router)

