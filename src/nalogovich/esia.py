from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, parse_qs

from nalogovich.exceptions import EsiaAuthError, ValidationError

__all__ = [
    "ESIA_BASE",
    "ESIA_LOGIN_URL",
    "ESIA_TOTP_URL",
    "LKNPD_REDIRECT_URL",
    "LKNPD_CALLBACK_URL",
    "extract_query_param",
    "generate_totp",
    "esia_login",
]

ESIA_BASE = "https://esia.gosuslugi.ru"
ESIA_LOGIN_URL = f"{ESIA_BASE}/aas/oauth2/api/login"
ESIA_TOTP_URL = f"{ESIA_BASE}/aas/oauth2/api/login/totp/verify"

LKNPD_REDIRECT_URL = (
    "https://lknpd.nalog.ru/auth/login/back?remember=true&register=false"
)
LKNPD_CALLBACK_URL = (
    "https://lknpd.nalog.ru/auth/login/back?remember=false&register=false"
)

DEFAULT_IMPERSONATE = "chrome"


def extract_query_param(url: str, name: str) -> str | None:
    """
    Достать значение query-параметра из URL.

    :param url: Адрес, из которого берём параметр
    :param name: Имя параметра

    :return: Значение параметра или None, если его нет
    """
    values = parse_qs(urlparse(url).query).get(name)
    return values[0] if values else None


def generate_totp(secret: str) -> str:
    """
    Сгенерировать одноразовый код по секрету Госуслуг.

    Принимает как чистый base32-секрет (``JBSWY3DPEHPK3PXP``),
    так и целиком строку ``otpauth://totp/...?secret=...&issuer=...`` из QR-кода.

    :param secret: Base32-секрет или otpauth-ссылка

    :raises ValidationError: Если не установлен пакет pyotp или секрет невалиден

    :return: Одноразовый код
    """
    try:
        import pyotp
    except ImportError as e:
        raise ValidationError(
            "Для генерации TOTP-кода установите зависимость: pip install nalogovich[totp]"
        ) from e

    secret = secret.strip()

    try:
        if secret.lower().startswith("otpauth://"):
            otp = pyotp.parse_uri(secret)
        else:
            otp = pyotp.TOTP(secret.replace(" ", "").upper())
        return otp.now()
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Некорректный TOTP-секрет: {e}") from e


def _get_async_session():
    """
    Ленивый импорт curl_cffi.

    :raises ValidationError: Если не установлен пакет curl_cffi

    :return: Класс curl_cffi.requests.AsyncSession
    """
    try:
        from curl_cffi.requests import AsyncSession
    except ImportError as e:
        raise ValidationError(
            "Для входа через Госуслуги установите зависимость: pip install nalogovich[esia]"
        ) from e

    return AsyncSession


def _parse_json(response: Any) -> Any:
    """Разобрать тело ответа как JSON, вернуть None если это не JSON."""
    try:
        return response.json()
    except Exception:
        return None


def _raise_esia_error(message: str, response: Any) -> None:
    """Собрать EsiaAuthError по ответу ЕСИА."""
    data = _parse_json(response)
    if isinstance(data, dict):
        message = data.get("error_description") or data.get("message") or message
    raise EsiaAuthError(message, status_code=response.status_code, response_data=data)


async def esia_login(
    auth_url: str,
    login: str,
    password: str,
    totp_secret: str | None = None,
    totp_code: str | None = None,
    user_agent: str | None = None,
    proxy: str | None = None,
    impersonate: str = DEFAULT_IMPERSONATE,
) -> tuple[str, str]:
    """
    Пройти авторизацию на портале Госуслуг (ЕСИА) и получить код авторизации для ЛК НПД.

    Порядок действий повторяет веб-клиент ЛК НПД:

    1. ``GET auth_url`` - ЕСИА выдаёт сессионные куки и редиректит на форму входа;
    2. ``POST /aas/oauth2/api/login`` - логин и пароль;
    3. ``POST /aas/oauth2/api/login/totp/verify`` - одноразовый код, если включена 2ФА;
    4. из ответа достаём ``redirect_url`` с параметрами ``code`` и ``state``.

    :param auth_url: Ссылка на ЕСИА, полученная из ``POST /api/v1/auth/esia/url``
    :param login: Логин Госуслуг (телефон, email или СНИЛС)
    :param password: Пароль Госуслуг
    :param totp_secret: Base32-секрет из приложения-аутентификатора
    :param totp_code: Готовый одноразовый код (приоритетнее, чем totp_secret)
    :param user_agent: User-Agent для запросов к ЕСИА
    :param proxy: Прокси в формате ``http://user:pass@host:port``
    :param impersonate: Профиль браузера curl_cffi для TLS-отпечатка

    :raises ValidationError: Если не установлен curl_cffi или нужен код 2ФА, но он не передан
    :raises EsiaAuthError: При неверных учетных данных или неподдерживаемом способе подтверждения

    :return: Кортеж ``(code, state)`` для ``POST /api/v1/auth/esia``
    """
    async_session = _get_async_session()

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": ESIA_BASE,
        "Referer": f"{ESIA_BASE}/login/",
    }
    if user_agent:
        headers["User-Agent"] = user_agent

    session_kwargs: dict[str, Any] = {"impersonate": impersonate, "headers": headers}
    if proxy:
        session_kwargs["proxies"] = {"http": proxy, "https": proxy}

    async with async_session(**session_kwargs) as session:
        response = await session.get(auth_url, allow_redirects=True)
        if response.status_code >= 400:
            _raise_esia_error(
                f"ЕСИА не приняла ссылку авторизации: HTTP {response.status_code}",
                response,
            )

        response = await session.post(
            ESIA_LOGIN_URL, json={"login": login, "password": password}
        )
        if response.status_code >= 400:
            _raise_esia_error("Неверный логин или пароль Госуслуг", response)

        data = _parse_json(response)
        if not isinstance(data, dict):
            _raise_esia_error("Неожиданный ответ ЕСИА при входе", response)

        action = data.get("action")

        if action == "ENTER_MFA":
            mfa_type = (data.get("mfa_details") or {}).get("type")
            if mfa_type != "TTP":
                raise EsiaAuthError(
                    f"Способ подтверждения {mfa_type!r} не поддерживается. "
                    "Включите в Госуслугах вход по одноразовому коду из приложения.",
                    status_code=response.status_code,
                    response_data=data,
                )

            code = totp_code or (generate_totp(totp_secret) if totp_secret else None)
            if not code:
                raise ValidationError(
                    "Для входа нужен одноразовый код: передайте totp_secret или totp_code"
                )

            response = await session.post(ESIA_TOTP_URL, params={"code": code})
            if response.status_code >= 400:
                _raise_esia_error("Неверный одноразовый код", response)

            data = _parse_json(response)
            if not isinstance(data, dict):
                _raise_esia_error("Неожиданный ответ ЕСИА при проверке кода", response)

            action = data.get("action")

        if action != "DONE":
            raise EsiaAuthError(
                f"ЕСИА не завершила вход, требуется действие {action!r}",
                status_code=response.status_code,
                response_data=data,
            )

        redirect_url = data.get("redirect_url")
        if not redirect_url:
            raise EsiaAuthError(
                "ЕСИА не вернула ссылку возврата с кодом авторизации",
                status_code=response.status_code,
                response_data=data,
            )

    code = extract_query_param(redirect_url, "code")
    state = extract_query_param(redirect_url, "state")
    if not code or not state:
        raise EsiaAuthError(
            "В ссылке возврата ЕСИА нет параметров code и state",
            status_code=200,
            response_data={"redirect_url": redirect_url},
        )

    return code, state
