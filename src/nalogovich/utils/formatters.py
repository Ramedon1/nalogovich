import datetime

from dateutil.relativedelta import relativedelta
from typing import Any


def format_datetime_with_tz(dt: datetime.datetime, default_tz: str = "+03:00") -> str:
    """
    Форматирует datetime в ISO строку с таймзоной.

    :param dt: datetime объект
    :param default_tz: таймзона по умолчанию, если не указана
    :return: ISO строка с таймзоной
    """
    tz_offset = dt.strftime("%z") or default_tz
    if tz_offset and len(tz_offset) == 5 and ":" not in tz_offset:
        tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}{tz_offset}"


def format_date_range(
    date_from: datetime.datetime | None = None,
    date_to: datetime.datetime | None = None,
    default_tz: str = "+03:00",
) -> tuple[str, str]:
    """
    Форматирует диапазон дат для API запросов.

    :param date_from: Начальная дата (если None - месяц назад)
    :param date_to: Конечная дата (если None - сейчас)
    :param default_tz: таймзона по умолчанию
    :return: кортеж (from_str, to_str)
    """

    if date_from is None:
        date_from = datetime.datetime.now() - relativedelta(months=1)
    if date_to is None:
        date_to = datetime.datetime.now()

    tz_offset = date_from.strftime("%z") or default_tz
    from_str = f"{date_from.strftime('%Y-%m-%dT00:00:00.00')}{tz_offset}"
    to_str = f"{date_to.strftime('%Y-%m-%dT23:59:59.59')}{tz_offset}"

    return from_str, to_str


def build_payload(base: dict[str, Any], **optional) -> dict[str, Any]:
    """
    Строит payload, добавляя только непустые опциональные поля.

    :param base: базовый словарь
    :param optional: опциональные поля
    :return: итоговый payload
    """

    payload = base.copy()
    for key, value in optional.items():
        if value is not None:
            payload[key] = value
    return payload
