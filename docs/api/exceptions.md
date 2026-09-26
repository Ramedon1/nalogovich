# Исключения

Nalogovich использует собственные исключения для обработки ошибок.

!!! warning "Переименование модуля"
    Модуль `nalogovich.exeptions` был переименован в `nalogovich.exceptions`
    (исправлена опечатка в названии). Старый путь импорта
    `from nalogovich.exeptions import ...` пока продолжает работать, но считается
    устаревшим, выдаёт `DeprecationWarning` и будет удалён в одной из будущих
    версий. Используйте `from nalogovich.exceptions import ...`.

---

## NPDError

Базовое исключение для всех ошибок библиотеки.

::: nalogovich.exceptions.NPDError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Использование:**

```python
from nalogovich.exceptions import NPDError

try:
    # Ваш код
    pass
except NPDError as e:
    print(f"Ошибка библиотеки: {e}")
```

---

## ValidationError

Ошибка валидации входных данных перед отправкой на сервер.

::: nalogovich.exceptions.ValidationError
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
from nalogovich.exceptions import ValidationError

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

::: nalogovich.exceptions.ApiError
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
from nalogovich.exceptions import ApiError

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

::: nalogovich.exceptions.AuthenticationError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Атрибуты:**

- `message` (str) — текст ошибки
- `status_code` (int) — HTTP код ответа (по умолчанию 401)
- `response_data` (Any) — данные ответа от сервера

**Когда возникает:**

- ЛК НПД вернул HTTP 401, 403 или 422 при авторизации
- Не заданы ИНН и пароль для `auth()`

`EsiaAuthError` наследуется от `AuthenticationError`. При обработке входа через ЕСИА
перехватывайте `EsiaAuthError` раньше этого базового класса. Причину ответа HTTP 422
смотрите в тексте ошибки и `response_data`.

**Пример обработки:**

```python
from nalogovich.exceptions import AuthenticationError

try:
    await client.auth()
except AuthenticationError as e:
    print(f"Ошибка авторизации (HTTP {e.status_code}): {e}")
    if e.response_data is not None:
        print(f"Детали: {e.response_data}")
```

---

## EsiaAuthError

Ошибка авторизации на портале Госуслуг (ЕСИА). Наследуется от `AuthenticationError`,
поэтому существующий `except AuthenticationError` продолжает её ловить.

::: nalogovich.exceptions.EsiaAuthError
    options:
      show_root_heading: false
      heading_level: 4
      docstring_section_style: list

**Когда возникает:**

- Неверный логин или пароль Госуслуг
- Неверный или просроченный одноразовый код
- На аккаунте включён неподдерживаемый способ подтверждения (СМС, push)
- ЕСИА потребовала дополнительное действие (капча, подтверждение входа)

**Пример обработки:**

```python
from nalogovich.exceptions import EsiaAuthError
from nalogovich.lknpd import NpdClient

try:
    client = await NpdClient.from_esia(
        login="79001234567",
        password="пароль_от_госуслуг",
        totp_secret="JBSWY3DPEHPK3PXP",
    )
except EsiaAuthError as e:
    print(f"❌ Госуслуги не пустили: {e}")
    print(f"HTTP код: {e.status_code}")
    print(f"Ответ ЕСИА: {e.response_data}")
```
