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


class ReceiptTemplate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    profession: str | None = None
    receipt_phone: str | None = None
    receipt_email: str | None = None
    description: str | None = None


class Invoice(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    invoice_id: int | None = None
    uuid: str | None = None
    receipt_id: str | None = None
    fid: int | None = None
    type: str | None = None
    status: str | None = None
    merchant_id: str | None = None
    acquirer_id: str | None = None
    acquirer_name: str | None = None
    payment_url: str | None = None
    payment_type: str | None = None
    bank_name: str | None = None
    bank_bik: str | None = None
    current_account: str | None = None
    corr_account: str | None = None
    phone: str | None = None
    client_type: str | None = None
    client_name: str | None = None
    client_inn: str | None = None
    client_phone: str | None = None
    client_email: str | None = None
    total_amount: float | None = None
    total_tax: float | None = None
    services: list | None = None
    created_at: str | None = None
    paid_at: str | None = None
    cancelled_at: str | None = None
    transition_page_url: str | None = None
    commission: float | None = None
    receipt_template: ReceiptTemplate | None = None
    auto_create_receipt: bool | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    items: list[Invoice]
    has_more: bool
    current_offset: int
    current_limit: int


class PaymentTypeInfo(BaseModel):
    """Реквизиты для получения оплаты"""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )

    id: int | None = None
    type: str | None = None
    bank_name: str | None = None
    bank_bik: str | None = None
    corr_account: str | None = None
    current_account: str | None = None
    phone: str | None = None
    is_default: bool | None = None
