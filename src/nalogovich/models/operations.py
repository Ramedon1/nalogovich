from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ServiceCheck(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    name: str
    quantity: int
    amount: float


class Service(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    name: str
    quantity: int
    service_number: int
    amount: float


class Operation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    approved_receipt_uuid: str
    name: str
    services: list[Service]
    operation_time: str
    request_time: str
    register_time: str
    tax_period_id: int
    payment_type: str
    income_type: str
    partner_code: str | None = None
    total_amount: float
    cancellation_info: dict | None = None
    source_device_id: str
    client_inn: str | None = None
    client_display_name: str | None = None
    partner_display_name: str | None = None
    partner_logo: str | None = None
    partner_inn: str | None = None
    inn: str
    profession: str
    description: list[str] = []
    invoice_id: str | None = None


class OperationResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    content: list[Operation]
    has_more: bool
    current_offset: int
    current_limit: int


class Income(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    approved_receipt_uuid: str


class CancellationInfo(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    operation_time: str
    register_time: str
    tax_period_id: int
    comment: str


class IncomeInfo(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    approved_receipt_uuid: str
    name: str
    operation_time: str
    request_time: str
    payment_type: str
    partner_code: str | None = None
    total_amount: float
    cancellation_info: CancellationInfo | None = None
    source_device_id: str
