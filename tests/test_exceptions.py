"""Тесты для модуля исключений и его обратной совместимости.

Модуль ``nalogovich.exeptions`` был переименован в ``nalogovich.exceptions``
(исправлена опечатка). Эти тесты проверяют, что:

* новый импорт ``from nalogovich.exceptions import ...`` работает;
* старый импорт ``from nalogovich.exeptions import ...`` всё ещё работает;
* старый путь импорта выдаёт ``DeprecationWarning``;
* оба модуля предоставляют одни и те же объекты классов.
"""

from __future__ import annotations

import importlib
import sys
import warnings

import pytest

EXPECTED_NAMES = ["NPDError", "ValidationError", "ApiError", "AuthenticationError"]


def _reimport(module_name: str):
    """Импортировать модуль заново, чтобы повторно сработал код уровня модуля."""
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_new_import_works():
    """Новый импорт `from nalogovich.exceptions import ...` работает."""
    from nalogovich.exceptions import (
        ApiError,
        AuthenticationError,
        NPDError,
        ValidationError,
    )

    assert issubclass(ValidationError, NPDError)
    assert issubclass(ApiError, NPDError)
    assert issubclass(AuthenticationError, NPDError)


def test_new_module_exports_full_public_api():
    """Новый модуль предоставляет весь ожидаемый публичный API."""
    module = importlib.import_module("nalogovich.exceptions")
    for name in EXPECTED_NAMES:
        assert hasattr(module, name), f"Отсутствует {name} в nalogovich.exceptions"


def test_old_import_still_works():
    """Старый импорт `from nalogovich.exeptions import ...` всё ещё работает."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from nalogovich.exeptions import (
            ApiError,
            AuthenticationError,
            NPDError,
            ValidationError,
        )

    assert issubclass(ValidationError, NPDError)
    assert issubclass(ApiError, NPDError)
    assert issubclass(AuthenticationError, NPDError)


def test_old_module_reexports_same_objects():
    """Старый модуль реэкспортирует те же самые объекты классов."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        old = _reimport("nalogovich.exeptions")
    new = importlib.import_module("nalogovich.exceptions")

    for name in EXPECTED_NAMES:
        assert getattr(old, name) is getattr(new, name)


def test_old_import_emits_deprecation_warning():
    """Старый путь импорта выдаёт DeprecationWarning."""
    sys.modules.pop("nalogovich.exeptions", None)
    with pytest.warns(DeprecationWarning, match="nalogovich.exceptions"):
        importlib.import_module("nalogovich.exeptions")


def test_api_error_attributes():
    """ApiError сохраняет переданные атрибуты."""
    from nalogovich.exceptions import ApiError

    err = ApiError("boom", status_code=500, response_data={"key": "value"})
    assert str(err) == "boom"
    assert err.status_code == 500
    assert err.response_data == {"key": "value"}


def test_authentication_error_defaults():
    """AuthenticationError по умолчанию использует статус 401."""
    from nalogovich.exceptions import AuthenticationError

    err = AuthenticationError("access denied")
    assert err.status_code == 401
    assert err.response_data is None
