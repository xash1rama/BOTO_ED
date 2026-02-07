from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    """Валидность ссылки"""

    url: HttpUrl
