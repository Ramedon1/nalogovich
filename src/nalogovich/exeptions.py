"""Устаревший модуль. Используйте :mod:`nalogovich.exceptions`.

Модуль сохранён только для обратной совместимости: в его названии была
опечатка (``exeptions`` вместо ``exceptions``). Все исключения теперь
определены в :mod:`nalogovich.exceptions`, а этот модуль лишь реэкспортирует
их и при импорте выдаёт :class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings

from nalogovich.exceptions import (
    ApiError,
    AuthenticationError,
    NPDError,
    ValidationError,
)

__all__ = [
    "NPDError",
    "ValidationError",
    "ApiError",
    "AuthenticationError",
]

warnings.warn(
    "Модуль 'nalogovich.exeptions' переименован в 'nalogovich.exceptions' "
    "(исправлена опечатка в названии). Старый путь импорта устарел и будет "
    "удалён в одной из будущих версий — используйте "
    "'from nalogovich.exceptions import ...'.",
    DeprecationWarning,
    stacklevel=2,
)
