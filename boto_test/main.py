import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path

from routers.routers import router
from setup import lifespan
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

core_1 = os.getenv("CORE_1")
core_2 = os.getenv("CORE_2")

app = FastAPI(lifespan=lifespan)
app.include_router(router)

ALLOWED_ORIGINS = [
    core_1,
    core_2,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Set-Cookie", "Authorization"],
)

app.include_router(router)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    file_path = Path("static/main.html")
    return FileResponse(file_path, media_type="text/html")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Ошибка валидации: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Передан некорректный URL. Убедитесь, что ссылка начинается с http:// или https://"
        },
    )