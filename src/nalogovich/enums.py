import enum


class SortBy(enum.Enum):
    """
    Типы сортировок операций

    operation_time_asc: Сортировка по дате (Сначала старые)
    operation_time_desc: Сортировка по дате (Сначала новые)
    total_amount_asc: Сортировка по стоимости (По возрастанию)
    total_amount_desc: Сортировка по стоимости (По убываению)
    """

    operation_time_asc = "operation_time:asc"
    operation_time_desc = "operation_time:desc"
    total_amount_asc = "total_amount:asc"
    total_amount_desc = "total_amount:desc"
