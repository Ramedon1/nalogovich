import enum


class SortBy(str, enum.Enum):
    """
    Типы сортировок операций

    operation_time_asc: Сортировка по дате (Сначала старые)
    operation_time_desc: Сортировка по дате (Сначала новые)
    total_amount_asc: Сортировка по стоимости (По возрастанию)
    total_amount_desc: Сортировка по стоимости (По убыванию)
    """

    operation_time_asc = "operation_time:asc"
    operation_time_desc = "operation_time:desc"
    total_amount_asc = "total_amount:asc"
    total_amount_desc = "total_amount:desc"


class CommentReturn(str, enum.Enum):
    """
    Типы возвратов с комментарием
    """

    wrong_receipt = "Чек сформирован ошибочно"
    receipt_return = "Чек возвращен"


class PaymentType(str, enum.Enum):
    """
    Типы оплаты
    CASH: Наличный расчет / Карта
    ACCOUNT: Безналичный расчет (на счет)
    """

    CASH = "CASH"
    ACCOUNT = "ACCOUNT"


class InvoiceStatus(str, enum.Enum):
    """
    Статусы счетов

    CREATED: Создан
    PAID: Оплачен
    TO_PAYMENT: К оплате
    FUND_RECEIVED: Средства получены
    PAID_WITH_RECEIPT: Оплачен с чеком
    PAID_WITHOUT_RECEIPT: Оплачен без чека
    CANCELLED: Аннулирован
    ERROR: Ошибка
    ALL: Все статусы (для фильтрации)
    """

    CREATED = "CREATED"
    PAID = "PAID"
    TO_PAYMENT = "TO_PAYMENT"
    FUND_RECEIVED = "FUND_RECEIVED"
    PAID_WITH_RECEIPT = "PAID_WITH_RECEIPT"
    PAID_WITHOUT_RECEIPT = "PAID_WITHOUT_RECEIPT"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"
    ALL = "ALL"


class InvoicePaymentType(str, enum.Enum):
    """
    Типы оплаты для счёта
    PHONE: Оплата по номеру телефона (СБП)
    ACCOUNT: Оплата на расчетный счет
    """

    PHONE = "PHONE"
    ACCOUNT = "ACCOUNT"


class InvoiceClientType(str, enum.Enum):
    """
    Типы клиентов для счёта
    FROM_INDIVIDUAL: От физического лица
    FROM_LEGAL_ENTITY: От юридического лица или ИП
    FROM_FOREIGN_AGENCY: От иностранной организации
    """

    FROM_INDIVIDUAL = "FROM_INDIVIDUAL"
    FROM_LEGAL_ENTITY = "FROM_LEGAL_ENTITY"
    FROM_FOREIGN_AGENCY = "FROM_FOREIGN_AGENCY"


class IncomeType(str, enum.Enum):
    """
    Типы клиентов для доходов
    FROM_INDIVIDUAL: От физического лица
    FROM_LEGAL_ENTITY: От юридического лица или ИП
    FROM_FOREIGN_AGENCY: От иностранной организации
    """

    FROM_INDIVIDUAL = "FROM_INDIVIDUAL"
    FROM_LEGAL_ENTITY = "FROM_LEGAL_ENTITY"
    FROM_FOREIGN_AGENCY = "FROM_FOREIGN_AGENCY"


class ReceiptType(str, enum.Enum):
    """
    Типы чеков при фильтрации

    REGISTERED: Действителен чек
    CANCELLED: Аннулирован чек
    """

    REGISTERED = "REGISTERED"
    CANCELLED = "CANCELLED"


class BuyerType(str, enum.Enum):
    """
    Тип покупателя

    PERSON - Физ.лицо
    COMPANY - Юр.лицо
    FOREIGN_AGENCY - Иностранная организация
    """

    PERSON = "PERSON"
    COMPANY = "COMPANY"
    FOREIGN_AGENCY = "FOREIGN_AGENCY"
