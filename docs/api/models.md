# Модели данных

Все модели данных используют **Pydantic** для валидации и сериализации.

---

## Чеки и операции

### ServiceCheck

Позиция в чеке (услуга или товар).

::: nalogovich.models.operations.ServiceCheck
    options:
      show_root_heading: false
      heading_level: 4
      show_signature_annotations: true
      docstring_section_style: list

**Пример использования:**

```python
from nalogovich.models.operations import ServiceCheck

service = ServiceCheck(
    name="Разработка сайта",
    amount=30000.00,
    quantity=1
)
```

---

### Operation

Информация о зарегистрированной операции (чеке).

::: nalogovich.models.operations.Operation
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

---

### OperationResponse

Ответ API со списком операций (чеков).

::: nalogovich.models.operations.OperationResponse
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Пример:**

```python
response = await client.get_checks()

print(f"Всего чеков: {len(response.content)}")
print(f"Есть ещё: {response.has_more}")
print(f"Смещение: {response.current_offset}")
print(f"Лимит: {response.current_limit}")
```

---

### Income

Информация о созданном доходе (чеке).

::: nalogovich.models.operations.Income
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

---

### IncomeInfo

Подробная информация о доходе.

::: nalogovich.models.operations.IncomeInfo
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

---

## Счета

### Invoice

Информация о счёте.

::: nalogovich.models.operations.Invoice
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Ключевые поля:**

- `invoice_id` — уникальный ID счёта
- `payment_url` — ссылка для оплаты
- `status` — статус счёта
- `total_amount` — общая сумма
- `client_name` — имя клиента

---

### InvoiceResponse

Ответ API со списком счетов.

::: nalogovich.models.operations.InvoiceResponse
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

---

### PaymentTypeInfo

Информация о реквизитах для получения оплаты.

::: nalogovich.models.operations.PaymentTypeInfo
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Пример:**

```python
from nalogovich.enums import InvoicePaymentType

payment_types = await client.get_payment_types(
    payment_type=InvoicePaymentType.PHONE
)

for pt in payment_types:
    print(f"{pt.phone} - {pt.bank_name}")
```
