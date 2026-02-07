import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from main import app
from database.models import get_db, init_db

# 1. Создаем функцию для ТЕСТОВОЙ базы
def get_test_db():
    # Здесь тоже добавляем этот параметр
    conn = sqlite3.connect("test.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# 2. ГОВОРИМ FASTAPI ИСПОЛЬЗОВАТЬ ТЕСТОВУЮ БАЗУ
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db("test.db") # Создаем таблицы в тест-базе
    with sqlite3.connect("test.db") as conn:
        conn.execute("DELETE FROM urls")
        conn.commit()
    yield
    # После тестов очищаем переопределения (хороший тон)
    # app.dependency_overrides.clear()

def test_shorten_url_success():
    """Проверка нормального запроса"""

    response = client.post("/shorten", json={"url": "https://google.com"})
    assert response.status_code == 200


def test_shorten_url_invalid():
    """Проверка валидации (ошибка 422 на обычный текст)"""
    response = client.post("/shorten", json={"url": "not-a-link"})
    assert response.status_code == 422
    # Проверяем, что в ответе есть наше кастомное сообщение или детали Pydantic
    assert "detail" in response.json() or "message" in response.json()

def test_redirect_and_logging():
    """Проверка редиректа на оригинальный URL"""
    target = "https://yandex.ru/"
    res = client.post("/shorten", json={"url": target})
    code = res.json()["short_url"].split("/")[-1]

    # Пробуем перейти (follow_redirects=False чтобы увидеть 307 статус)
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == target

def test_redirect_not_found():
    """Проверка 404 для несуществующего кода"""
    response = client.get("/nonexistent123")
    assert response.status_code == 404

def test_history_list():
    """Проверка отображения списка (истории)"""
    # Добавляем 2 ссылки
    client.post("/shorten", json={"url": "https://a.com"})
    client.post("/shorten", json={"url": "https://b.com"})

    response = client.get("/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Проверяем, что последняя (b.com) идет первой (ORDER BY id DESC)
    assert "b.com" in data[0]["full_url"]

def test_delete_link_success():
    """Проверка удаления ссылки"""
    # Создаем ссылку
    client.post("/shorten", json={"url": "https://delete-me.com/"})
    links = client.get("/links").json()
    link_id = links[0]["id"]

    # Удаляем
    del_res = client.delete(f"/links/{link_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Deleted successfully"

    # Проверяем, что в базе стало пусто
    history = client.get("/links").json()
    assert len(history) == 0

def test_delete_nonexistent_link():
    """Проверка удаления несуществующей ссылки (404)"""
    response = client.delete("/links/9999")
    assert response.status_code == 404
