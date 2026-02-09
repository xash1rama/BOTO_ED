from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.models import init_db
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "links.db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Все, что ДО yield — выполняется при старте.
    Все, что ПОСЛЕ — при выключении приложения.
    """
        init_db(DB_URL)
    yield  
