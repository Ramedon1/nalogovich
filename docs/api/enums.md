# Перечисления (Enums)

Все перечисления используются для указания типов, статусов и других параметров.

---

## PaymentType

Тип оплаты при создании чека.

::: nalogovich.enums.PaymentType
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `CASH` — наличный расчёт или оплата картой
- `ACCOUNT` — безналичный расчёт (на счёт)

**Пример:**

```python
from nalogovich.enums import PaymentType

income = await client.create_check(
    name="Консультация",
    amount=5000.00,
    payment_type=PaymentType.CASH
)
```

---

## SortBy

Параметры сортировки для списка чеков.

::: nalogovich.enums.SortBy
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `operation_time_asc` — по дате (старые → новые)
- `operation_time_desc` — по дате (новые → старые) ⭐ *по умолчанию*
- `total_amount_asc` — по сумме (возрастание)
- `total_amount_desc` — по сумме (убывание)

**Пример:**

```python
from nalogovich.enums import SortBy

response = await client.get_checks(
    sort_by=SortBy.total_amount_desc
)
```

---

## ReceiptType

Тип чека при фильтрации.

::: nalogovich.enums.ReceiptType
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `REGISTERED` — действующие чеки
- `CANCELLED` — аннулированные чеки

**Пример:**

```python
from nalogovich.enums import ReceiptType

# Только действующие чеки
response = await client.get_checks(
    receipt_type=ReceiptType.REGISTERED
)
```

---

## BuyerType

Тип покупателя/клиента.

::: nalogovich.enums.BuyerType
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `PERSON` — физическое лицо
- `COMPANY` — юридическое лицо
- `FOREIGN_AGENCY` — иностранная организация

**Пример:**

```python
from nalogovich.enums import BuyerType

# Только чеки от юр. лиц
response = await client.get_checks(
    buyer_type=BuyerType.COMPANY
)
```

---

## CommentReturn

Причина аннулирования чека.

::: nalogovich.enums.CommentReturn
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `wrong_receipt` — "Чек сформирован ошибочно"
- `receipt_return` — "Чек возвращен"

**Пример:**

```python
from nalogovich.enums import CommentReturn

await client.cancel_check(
    receipt_uuid="200bzznrt0",
    comment=CommentReturn.wrong_receipt
)
```

---

## InvoicePaymentType

Способ оплаты для счёта.

::: nalogovich.enums.InvoicePaymentType
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `PHONE` — оплата по номеру телефона (СБП)
- `ACCOUNT` — оплата на расчётный счёт

**Пример:**

```python
from nalogovich.enums import InvoicePaymentType

invoice = await client.create_bill(
    name="Услуга",
    amount=10000.00,
    client_name="Клиент",
    payment_type=InvoicePaymentType.PHONE,  # СБП
    phone="+79001234567",
    bank_name="Сбербанк"
)
```

---

## InvoiceClientType

Тип клиента для счёта.

::: nalogovich.enums.InvoiceClientType
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `FROM_INDIVIDUAL` — физическое лицо
- `FROM_LEGAL_ENTITY` — юридическое лицо или ИП
- `FROM_FOREIGN_AGENCY` — иностранная организация

**Пример:**

```python
from nalogovich.enums import InvoiceClientType

invoice = await client.create_bill(
    name="Услуга",
    amount=10000.00,
    client_name="ООО Ромашка",
    client_inn="7743013902",  # Обязательно для юр. лиц
    client_type=InvoiceClientType.FROM_LEGAL_ENTITY,
    payment_type=InvoicePaymentType.PHONE,
    phone="+79001234567"
)
```

---

## InvoiceStatus

Статус счёта.

::: nalogovich.enums.InvoiceStatus
    options:
      show_root_heading: false
      heading_level: 4
      show_docstring_description: false

**Значения:**

- `CREATED` — создан
- `TO_PAYMENT` — к оплате
- `PAID` — оплачен
- `FUND_RECEIVED` — средства получены
- `PAID_WITH_RECEIPT` — оплачен с чеком
- `PAID_WITHOUT_RECEIPT` — оплачен без чека
- `CANCELLED` — аннулирован
- `ERROR` — ошибка
- `ALL` — все статусы (для фильтрации)

**Пример:**

```python
from nalogovich.enums import InvoiceStatus

# Получить только оплаченные счета
response = await client.get_bills(
    status=InvoiceStatus.PAID
)
```

---

## IncomeType

Тип клиента для доходов (аналогично `InvoiceClientType`).

::: nalogovich.enums.IncomeType
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list
      show_docstring_description: false

**Значения:**

- `FROM_INDIVIDUAL` — от физического лица
- `FROM_LEGAL_ENTITY` — от юридического лица или ИП
- `FROM_FOREIGN_AGENCY` — от иностранной организации
