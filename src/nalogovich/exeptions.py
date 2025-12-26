from typing import Any


class NPDError(Exception):
    """Базовое исключение для библиотеки"""

    pass


class ValidationError(NPDError):
    """Ошибка валидации входных данных перед отправкой"""

    pass


class ApiError(NPDError):
    """Ошибка, которую вернул сервер ФНС"""

    def __init__(self, message: str, status_code: int, response_data: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(NPDError):
    """Ошибка авторизации"""

    def __init__(self, message: str, status_code: int = 401, response_data: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
