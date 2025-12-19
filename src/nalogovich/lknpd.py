from __future__ import annotations

import datetime
import aiohttp
from typing import Any
from dateutil.relativedelta import relativedelta

from src.nalogovich.enums import PaymentType, SortBy, CommentReturn
from src.nalogovich.exeptions import ValidationError
from src.nalogovich.models.operations import (
    ServiceCheck,
    OperationResponse,
    Income,
    IncomeInfo,
)
from src.nalogovich.utils.checks import prepare_client_payload


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
        payload = {
            "username": self.inn,
            "password": self.password,
            "deviceInfo": self.device_info,
        }
        response = await self.request("POST", "auth/lkfl", json=payload)

        if token := response.get("token"):
            self.token = token
            self.refresh_token = response.get("refreshToken")
            self.headers["Authorization"] = f"Bearer {token}"
            if self.session and not self.session.closed:
                self.session.headers.update({"Authorization": f"Bearer {token}"})

        return response

    async def re_auth(self):
        if not self.refresh_token:
            return await self.auth()

        payload = {
            "refreshToken": self.refresh_token,
            "deviceInfo": self.device_info,
        }
        response = await self.request("POST", "auth/token", json=payload)

        if token := response.get("token"):
            self.token = token
            self.refresh_token = response.get("refreshToken")
            self.headers["Authorization"] = f"Bearer {token}"
            if self.session and not self.session.closed:
                self.session.headers.update({"Authorization": f"Bearer {token}"})

        return response

    async def get_checks(
        self,
        from_date: datetime.datetime | None = (
            datetime.datetime.now() - relativedelta(months=1)
        ).replace(day=1),
        to_date: datetime.datetime | None = datetime.datetime.now(),
        offset: int | None = 0,
        limit: int | None = 10,
        sort_by: SortBy | None = SortBy.operation_time_desc,
    ) -> OperationResponse:
        """
        Метод для получения чеков в истории за определенный период
        API Endpoint: https://lknpd.nalog.ru/api/v1/incomes

        :param from_date: Дата с которой будет браться информация о чеках
        :param to_date: Дата по которой будет браться информация о чеках
        :param offset: Смещение для пагинации
        :param limit: Количество записей на страницу
        :param sort_by: Сортировка записей по определенному параметру
        :return: OperationResponse - модель с информацией о чеках
        """
        params = {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "offset": offset,
            "limit": limit,
            "sort_by": sort_by.value if sort_by else None,
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
