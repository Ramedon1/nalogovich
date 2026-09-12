from __future__ import annotations

import datetime
import aiohttp
from typing import Any
from dateutil.relativedelta import relativedelta
from loguru import logger

from nalogovich.enums import (
    PaymentType,
    SortBy,
    CommentReturn,
    ReceiptType,
    BuyerType,
    InvoicePaymentType,
    InvoiceClientType,
    InvoiceStatus,
)
from nalogovich.esia import (
    LKNPD_CALLBACK_URL,
    LKNPD_REDIRECT_URL,
    esia_login,
    extract_query_param,
)
from nalogovich.exceptions import ValidationError, AuthenticationError, ApiError
from nalogovich.models.operations import (
    ServiceCheck,
    OperationResponse,
    Income,
    IncomeInfo,
    Invoice,
    InvoiceResponse,
    PaymentTypeInfo,
)
from nalogovich.utils.checks import prepare_client_payload
from nalogovich.utils.formatters import format_date_range, build_payload
from nalogovich.utils.validators import (
    validate_payment_type_params,
    validate_client_type_params,
)


class NpdClient:
    def __init__(
        self,
        inn: str | None = None,
        password: str | None = None,
        enable_logging: bool = False,
        proxy: str | None = None,
        source_device_id: str | None = None,
    ):
        self.base_url = "https://lknpd.nalog.ru/api/v1/"
        self.inn = inn
        self.password = password
        self.enable_logging = enable_logging
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        self.device_info = {
            "sourceDeviceId": source_device_id or "-YWmoFV_Tw8ATGRD8Zym3",
            "sourceType": "WEB",
            "appVersion": "1.0.0",
            "metaDetails": {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            },
        }
        self.token: str | None = None
        self.refresh_token: str | None = None
        self.token_expire_in: str | None = None
        self.profile: dict[str, Any] | None = None
        self.session: aiohttp.ClientSession | None = None

        if self.enable_logging:
            logger.enable("nalogovich")
        else:
            logger.disable("nalogovich")

    def _log(self, level: str, message: str, **kwargs):
        """Вспомогательный метод для логирования."""
        if self.enable_logging:
            log_func = getattr(logger.opt(depth=1), level)
            log_func(f"[nalogovich] {message}", **kwargs)

    def _apply_token(self, response_data: Any) -> None:
        """
        Сохранить токены из ответа авторизации и проставить заголовок Authorization.

        :param response_data: Тело ответа ручки авторизации
        """
        if not isinstance(response_data, dict):
            return

        token = response_data.get("token")
        if not token:
            return

        self.token = token
        self.refresh_token = response_data.get("refreshToken") or self.refresh_token
        self.token_expire_in = response_data.get("tokenExpireIn")
        if profile := response_data.get("profile"):
            self.profile = profile
            if not self.inn:
                self.inn = profile.get("inn")

        self.headers["Authorization"] = f"Bearer {token}"
        if self.session and not self.session.closed:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _raise_for_auth_status(
        self, status: int, response_data: Any, prefix: str = "Ошибка авторизации"
    ) -> None:
        """
        Превратить HTTP-статус ручки авторизации в исключение библиотеки.

        :param status: HTTP-статус ответа
        :param response_data: Тело ответа (если это был JSON)
        :param prefix: Префикс для сообщения об ошибке

        :raises AuthenticationError: При 401, 403 и 422
        :raises ApiError: При остальных статусах >= 400
        """
        if status < 400:
            return

        message = None
        if isinstance(response_data, dict):
            message = response_data.get("message")

        if status == 422:
            message = message or "Неверный ИНН или пароль"
            self._log("error", f"{prefix}: {message}")
            raise AuthenticationError(
                message, status_code=422, response_data=response_data
            )

        if status == 401:
            message = message or "Неавторизован. Проверьте учетные данные."
            self._log("error", f"{prefix}: Неавторизован")
            raise AuthenticationError(
                message, status_code=401, response_data=response_data
            )

        if status == 403:
            message = message or "Доступ запрещен. Возможно, аккаунт заблокирован."
            self._log("error", f"{prefix}: Доступ запрещен")
            raise AuthenticationError(
                message, status_code=403, response_data=response_data
            )

        message = message or f"{prefix}: HTTP {status}"
        self._log("error", message)
        raise ApiError(message, status_code=status, response_data=response_data)

    async def _post_auth(self, endpoint: str, payload: dict, prefix: str) -> Any:
        """
        Выполнить запрос к ручке авторизации и разобрать ответ.

        :param endpoint: Эндпоинт относительно base_url
        :param payload: Тело запроса
        :param prefix: Префикс для сообщений об ошибках

        :raises AuthenticationError: При ошибке учетных данных
        :raises ApiError: При сетевой ошибке или ошибке API

        :return: Тело ответа
        """
        session = await self.get_session()

        kwargs = {}
        if self.proxy:
            kwargs["proxy"] = self.proxy

        try:
            async with session.request(
                "POST", self.base_url + endpoint, json=payload, **kwargs
            ) as response:
                response_data = None
                if "application/json" in response.headers.get("Content-Type", ""):
                    response_data = await response.json()

                self._raise_for_auth_status(response.status, response_data, prefix)
                return response_data

        except aiohttp.ClientError as e:
            self._log("error", f"Ошибка сети при авторизации: {e}")
            raise ApiError(f"Ошибка сети при авторизации: {e}", status_code=0)

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def request(self, method: str, endpoint: str, **kwargs) -> Any:
        session = await self.get_session()

        if self.proxy and "proxy" not in kwargs:
            kwargs["proxy"] = self.proxy

        if isinstance(kwargs.get("params"), dict):
            kwargs["params"] = {
                key: value
                for key, value in kwargs["params"].items()
                if value is not None
            }

        try:
            async with session.request(
                method, self.base_url + endpoint, **kwargs
            ) as response:
                response.raise_for_status()
                if "application/json" in response.headers.get("Content-Type", ""):
                    return await response.json()
                return await response.text()

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                await self.re_auth()
                return await self.request(method, endpoint, **kwargs)
            raise

        except aiohttp.ClientError:
            raise

    async def auth(self):
        """
        Авторизация через ЛК ФЛ (lkfl).

        :raises AuthenticationError: При неверных учетных данных или других ошибках авторизации
        :raises ApiError: При других ошибках API

        :return: Ответ ручки авторизации с токенами и профилем
        """

        if not self.inn or not self.password:
            raise AuthenticationError(
                "Не заданы ИНН и пароль. Используйте auth_esia(), from_token() "
                "или создайте клиент с inn и password."
            )

        payload = {
            "username": self.inn,
            "password": self.password,
            "deviceInfo": self.device_info,
        }

        response_data = await self._post_auth(
            "auth/lkfl", payload, "Ошибка авторизации"
        )
        self._apply_token(response_data)
        if self.token:
            self._log("info", "Авторизация успешно завершена")
        return response_data

    async def auth_esia(
        self,
        login: str,
        password: str,
        totp_secret: str | None = None,
        totp_code: str | None = None,
        impersonate: str = "chrome",
    ):
        """
        Авторизация через Госуслуги (ЕСИА).

        Требует установленной зависимости ``curl_cffi`` (``pip install nalogovich[esia]``),
        а для генерации одноразового кода по секрету - ``pyotp`` (``nalogovich[totp]``).

        :param login: Логин Госуслуг (телефон, email или СНИЛС)
        :param password: Пароль Госуслуг
        :param totp_secret: Base32-секрет из приложения-аутентификатора
        :param totp_code: Готовый одноразовый код (приоритетнее, чем totp_secret)
        :param impersonate: Профиль браузера curl_cffi для TLS-отпечатка

        :raises ValidationError: Если не установлены зависимости или не передан код 2ФА
        :raises EsiaAuthError: При ошибке авторизации на стороне Госуслуг
        :raises ApiError: При других ошибках API

        :return: Ответ ручки авторизации с токенами и профилем
        """

        self._log("info", "Авторизация через Госуслуги (ЕСИА)")

        url_response = await self._post_auth(
            "auth/esia/url",
            {"redirectUrl": LKNPD_REDIRECT_URL},
            "Ошибка получения ссылки ЕСИА",
        )

        auth_url = (url_response or {}).get("url")
        if not auth_url:
            raise ApiError(
                "ЛК НПД не вернул ссылку авторизации ЕСИА",
                status_code=0,
                response_data=url_response,
            )

        code, state = await esia_login(
            auth_url=auth_url,
            login=login,
            password=password,
            totp_secret=totp_secret,
            totp_code=totp_code,
            user_agent=self.headers.get("User-Agent"),
            proxy=self.proxy,
            impersonate=impersonate,
        )

        expected_state = extract_query_param(auth_url, "state")
        if expected_state and expected_state != state:
            self._log(
                "warning",
                "State в ответе ЕСИА не совпадает с исходным, используем полученный",
            )

        payload = {
            "redirectUrl": LKNPD_CALLBACK_URL,
            "code": code,
            "state": state,
            "deviceInfo": self.device_info,
        }

        response_data = await self._post_auth(
            "auth/esia", payload, "Ошибка авторизации через ЕСИА"
        )
        self._apply_token(response_data)
        if self.token:
            self._log("info", "Авторизация через Госуслуги успешно завершена")
        return response_data

    async def auth_with_token(
        self,
        token: str,
        refresh_token: str | None = None,
        verify: bool = False,
    ):
        """
        Восстановить ранее полученную сессию из сохраненных токенов.

        :param token: Токен доступа (живёт около часа)
        :param refresh_token: Токен обновления, нужен для автоматического продления сессии
        :param verify: Проверить токен запросом к API (при истечении сработает re_auth)

        :raises AuthenticationError: Если токен протух, а refresh_token не передан
        :raises ApiError: При других ошибках API
        """
        self._apply_token({"token": token, "refreshToken": refresh_token})
        self._log("info", "Сессия восстановлена из сохранённого токена")

        if verify:
            self.profile = await self.request("GET", "taxpayer")

    def export_session(self) -> dict[str, Any]:
        """
        Выгрузить текущую сессию для последующего восстановления через from_token().

        :return: Словарь с токенами и идентификатором устройства
        """
        return {
            "token": self.token,
            "refresh_token": self.refresh_token,
            "source_device_id": self.device_info["sourceDeviceId"],
        }

    @classmethod
    def from_token(
        cls,
        token: str,
        refresh_token: str | None = None,
        source_device_id: str | None = None,
        **kwargs: Any,
    ) -> "NpdClient":
        """
        Создать клиент из сохранённых токенов, без повторной авторизации.

        :param token: Токен доступа
        :param refresh_token: Токен обновления
        :param source_device_id: Идентификатор устройства из export_session()
        :param kwargs: Остальные параметры конструктора (proxy, enable_logging, inn, ...)

        :return: Готовый к работе клиент
        """
        client = cls(source_device_id=source_device_id, **kwargs)
        client._apply_token({"token": token, "refreshToken": refresh_token})
        return client

    @classmethod
    async def from_esia(
        cls,
        login: str,
        password: str,
        totp_secret: str | None = None,
        totp_code: str | None = None,
        **kwargs: Any,
    ) -> "NpdClient":
        """
        Создать клиент и сразу авторизоваться через Госуслуги (ЕСИА).

        :param login: Логин Госуслуг (телефон, email или СНИЛС)
        :param password: Пароль Госуслуг
        :param totp_secret: Base32-секрет из приложения-аутентификатора
        :param totp_code: Готовый одноразовый код
        :param kwargs: Остальные параметры конструктора (proxy, enable_logging, ...)

        :return: Авторизованный клиент
        """
        client = cls(**kwargs)
        try:
            await client.auth_esia(
                login=login,
                password=password,
                totp_secret=totp_secret,
                totp_code=totp_code,
            )
        except Exception:
            await client.close()
            raise
        return client

    async def re_auth(self):
        """
        Повторная авторизация через refresh token.

        :raises AuthenticationError: При невалидном refresh token
        :raises ApiError: При других ошибках API
        """
        self._log("info", "Попытка обновления токена")

        if not self.refresh_token:
            return await self.auth()

        payload = {
            "refreshToken": self.refresh_token,
            "deviceInfo": self.device_info,
        }

        session = await self.get_session()
        try:
            kwargs = {}
            if self.proxy:
                kwargs["proxy"] = self.proxy

            async with session.request(
                "POST", self.base_url + "auth/token", json=payload, **kwargs
            ) as response:
                response_data = None
                if "application/json" in response.headers.get("Content-Type", ""):
                    response_data = await response.json()

                if response.status in (401, 422):
                    self.refresh_token = None
                    return await self.auth()

                self._raise_for_auth_status(
                    response.status, response_data, "Ошибка обновления токена"
                )

                self._apply_token(response_data)
                if self.token:
                    self._log("info", "Токен успешно обновлен")

                return response_data

        except aiohttp.ClientError as e:
            self._log("error", f"Ошибка сети при обновлении токена: {e}")
            raise ApiError(f"Ошибка сети при обновлении токена: {e}", status_code=0)

    async def get_checks(
        self,
        from_date: datetime.datetime | None = (
            datetime.datetime.now() - relativedelta(months=1)
        ).replace(day=1),
        to_date: datetime.datetime | None = datetime.datetime.now(),
        offset: int | None = 0,
        limit: int | None = 30,
        sort_by: SortBy | None = SortBy.operation_time_desc,
        receipt_type: ReceiptType | None = None,
        buyer_type: BuyerType | None = None,
    ) -> OperationResponse:
        """
        Метод для получения чеков в истории за определенный период
        API Endpoint: https://lknpd.nalog.ru/api/v1/incomes

        :param from_date: Дата с которой будет браться информация о чеках
        :param to_date: Дата по которой будет браться информация о чеках
        :param offset: Смещение для пагинации
        :param limit: Количество записей на страницу
        :param sort_by: Сортировка записей по определенному параметру
        :param receipt_type: Сортировка чеков по их статусу (по стандарту - все чеки)
        :param buyer_type: Сортировка чеков по типу клиента (по стандарту - все чеки)

        :return: OperationResponse - модель с информацией о чеках
        """
        self._log(
            "info",
            f"Получение чеков за период с {from_date} по {to_date}, offset={offset}, limit={limit}",
        )

        params = {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "offset": offset,
            "limit": limit,
            "sort_by": sort_by.value if sort_by else None,
            "receipt_type": receipt_type.value if receipt_type else None,
            "buyer_type": buyer_type.value if buyer_type else None,
        }

        response = await self.request("GET", "incomes", params=params)
        result = OperationResponse.model_validate(response)
        self._log(
            "info",
            f"Получено чеков: {len(result.content)}, есть ещё: {result.has_more}",
        )
        return result

    async def create_check(
        self,
        name: str | None = None,
        amount: float | None = None,
        services: list[ServiceCheck] | None = None,
        is_business: bool = False,
        is_foreign_organization: bool = False,
        inn_of_organization: str | None = None,
        name_of_organization: str | None = None,
        date_of_sale: datetime.datetime | None = None,
        payment_type: PaymentType = PaymentType.CASH,
        ignore_max_total_income_restriction: bool = False,
    ) -> Income:
        """
        Регистрация дохода. Поддерживает одну или несколько позиций.

        :param name: Название (если одна позиция)
        :param amount: Сумма (если одна позиция)
        :param services: Список объектов ServiceCheck (если позиций несколько)
        :param is_business: Является ли организация бизнесом
        :param is_foreign_organization: Является ли организация иностранной
        :param inn_of_organization: ИНН организации
        :param name_of_organization: Название организации
        :param date_of_sale: Дата и время продажи
        :param payment_type: Тип оплаты
        :param ignore_max_total_income_restriction: Игнорировать ограничение по максимальному годовому доходу

        :return: Income - модель с информацией о зарегистрированном доходе
        """

        final_services: list[ServiceCheck] = []

        if services:
            final_services = services
        elif name and amount is not None:
            final_services = [ServiceCheck(name=name, amount=amount, quantity=1)]
        else:
            raise ValidationError(
                "Необходимо указать либо (name и amount), либо список services"
            )

        total_sum = sum(s.amount * s.quantity for s in final_services)

        client_payload = prepare_client_payload(
            is_business,
            is_foreign_organization,
            inn_of_organization,
            name_of_organization,
        )

        now = datetime.datetime.now().astimezone()
        sale_time = date_of_sale.astimezone() if date_of_sale else now

        payload = {
            "operationTime": sale_time.isoformat(),
            "requestTime": now.isoformat(),
            "services": [s.model_dump(by_alias=True) for s in final_services],
            "totalAmount": str(round(total_sum, 2)),
            "client": client_payload,
            "paymentType": payment_type.value,
            "ignoreMaxTotalIncomeRestriction": ignore_max_total_income_restriction,
        }

        response = await self.request("POST", "income", json=payload)
        result = Income.model_validate(response)
        self._log("info", f"Чек успешно создан, ID: {result.approved_receipt_uuid}")
        return result

    async def cancel_check(
        self,
        receipt_uuid: str,
        comment: CommentReturn | str = CommentReturn.wrong_receipt,
    ) -> IncomeInfo:
        """
        Метод для аннулирования чека.
        API Endpoint: https://lknpd.nalog.ru/api/v1/cancel

        :param receipt_uuid: Уникальный идентификатор чека (например, "200bzznrt0").
        :param comment: Причина аннулирования.
        """

        now = datetime.datetime.now().astimezone()
        formatted_time = now.isoformat()

        payload = {
            "operationTime": formatted_time,
            "requestTime": formatted_time,
            "comment": comment.value if isinstance(comment, CommentReturn) else comment,
            "receiptUuid": receipt_uuid,
        }

        response = await self.request("POST", "cancel", json=payload)
        result = IncomeInfo.model_validate(response.get("incomeInfo", response))
        self._log("info", f"Чек {receipt_uuid} успешно аннулирован")
        return result

    async def create_bill(
        self,
        name: str | None = None,
        amount: float | None = None,
        services: list[ServiceCheck] | None = None,
        client_name: str | None = None,
        client_phone: str | None = None,
        client_email: str | None = None,
        client_inn: str | None = None,
        client_type: InvoiceClientType = InvoiceClientType.FROM_INDIVIDUAL,
        payment_type: InvoicePaymentType = InvoicePaymentType.PHONE,
        phone: str | None = None,
        bank_name: str | None = None,
        bank_bik: str | None = None,
        corr_account: str | None = None,
        current_account: str | None = None,
    ) -> Invoice:
        """
        Создание счёта на оплату.

        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice

        :param name: Название услуги (если одна позиция)
        :param amount: Сумма услуги (если одна позиция)
        :param services: Список объектов ServiceCheck (если позиций несколько)
        :param client_name: ФИО/Название клиента
        :param client_phone: Телефон клиента
        :param client_email: Email клиента
        :param client_inn: ИНН клиента (обязательно для юр. лиц и ИП)
        :param client_type: Тип клиента (FROM_INDIVIDUAL, FROM_LEGAL_ENTITY, FROM_FOREIGN_AGENCY)
        :param payment_type: Тип оплаты (PHONE - СБП по номеру телефона, ACCOUNT - на банковский счет)
        :param phone: Номер телефона для получения оплаты (обязательно для PHONE)
        :param bank_name: Название банка
        :param bank_bik: БИК банка (обязательно для ACCOUNT)
        :param corr_account: Корреспондентский счет банка (обязательно для ACCOUNT)
        :param current_account: Расчетный счет (обязательно для ACCOUNT)

        :return: Invoice - модель с информацией о созданном счёте
        """

        final_services: list[dict] = []

        if services:
            for i, s in enumerate(services):
                final_services.append(
                    {
                        "name": s.name,
                        "amount": s.amount,
                        "quantity": s.quantity,
                        "serviceNumber": i,
                    }
                )
        elif name and amount is not None:
            final_services = [
                {
                    "name": name,
                    "amount": amount,
                    "quantity": 1,
                    "serviceNumber": 0,
                }
            ]
        else:
            raise ValidationError(
                "Необходимо указать либо (name и amount), либо список services"
            )

        validate_payment_type_params(
            payment_type, phone, bank_name, bank_bik, corr_account, current_account
        )
        validate_client_type_params(client_type, client_inn)

        total_sum = sum(s["amount"] * s["quantity"] for s in final_services)

        payload = build_payload(
            {
                "paymentType": payment_type.value,
                "type": "MANUAL",
                "services": final_services,
                "totalAmount": str(round(total_sum, 2)),
                "clientType": client_type.value,
            },
            clientName=client_name,
            clientPhone=client_phone,
            clientEmail=client_email,
            clientInn=client_inn,
            bankName=bank_name,
            phone=phone,
            bankBik=bank_bik,
            corrAccount=corr_account,
            currentAccount=current_account,
        )

        response = await self.request("POST", "invoice", json=payload)
        result = Invoice.model_validate(response)
        self._log("info", f"Счёт успешно создан, ID: {result.id}")
        return result

    async def cancel_bill(self, invoice_id: int) -> Invoice:
        """
        Аннулирование счёта.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/{invoice_id}/cancel

        :param invoice_id: ID счёта для аннулирования

        :return: Invoice - модель с информацией об аннулированном счёте
        """
        response = await self.request("POST", f"invoice/{invoice_id}/cancel")
        result = Invoice.model_validate(response)
        self._log("info", f"Счёт ID: {invoice_id} успешно аннулирован")
        return result

    async def get_bills(
        self,
        offset: int = 0,
        limit: int = 10,
        status: InvoiceStatus = InvoiceStatus.ALL,
        search: str | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
        sort_by: str = "createdAt",
        sort_desc: bool = True,
    ) -> InvoiceResponse:
        """
        Получение списка счетов.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/table

        :param offset: Смещение для пагинации
        :param limit: Лимит записей
        :param status: Статус счетов
        :param search: Поиск по ИНН или ФИО клиента
        :param date_from: Дата начала периода
        :param date_to: Дата окончания периода
        :param sort_by: Поле для сортировки (createdAt)
        :param sort_desc: Сортировка по убыванию

        :return: InvoiceResponse - список счетов с пагинацией
        """

        from_str, to_str = format_date_range(date_from, date_to)

        filtered = [
            {
                "id": "status",
                "value": status.value if isinstance(status, InvoiceStatus) else status,
            },
            {"id": "from", "value": from_str},
            {"id": "to", "value": to_str},
        ]

        if search:
            filtered.insert(1, {"id": "context", "value": search})

        payload = {
            "offset": offset,
            "limit": limit,
            "filtered": filtered,
            "sorted": [{"id": sort_by, "desc": sort_desc}],
        }

        response = await self.request("POST", "invoice/table", json=payload)
        result = InvoiceResponse.model_validate(response)
        self._log(
            "info",
            f"Получено счетов: {len(result.items)}, есть ещё: {result.has_more}",
        )
        return result

    async def get_payment_types(
        self,
        payment_type: InvoicePaymentType,
    ) -> list[PaymentTypeInfo]:
        """
        Получение реквизитов пользователя для получения оплаты.
        API Endpoint: https://lknpd.nalog.ru/api/v1/payment-type/table?type={type}

        :param payment_type: Тип реквизитов (PHONE - СБП, ACCOUNT - банковский счет)

        :return: Список реквизитов PaymentTypeInfo
        """
        response = await self.request(
            "GET", f"payment-type/table?type={payment_type.value}"
        )

        if isinstance(response, list):
            result = [PaymentTypeInfo.model_validate(item) for item in response]
            self._log("info", f"Получено реквизитов: {len(result)}")
            return result
        return []

    async def update_bill_payment_info(
        self,
        invoice_id: int,
        payment_type: InvoicePaymentType,
        phone: str | None = None,
        bank_name: str | None = None,
        bank_bik: str | None = None,
        corr_account: str | None = None,
        current_account: str | None = None,
    ) -> Invoice:
        """
        Изменение способа оплаты счёта.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/update-payment-info

        :param invoice_id: ID счёта
        :param payment_type: Тип оплаты (PHONE - СБП, ACCOUNT - на банковский счет)
        :param phone: Номер телефона для получения оплаты (для СБП)
        :param bank_name: Название банка
        :param bank_bik: БИК банка (для оплаты на счет)
        :param corr_account: Корреспондентский счет банка (для оплаты на счет)
        :param current_account: Расчетный счет (для оплаты на счет)

        :return: Invoice - модель с обновлённой информацией о счёте
        """

        validate_payment_type_params(
            payment_type, phone, bank_name, bank_bik, corr_account, current_account
        )

        payload = build_payload(
            {
                "invoiceId": invoice_id,
                "paymentType": payment_type.value,
            },
            bankName=bank_name,
            phone=phone,
            bankBik=bank_bik,
            corrAccount=corr_account,
            currentAccount=current_account,
        )

        response = await self.request(
            "POST", "invoice/update-payment-info", json=payload
        )
        result = Invoice.model_validate(response)
        self._log(
            "info", f"Платёжная информация для счёта ID: {invoice_id} успешно обновлена"
        )
        return result

    async def approve_bill(self, invoice_id: int) -> Invoice:
        """
        Пометить счёт как оплаченный.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/{invoice_id}/approve

        :param invoice_id: ID счёта

        :return: Invoice - модель с информацией об оплаченном счёте
        """
        response = await self.request("POST", f"invoice/{invoice_id}/approve")
        result = Invoice.model_validate(response)
        self._log("info", f"Счёт ID: {invoice_id} успешно отмечен как оплаченный")
        return result

    async def create_check_from_bill(
        self,
        invoice_id: int,
        operation_time: datetime.datetime | None = None,
    ) -> Invoice:
        """
        Создать чек на основе оплаченного счёта.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/{invoice_id}/approve

        :param invoice_id: ID счёта
        :param operation_time: Дата и время получения средств (если не указано - текущее время)

        :return: Invoice - модель с информацией о счёте с чеком
        """

        if operation_time is None:
            operation_time = datetime.datetime.now().astimezone()

        payload = {
            "operationTime": operation_time.isoformat(),
        }

        response = await self.request(
            "POST", f"invoice/{invoice_id}/approve", json=payload
        )
        result = Invoice.model_validate(response)
        self._log("info", f"Чек на основе счёта ID: {invoice_id} успешно создан")
        return result
