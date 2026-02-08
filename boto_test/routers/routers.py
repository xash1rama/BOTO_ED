import random
import sqlite3
import string
from fastapi import APIRouter, HTTPException, Depends
from starlette.responses import RedirectResponse
from schemas.schemas import ShortenRequest
from database.models import get_db
import logging

router = APIRouter(tags=["users"])


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_code(length=6):
    """Генерируем случайную ссылку из 6 значений (более 6 млрд вариантов)"""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))



@router.get("/links")
async def get_all_links(db: sqlite3.Connection = Depends(get_db)):
    """Для отображения истории запросов"""
    rows = db.execute("SELECT id, full_url, short_code FROM urls ORDER BY id DESC").fetchall()
    return [
        {
            "id": r[0],
            "full_url": r[1],
            "short_url": f"{r[2]}"
        } for r in rows
        ]


@router.delete("/links/{link_id}")
async def delete_link(link_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Удалить ссылку по ID."""
    cursor = db.execute("DELETE FROM urls WHERE id = ?", (link_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    logger.info(f"Удаляем ссылку с id: {link_id}")  # <- Логируем
    db.commit()
    return {"message": "Deleted successfully"}


@router.post("/shorten")
async def shorten(request: ShortenRequest, db: sqlite3.Connection = Depends(get_db)):
    code = generate_code()  # <- Создаем случайное значение
    try:
        db.execute(
                "INSERT INTO urls (full_url, short_code) VALUES (?, ?)",
                (str(request.url), code),
            )  # <- Создаем запись в бд если ссылка валидна
        db.commit()

        logger.info(f"Сократили: {request.url} -> {code}")  # <- Логируем
        return {
            "short_url": f"http://localhost:8000/{code}"
        }  # <- Даем ответ если небыло ошибок
    except Exception as e:
        ###Использую Exception что бы не обрабатывать кучу случаев
        logger.error(f"Error saving URL: {e}")  # <- Логируем ошибку
        raise HTTPException(
            status_code=500, detail="Database error"
        )  # <- Высвечивается окно с ошибкой


@router.get("/{code}")
async def redirect(code: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute(
        "SELECT full_url FROM urls WHERE short_code = ?", (code,)
    )  # <- ищем код который сгенерировали и по нему достаем полную ссылку
    row = cursor.fetchone()

    if row:
        logger.info(f"Перенеслись из {code} to {row[0]}")
        return RedirectResponse(
            url=row[0]
        )  # <- редиректимся по нашему коду в сохраненную ссылку

    logger.warning(f"Код не найден: {code}")
    raise HTTPException(
        status_code=404, detail="URL not found"
    )  # <- Если ссылку по коду не нашли


