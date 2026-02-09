import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from main import app
from database.models import get_db, init_db

def get_test_db():
    """
    Генератор подключения к временной базе данных для тестов.
    """
    conn = sqlite3.connect("test.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)

def test_shorten_url_success():
    """Проверка: корректный URL должен сохраняться и возвращать код 201/200."""
    response = client.post("/shorten", json={"url": "https://google.com"})
    assert response.status_code == 201 or response.status_code == 200
    assert "short_url" in response.json()

def test_shorten_url_invalid():
    """Проверка: если передать не URL, Pydantic должен вернуть ошибку 422."""
    response = client.post("/shorten", json={"url": "это-не-ссылка"})
    assert response.status_code == 422

def test_redirect_and_flow():
    """
    Комплексная проверка: 
    1. Создаем ссылку. 
    2. Пытаемся по ней перейти.
    """
    target = "https://yandex.ru/"
    res_create = client.post("/shorten", json={"url": target})
    code = res_create.json()["short_url"].split("/")[-1]
    
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == target

def test_history_sorting():
    """Проверка: ссылки в истории должны идти в обратном порядке (новые сверху)."""
    client.post("/shorten", json={"url": "https://first.com"})
    client.post("/shorten", json={"url": "https://second.com"})

    response = client.get("/links")
    data = response.json()
    assert len(data) == 2
    assert "second.com" in data[0]["full_url"]

def test_delete_flow():
    """Проверка удаления: существующая ссылка удаляется, несуществующая — дает 404."""
    # Подготовка
    client.post("/shorten", json={"url": "https://drop.me"})
    links = client.get("/links").json()
    link_id = links[0]["id"]

    # Удаление
    del_res = client.delete(f"/links/{link_id}")
    assert del_res.status_code == 200
    
    # Проверка пустоты
    check_res = client.get("/links")
    assert len(check_res.json()) == 0

    # Повторное удаление (ошибка)
    failed_del = client.delete(f"/links/{link_id}")
    assert failed_del.status_code == 404
