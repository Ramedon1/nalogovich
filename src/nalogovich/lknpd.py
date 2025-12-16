from __future__ import annotations

import datetime
import aiohttp
from typing import Any
from dateutil.relativedelta import relativedelta

from nalogovich.enums import SortBy
from nalogovich.models.operations import OperationResponse


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

        except aiohttp.ClientError as e:
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
            self.refresh_token = response.get(
                "refreshToken"
            )  # Изменено с refresh_token на refreshToken
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

        :param from_date:
        :param to_date:
        :param offset:
        :param limit:
        :param sort_by:
        :return:
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
