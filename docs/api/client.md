# NpdClient

**`NpdClient`** — основной класс для взаимодействия с API "Мой Налог" (lknpd.nalog.ru).

Класс предоставляет асинхронный интерфейс для:

- 🔐 Авторизации и управления сессией
- 🧾 Создания и управления чеками
- 💰 Работы со счетами на оплату  
- 📊 Получения статистики и истории операций

---

## Быстрый старт

```python
from nalogovich import NpdClient

async with NpdClient(inn="ваш_инн", password="ваш_пароль") as client:
    # Авторизация
    await client.auth()
    
    # Создание чека
    income = await client.create_check(
        name="Консультация",
        amount=5000.00
    )
    print(f"Чек создан: {income.receipt_id}")
```

---

## Основные группы методов

### 🔐 Авторизация
- [`auth()`](#nalogovich.lknpd.NpdClient.auth) — авторизация через ЛК ФЛ
- [`auth_esia()`](#nalogovich.lknpd.NpdClient.auth_esia) — авторизация через Госуслуги (ЕСИА)
- [`from_esia()`](#nalogovich.lknpd.NpdClient.from_esia) — создать клиент и сразу войти через Госуслуги
- [`from_token()`](#nalogovich.lknpd.NpdClient.from_token) — восстановить сессию из сохранённых токенов
- [`auth_with_token()`](#nalogovich.lknpd.NpdClient.auth_with_token) — подставить токены в существующий клиент
- [`export_session()`](#nalogovich.lknpd.NpdClient.export_session) — выгрузить токены для повторного входа
- [`re_auth()`](#nalogovich.lknpd.NpdClient.re_auth) — обновление токена

### 🧾 Работа с чеками
- [`create_check()`](#nalogovich.lknpd.NpdClient.create_check) — создание чека (регистрация дохода)
- [`cancel_check()`](#nalogovich.lknpd.NpdClient.cancel_check) — аннулирование чека
- [`get_checks()`](#nalogovich.lknpd.NpdClient.get_checks) — получение списка чеков
- [`create_check_from_bill()`](#nalogovich.lknpd.NpdClient.create_check_from_bill) — создание чека из оплаченного счёта

### 💰 Работа со счетами
- [`create_bill()`](#nalogovich.lknpd.NpdClient.create_bill) — создание счёта на оплату
- [`get_bills()`](#nalogovich.lknpd.NpdClient.get_bills) — получение списка счетов
- [`approve_bill()`](#nalogovich.lknpd.NpdClient.approve_bill) — подтверждение оплаты счёта
- [`cancel_bill()`](#nalogovich.lknpd.NpdClient.cancel_bill) — аннулирование счёта
- [`update_bill_payment_info()`](#nalogovich.lknpd.NpdClient.update_bill_payment_info) — обновление платёжной информации счёта

### 📊 Дополнительно
- [`get_payment_types()`](#nalogovich.lknpd.NpdClient.get_payment_types) — список реквизитов для оплаты

---

## Справочник методов

::: nalogovich.lknpd.NpdClient
    options:
      show_root_heading: false
      show_source: false
      heading_level: 3
      members_order: source
      group_by_category: true
      show_category_heading: true
      show_signature_annotations: true
      separate_signature: true
      merge_init_into_class: true
      docstring_section_style: list
