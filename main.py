from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from dotenv import load_dotenv




app = FastAPI()
load_dotenv()


