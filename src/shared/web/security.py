from secrets import compare_digest

from fastapi import Security
from fastapi.security import APIKeyHeader

from src.shared.web.api_settings import get_api_settings
from src.shared.web.exceptions import InvalidApiKeyError

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Проверяет статический ключ; compare_digest - сравнение за постоянное время."""
    expected = get_api_settings().api_key.get_secret_value()
    if api_key is None or not compare_digest(api_key.encode(), expected.encode()):
        raise InvalidApiKeyError()
