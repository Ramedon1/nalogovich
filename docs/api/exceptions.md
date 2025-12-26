# Исключения

Nalogovich использует собственные исключения для обработки ошибок.

---

## NPDError

Базовое исключение для всех ошибок библиотеки.

::: nalogovich.exeptions.NPDError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Использование:**

```python
from nalogovich.exeptions import NPDError

try:
    # Ваш код
    pass
except NPDError as e:
    print(f"Ошибка библиотеки: {e}")
```

---

## ValidationError

Ошибка валидации входных данных перед отправкой на сервер.

::: nalogovich.exeptions.ValidationError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Когда возникает:**

- Не указаны обязательные параметры
- Неправильный формат данных
- Логические ошибки в параметрах

**Пример:**

```python
from nalogovich.exeptions import ValidationError

try:
    # Не указано ни name/amount, ни services
    income = await client.create_check(
        payment_type=PaymentType.CASH
    )
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
    # Вывод: Необходимо указать либо (name и amount), либо список services
```

**Другие примеры:**

```python
# Для СБП не указан номер телефона
try:
    invoice = await client.create_bill(
        name="Услуга",
        amount=5000.00,
        payment_type=InvoicePaymentType.PHONE,
        # phone не указан!
        bank_name="Сбербанк"
    )
except ValidationError as e:
    print(e)  # ValidationError о необходимости указать phone
```

---

## ApiError

Ошибка, возвращённая сервером API ФНС.

::: nalogovich.exeptions.ApiError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Атрибуты:**

- `message` (str) — текст ошибки
- `status_code` (int) — HTTP код ответа
- `response_data` (Any) — данные ответа от сервера

**Пример обработки:**

```python
from nalogovich.exeptions import ApiError

try:
    checks = await client.get_checks()
except ApiError as e:
    print(f"Ошибка API: {e}")
    print(f"HTTP код: {e.status_code}")
    print(f"Данные ответа: {e.response_data}")
    
    if e.status_code == 500:
        print("Проблемы на стороне сервера ФНС")
    elif e.status_code == 404:
        print("Ресурс не найден")
```

---

## AuthenticationError

Ошибка авторизации.

::: nalogovich.exeptions.AuthenticationError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Атрибуты:**

- `message` (str) — текст ошибки
- `status_code` (int) — HTTP код ответа (по умолчанию 401)
- `response_data` (Any) — данные ответа от сервера

**Когда возникает:**

- Неверный ИНН или пароль (422)
- Неавторизован (401)
- Доступ запрещён (403)

**Пример обработки:**

```python
from nalogovich.exeptions import AuthenticationError

try:
    await client.auth()
except AuthenticationError as e:
    if e.status_code == 422:
        print("❌ Неверный ИНН или пароль")
    elif e.status_code == 401:
        print("❌ Неавторизован. Проверьте учетные данные")
    elif e.status_code == 403:
        print("❌ Доступ запрещён. Возможно, аккаунт заблокирован")
    
    print(f"Детали: {e.response_data}")
```