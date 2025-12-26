from src.nalogovich.enums import InvoicePaymentType, InvoiceClientType
from src.nalogovich.exeptions import ValidationError


def validate_payment_type_params(
    payment_type: InvoicePaymentType,
    phone: str | None = None,
    bank_name: str | None = None,
    bank_bik: str | None = None,
    corr_account: str | None = None,
    current_account: str | None = None,
) -> None:
    """
    Валидирует параметры в зависимости от типа оплаты.

    :param payment_type: Тип оплаты
    :param phone: Телефон (для PHONE)
    :param bank_name: Название банка
    :param bank_bik: БИК банка (для ACCOUNT)
    :param corr_account: Корр. счет (для ACCOUNT)
    :param current_account: Расчетный счет (для ACCOUNT)
    :raises ValidationError: При недостающих параметрах
    """

    if payment_type == InvoicePaymentType.PHONE:
        if not phone or not bank_name:
            raise ValidationError(
                "Для оплаты по СБП (PHONE) необходимо указать phone и bank_name"
            )

    elif payment_type == InvoicePaymentType.ACCOUNT:
        if not all([bank_name, bank_bik, corr_account, current_account]):
            raise ValidationError(
                "Для оплаты на счёт (ACCOUNT) необходимо указать bank_name, bank_bik, corr_account и current_account"
            )


def validate_client_type_params(
    client_type: InvoiceClientType,
    client_inn: str | None = None,
) -> None:
    """
    Валидирует параметры клиента в зависимости от типа.

    :param client_type: Тип клиента
    :param client_inn: ИНН клиента
    :raises ValidationError: При недостающих параметрах
    """
    if client_type == InvoiceClientType.FROM_LEGAL_ENTITY and not client_inn:
        raise ValidationError(
            "Для юр. лиц и ИП (FROM_LEGAL_ENTITY) необходимо указать client_inn"
        )
