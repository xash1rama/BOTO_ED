from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.models import init_db
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")


@asynccontextmanager
async def lifespan(main_app: FastAPI):
    init_db(DB_URL)
    yield
