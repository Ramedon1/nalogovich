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
