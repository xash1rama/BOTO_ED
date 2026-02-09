import random
import sqlite3
import string
from fastapi import APIRouter, HTTPException, Depends
from starlette.responses import RedirectResponse
from schemas.schemas import ShortenRequest
from database.models import get_db
from main import logger

router = APIRouter(tags=["Shortener"]) 

logger = logging.getLogger(__name__)

def generate_code(length: int = 6) -> str:
    """
    Генерирует случайную строку из букв и цифр.
    6 символов дают ~56 миллиардов комбинаций, что исключает коллизии для небольших сервисов.
    """
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

@router.get("/links", summary="Список всех ссылок")
async def get_all_links(db: sqlite3.Connection = Depends(get_db)):
    """
    Возвращает историю всех сокращенных ссылок. 
    """
    rows = db.execute("SELECT id, full_url, short_code FROM urls ORDER BY id DESC").fetchall()
    return [
        {
            "id": r["id"], 
            "full_url": r["full_url"], 
            "short_url": f"http://localhost:8000/{r['short_code']}"
        } for r in rows
    ]

@router.post("/shorten", status_code=201, summary="Создать короткую ссылку")
async def shorten(request: ShortenRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Принимает длинный URL, генерирует уникальный код и сохраняет пару в базу.
    """
    code = generate_code()
    url_str = str(request.url) 
    
    try:
        db.execute(
            "INSERT INTO urls (full_url, short_code) VALUES (?, ?)",
            (url_str, code),
        )
        db.commit()
        logger.info(f"URL сокращен: {url_str} -> {code}")
        return {"short_url": f"http://localhost:8000/{code}"}
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при сохранении: {e}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить ссылку")

@router.get("/{code}", summary="Редирект")
async def redirect(code: str, db: sqlite3.Connection = Depends(get_db)):
    """
    Ищет оригинальную ссылку по коду. 
    Если находит перенаправляет пользователя
    """
    row = db.execute(
        "SELECT full_url FROM urls WHERE short_code = ?", (code,)
    ).fetchone()

    if row:
        logger.info(f"Переход по коду {code} на {row['full_url']}")
        return RedirectResponse(url=row["full_url"])

    logger.warning(f"Попытка доступа по несуществующему коду: {code}")
    raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")

@router.delete("/links/{link_id}", summary="Удалить ссылку")
async def delete_link(link_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Удаляет запись о ссылке из базы по её ID.
    """
    cursor = db.execute("DELETE FROM urls WHERE id = ?", (link_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    logger.info(f"Удалена ссылка ID: {link_id}")
    return {"message": "Успешно удалено"}


