from __future__ import annotations

import datetime
import aiohttp
from typing import Any
from dateutil.relativedelta import relativedelta

from nalogovich.enums import SortBy, CommentReturn
from nalogovich.models.operations import OperationResponse, Income, IncomeInfo


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
        name: str,
        amount: float,
        is_foreign_organization: bool = False,
        inn_of_organization: str | None = None,
        name_of_organization: str | None = None,
        date_of_sale: datetime.datetime | None = None,
        is_business: bool = False,
    ) -> Income:
        """
        Метод для создания чека (регистрации дохода)
        API Endpoint: https://lknpd.nalog.ru/api/v1/income
        :param name: Название услуги или товара
        :param amount: Сумма услуги или товара
        :param is_foreign_organization: Является ли организация иностранной
        :param inn_of_organization: ИНН организации (если бизнес)
        :param name_of_organization: Название организации (если иностранная организация или бизнес)
        :param date_of_sale: Дата продажи (если не указана, будет использовано текущее время)
        :param is_business: Является ли клиент бизнесом

        :return: Income - модель с информацией о созданном чеке
        """

        dt = date_of_sale if date_of_sale else datetime.datetime.now().astimezone()
        formatted_time = dt.isoformat()

        client = {}

        if is_foreign_organization:
            client["incomeType"] = "FROM_FOREIGN_AGENCY"
            client["displayName"] = name_of_organization
        elif is_business:
            client["incomeType"] = "FROM_LEGAL_ENTITY"
            client["inn"] = inn_of_organization
            client["displayName"] = name_of_organization
        else:
            client["incomeType"] = "FROM_INDIVIDUAL"
            client["displayName"] = None
            client["inn"] = None
            client["contactPhone"] = None

        payload = {
            "operationTime": formatted_time,
            "requestTime": datetime.datetime.now().astimezone().isoformat(),
            "services": [{"name": name, "amount": amount, "quantity": 1}],
            "totalAmount": str(amount),
            "client": client,
            "paymentType": "CASH",  # Valid values: "CASH" (Cash/Card) or "ACCOUNT" (Transfer)
            "ignoreMaxTotalIncomeRestriction": False,
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
