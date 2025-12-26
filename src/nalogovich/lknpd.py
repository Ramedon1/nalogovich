from __future__ import annotations

import datetime
import aiohttp
from typing import Any
from dateutil.relativedelta import relativedelta

from src.nalogovich.enums import (
    PaymentType,
    SortBy,
    CommentReturn,
    ReceiptType,
    BuyerType,
    InvoicePaymentType,
    InvoiceClientType,
    InvoiceStatus,
)
from src.nalogovich.exeptions import ValidationError, AuthenticationError, ApiError
from src.nalogovich.models.operations import (
    ServiceCheck,
    OperationResponse,
    Income,
    IncomeInfo,
    Invoice,
    InvoiceResponse,
    PaymentTypeInfo,
)
from src.nalogovich.utils.checks import prepare_client_payload
from src.nalogovich.utils.formatters import format_date_range, build_payload
from src.nalogovich.utils.validators import (
    validate_payment_type_params,
    validate_client_type_params,
)


class NpdClient:
    def __init__(
        self,
        inn: str,
        password: str,
    ):
        self.base_url = "https://lknpd.nalog.ru/api/v1/"
        self.inn = inn
        self.password = password
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        self.device_info = {
            "sourceDeviceId": "-YWmoFV_Tw8ATGRD8Zym3",
            "sourceType": "WEB",
            "appVersion": "1.0.0",
            "metaDetails": {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            },
        }
        self.token: str | None = None
        self.refresh_token: str | None = None
        self.session: aiohttp.ClientSession | None = None

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
        """
        payload = {
            "username": self.inn,
            "password": self.password,
            "deviceInfo": self.device_info,
        }

        session = await self.get_session()
        try:
            async with session.request(
                "POST", self.base_url + "auth/lkfl", json=payload
            ) as response:
                response_data = None
                if "application/json" in response.headers.get("Content-Type", ""):
                    response_data = await response.json()

                if response.status == 422:
                    error_message = "Неверный ИНН или пароль"
                    if response_data:
                        error_message = response_data.get("message", error_message)
                    raise AuthenticationError(
                        error_message, status_code=422, response_data=response_data
                    )

                if response.status == 401:
                    raise AuthenticationError(
                        "Неавторизован. Проверьте учетные данные.",
                        status_code=401,
                        response_data=response_data,
                    )

                if response.status == 403:
                    raise AuthenticationError(
                        "Доступ запрещен. Возможно, аккаунт заблокирован.",
                        status_code=403,
                        response_data=response_data,
                    )

                if response.status >= 400:
                    error_message = f"Ошибка авторизации: HTTP {response.status}"
                    if response_data and isinstance(response_data, dict):
                        error_message = response_data.get("message", error_message)
                    raise ApiError(
                        error_message,
                        status_code=response.status,
                        response_data=response_data,
                    )

                if token := response_data.get("token"):
                    self.token = token
                    self.refresh_token = response_data.get("refreshToken")
                    self.headers["Authorization"] = f"Bearer {token}"
                    if self.session and not self.session.closed:
                        self.session.headers.update(
                            {"Authorization": f"Bearer {token}"}
                        )

                return response_data

        except aiohttp.ClientError as e:
            raise ApiError(f"Ошибка сети при авторизации: {e}", status_code=0)

    async def re_auth(self):
        """
        Повторная авторизация через refresh token.

        :raises AuthenticationError: При невалидном refresh token
        :raises ApiError: При других ошибках API
        """
        if not self.refresh_token:
            return await self.auth()

        payload = {
            "refreshToken": self.refresh_token,
            "deviceInfo": self.device_info,
        }

        session = await self.get_session()
        try:
            async with session.request(
                "POST", self.base_url + "auth/token", json=payload
            ) as response:
                response_data = None
                if "application/json" in response.headers.get("Content-Type", ""):
                    response_data = await response.json()

                if response.status in (401, 422):
                    self.refresh_token = None
                    return await self.auth()

                if response.status >= 400:
                    error_message = f"Ошибка обновления токена: HTTP {response.status}"
                    if response_data and isinstance(response_data, dict):
                        error_message = response_data.get("message", error_message)
                    raise ApiError(
                        error_message,
                        status_code=response.status,
                        response_data=response_data,
                    )

                if token := response_data.get("token"):
                    self.token = token
                    self.refresh_token = response_data.get("refreshToken")
                    self.headers["Authorization"] = f"Bearer {token}"
                    if self.session and not self.session.closed:
                        self.session.headers.update(
                            {"Authorization": f"Bearer {token}"}
                        )

                return response_data

        except aiohttp.ClientError as e:
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
        return OperationResponse.model_validate(response)

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
        return Income.model_validate(response)

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
        return IncomeInfo.model_validate(response.get("incomeInfo", response))

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
        return Invoice.model_validate(response)

    async def cancel_bill(self, invoice_id: int) -> Invoice:
        """
        Аннулирование счёта.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/{invoice_id}/cancel

        :param invoice_id: ID счёта для аннулирования

        :return: Invoice - модель с информацией об аннулированном счёте
        """
        response = await self.request("POST", f"invoice/{invoice_id}/cancel")
        return Invoice.model_validate(response)

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
        return InvoiceResponse.model_validate(response)

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
            return [PaymentTypeInfo.model_validate(item) for item in response]
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
        return Invoice.model_validate(response)

    async def approve_bill(self, invoice_id: int) -> Invoice:
        """
        Пометить счёт как оплаченный.
        API Endpoint: https://lknpd.nalog.ru/api/v1/invoice/{invoice_id}/approve

        :param invoice_id: ID счёта

        :return: Invoice - модель с информацией об оплаченном счёте
        """
        response = await self.request("POST", f"invoice/{invoice_id}/approve")
        return Invoice.model_validate(response)

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
        return Invoice.model_validate(response)
