from src.nalogovich.enums import IncomeType
from src.nalogovich.exeptions import ValidationError


def prepare_client_payload(is_business, is_foreign, inn, name):
    """Вспомогательный метод для формирования пайлода для чека"""

    if is_foreign:
        if not name:
            raise ValidationError("Имя обязательно для иностранцев")
        return {"incomeType": IncomeType.FROM_FOREIGN_AGENCY.value, "displayName": name}
    if is_business:
        if not inn:
            raise ValidationError("ИНН обязателен для бизнеса")
        return {
            "incomeType": IncomeType.FROM_LEGAL_ENTITY.value,
            "inn": inn,
            "displayName": name,
        }

    return {
        "incomeType": IncomeType.FROM_INDIVIDUAL.value,
        "displayName": None,
        "inn": None,
    }
