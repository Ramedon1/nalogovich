# Работа со счетами

Счета позволяют выставлять счёта для оплаты услуг. После оплаты счёта можно автоматически создать чек.

## Создание счёта

### Базовый счёт для физического лица

Простой пример создания счёта с оплатой через СБП:

```python
from nalogovich.lknpd import NpdClient
from nalogovich.enums import InvoicePaymentType, InvoiceClientType

async def create_simple_invoice():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice = await client.create_bill(
            name="Консультация по веб-разработке",
            amount=10000.00,
            client_name="Иван Петров",
            client_phone="+79001234567",
            client_email="ivan@example.com",
            client_type=InvoiceClientType.FROM_INDIVIDUAL,
            payment_type=InvoicePaymentType.PHONE,  # Оплата через СБП
            phone="+79009876543",  # Ваш номер для получения оплаты
            bank_name="Сбербанк"
        )
        
        print(f"✅ Счёт создан!")
        print(f"ID: {invoice.invoice_id}")
```

### Счёт с несколькими позициями

```python
from nalogovich.models.operations import ServiceCheck

async def create_multi_item_invoice():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        services = [
            ServiceCheck(name="Дизайн главной страницы", amount=15000.00, quantity=1),
            ServiceCheck(name="Вёрстка", amount=20000.00, quantity=1),
            ServiceCheck(name="Интеграция с backend", amount=25000.00, quantity=1),
        ]
        
        invoice = await client.create_bill(
            services=services,
            client_name="ООО Технологии",
            client_inn="7743013902",  # Обязательно для юр. лиц
            client_type=InvoiceClientType.FROM_LEGAL_ENTITY,
            payment_type=InvoicePaymentType.PHONE,
            phone="+79009876543",
            bank_name="Тинькофф"
        )
        
        total = sum(s.amount * s.quantity for s in services)
        print(f"✅ Счёт на {total:,.0f} ₽ создан")
```

!!! warning "Юридические лица"
    Для юридических лиц (`InvoiceClientType.FROM_LEGAL_ENTITY`) обязательно указывайте `client_inn`.

### Счёт с оплатой на банковский счёт

Вместо СБП можно указать банковский счёт:

```python
async def create_invoice_with_bank_account():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice = await client.create_bill(
            name="Разработка мобильного приложения",
            amount=150000.00,
            client_name="ООО Инновации",
            client_inn="7743013902",
            client_type=InvoiceClientType.FROM_LEGAL_ENTITY,
            payment_type=InvoicePaymentType.ACCOUNT,  # Оплата на счёт
            bank_name="Тинькофф Банк",
            bank_bik="044525974",
            corr_account="30101810145250000974",
            current_account="40817810099910004312"
        )
        
        print(f"✅ Счёт создан с реквизитами для оплаты на счёт")
```

!!! warning "Обязательные поля"
    При `payment_type=InvoicePaymentType.ACCOUNT` необходимо указать:
    
    - `bank_name` — название банка
    - `bank_bik` — БИК банка
    - `corr_account` — корреспондентский счёт
    - `current_account` — расчётный счёт

### Счёт для иностранной организации

```python
async def create_invoice_for_foreign():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice = await client.create_bill(
            name="Software development services",
            amount=50000.00,
            client_name="Foreign Company Ltd",
            client_type=InvoiceClientType.FROM_FOREIGN_AGENCY,  # Иностранная организация
            payment_type=InvoicePaymentType.PHONE,
            phone="+79009876543",
            bank_name="Сбербанк"
        )
        
        print(f"✅ Счёт для иностранной организации создан")
```

## Получение списка счетов

### Все счета

```python
async def get_all_invoices():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        response = await client.get_bills()
        
        print(f"Всего счетов: {len(response.items)}")
        
        for invoice in response.items:
            print(f"  Счёт №{invoice.invoice_id}")
            print(f"  Статус: {invoice.status}")
            print(f"  Сумма: {invoice.total_amount} ₽")
            print(f"  Клиент: {invoice.client_name}")
            print(f"  Создан: {invoice.created_at}")
```

### Фильтрация по статусу

```python
from nalogovich.enums import InvoiceStatus

async def get_paid_invoices():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Только оплаченные счета
        response = await client.get_bills(
            status=InvoiceStatus.PAID
        )
        
        print(f"Оплаченных счетов: {len(response.items)}")
```

Доступные статусы:

| Статус | Описание |
|--------|----------|
| `InvoiceStatus.CREATED` | Создан |
| `InvoiceStatus.TO_PAYMENT` | К оплате |
| `InvoiceStatus.PAID` | Оплачен |
| `InvoiceStatus.FUND_RECEIVED` | Средства получены |
| `InvoiceStatus.PAID_WITH_RECEIPT` | Оплачен с чеком |
| `InvoiceStatus.PAID_WITHOUT_RECEIPT` | Оплачен без чека |
| `InvoiceStatus.CANCELLED` | Аннулирован |
| `InvoiceStatus.ERROR` | Ошибка |
| `InvoiceStatus.ALL` | Все статусы *(по умолчанию)* |

### Поиск счёта

```python
async def search_invoices():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Поиск по ИНН или имени клиента
        response = await client.get_bills(
            search="7743013902"  # ИНН или имя клиента
        )
        
        print(f"Найдено счетов: {len(response.items)}")
```

### Фильтрация по дате

```python
from datetime import datetime, timedelta

async def get_invoices_by_date():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Счета за последнюю неделю
        week_ago = datetime.now() - timedelta(days=7)
        
        response = await client.get_bills(
            date_from=week_ago,
            date_to=datetime.now()
        )
        
        print(f"Счетов за неделю: {len(response.items)}")
```

### Пагинация

```python
async def get_all_invoices_paginated():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        offset = 0
        limit = 20
        all_invoices = []
        
        while True:
            response = await client.get_bills(
                offset=offset,
                limit=limit
            )
            
            all_invoices.extend(response.items)
            
            if not response.has_more:
                break
            
            offset += limit
        
        print(f"Всего загружено счетов: {len(all_invoices)}")
```

## Управление счётом

### Отметить как оплаченный

После того как клиент оплатил счёт, отметьте его как оплаченный:

```python
async def approve_invoice():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice_id = 12345  # ID счёта
        
        invoice = await client.approve_bill(invoice_id)
        
        print(f"✅ Счёт №{invoice_id} отмечен как оплаченный")
        print(f"Статус: {invoice.status}")
```

### Создать чек на основе оплаченного счёта

После оплаты счёта можно автоматически создать чек:

```python
from datetime import datetime

async def create_receipt_from_invoice():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice_id = 12345
        
        # Указываем дату получения средств (если не указать - текущее время)
        invoice = await client.create_check_from_bill(
            invoice_id=invoice_id,
            operation_time=datetime.now()
        )
        
        print(f"✅ Чек создан для счёта №{invoice_id}")
        print(f"UUID чека: {invoice.receipt_id}")
```


### Изменить способ оплаты

Если нужно изменить реквизиты для оплаты:

```python
async def update_payment_method():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice_id = 12345
        
        # Меняем на другой номер СБП
        invoice = await client.update_bill_payment_info(
            invoice_id=invoice_id,
            payment_type=InvoicePaymentType.PHONE,
            phone="+79991234567",
            bank_name="Альфа-Банк"
        )
        
        print(f"✅ Способ оплаты для счёта №{invoice_id} обновлён")
```

### Аннулировать счёт

Если счёт больше не нужен:

```python
async def cancel_invoice():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        invoice_id = 12345
        
        invoice = await client.cancel_bill(invoice_id)
        
        print(f"✅ Счёт №{invoice_id} аннулирован")
        print(f"Статус: {invoice.status}")
```

!!! warning "Важно"
    Аннулировать можно только счета в статусе "Создан" или "К оплате". Оплаченные счета аннулировать нельзя.

## Получение реквизитов

Получите сохранённые реквизиты для выставления счетов:

### Реквизиты СБП

```python
async def get_sbp_details():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        payment_types = await client.get_payment_types(
            payment_type=InvoicePaymentType.PHONE
        )
        
        print("Доступные номера для СБП:")
        for pt in payment_types:
            default = "⭐" if pt.is_default else ""
            print(f"  {pt.phone} ({pt.bank_name}) {default}")
```

### Банковские счета

```python
async def get_bank_accounts():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        payment_types = await client.get_payment_types(
            payment_type=InvoicePaymentType.ACCOUNT
        )
        
        print("Доступные банковские счета:")
        for pt in payment_types:
            print(f"\n{pt.bank_name}")
            print(f"  Расчётный счёт: {pt.current_account}")
            print(f"  БИК: {pt.bank_bik}")
            print(f"  Корр. счёт: {pt.corr_account}")
```