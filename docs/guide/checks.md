# Работа с чеками

Чеки — это основной способ регистрации дохода для самозанятых. В этом разделе описаны все операции с чеками.

## Создание чека

### Простой чек (одна позиция)

Самый простой способ создать чек для одной услуги или товара:

```python
from nalogovich.lknpd import NpdClient
from nalogovich.enums import PaymentType

async def create_simple_check():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        income = await client.create_check(
            name="Консультация по программированию",
            amount=5000.00,
            payment_type=PaymentType.CASH
        )
        
        print(f"✅ Чек создан: {income.approved_receipt_uuid}")
```

### Чек с несколькими позициями

Если нужно указать несколько услуг или товаров:

```python
from nalogovich.models.operations import ServiceCheck
from nalogovich.enums import PaymentType

async def create_multi_item_check():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Создаём список позиций
        services = [
            ServiceCheck(name="Разработка сайта", amount=30000.00, quantity=1),
            ServiceCheck(name="Настройка сервера", amount=10000.00, quantity=1),
            ServiceCheck(name="Техническая поддержка", amount=5000.00, quantity=2),
        ]
        
        income = await client.create_check(
            services=services,
            payment_type=PaymentType.CASH
        )
        
        print(f"✅ Чек на {sum(s.amount * s.quantity for s in services)} ₽ создан")
        print(f"UUID: {income.approved_receipt_uuid}")
```

!!! tip "Общая сумма"
    Nalogovich автоматически рассчитывает общую сумму чека на основе указанных позиций.

### Чек для юридического лица

Если услуга оказана организации:

```python
async def create_check_for_company():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        income = await client.create_check(
            name="Дизайн логотипа",
            amount=25000.00,
            payment_type=PaymentType.ACCOUNT,  # Безналичная оплата
            is_business=True,  # Услуга для бизнеса
            inn_of_organization="7743013902",  # ИНН организации
            name_of_organization="ООО Ромашка"  # Название организации
        )
        
        print(f"✅ Чек для юр. лица создан")
```

!!! warning "Обязательные поля для юр. лиц"
    При `is_business=True` обязательно указывайте `inn_of_organization` и `name_of_organization`.

### Чек для иностранной организации

```python
async def create_check_for_foreign():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        income = await client.create_check(
            name="Web development services",
            amount=100000.00,
            payment_type=PaymentType.ACCOUNT,
            is_foreign_organization=True,  # Иностранная организация
            name_of_organization="Foreign Company Ltd"
        )
        
        print(f"✅ Чек для иностранной организации создан")
```

### Указание даты продажи

По умолчанию используется текущая дата и время. Можно указать другую дату:

```python
from datetime import datetime, timedelta

async def create_check_with_date():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Дата продажи - вчера
        yesterday = datetime.now() - timedelta(days=1)
        
        income = await client.create_check(
            name="Консультация",
            amount=3000.00,
            payment_type=PaymentType.CASH,
            date_of_sale=yesterday
        )
        
        print(f"✅ Чек с датой {yesterday.date()} создан")
```

## Получение списка чеков

### Базовый запрос

По умолчанию возвращаются чеки за последний месяц:

```python
async def get_all_checks():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        response = await client.get_checks()
        
        print(f"Найдено чеков: {len(response.content)}")
        
        for check in response.content:
            print(f"\n{check.name}")
            print(f"  Сумма: {check.total_amount} ₽")
            print(f"  Дата: {check.operation_time}")
            print(f"  UUID: {check.approved_receipt_uuid}")
```

### Фильтрация по дате

```python
from datetime import datetime, timedelta

async def get_checks_by_date():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Чеки за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        
        response = await client.get_checks(
            from_date=week_ago,
            to_date=datetime.now()
        )
        
        print(f"Чеков за неделю: {len(response.content)}")
```

### Сортировка

```python
from nalogovich.enums import SortBy

async def get_sorted_checks():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Сортировка по сумме (сначала самые дорогие)
        response = await client.get_checks(
            sort_by=SortBy.total_amount_desc
        )
        
        print("Топ-3 самых дорогих чека:")
        for check in response.content[:3]:
            print(f"{check.total_amount} ₽ — {check.name}")
```

Доступные варианты сортировки:

- `SortBy.operation_time_asc` — по дате (старые → новые)
- `SortBy.operation_time_desc` — по дате (новые → старые) ⭐ *по умолчанию*
- `SortBy.total_amount_asc` — по сумме (возрастание)
- `SortBy.total_amount_desc` — по сумме (убывание)

### Фильтрация по статусу

```python
from nalogovich.enums import ReceiptType

async def get_active_checks():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Только действующие чеки
        response = await client.get_checks(
            receipt_type=ReceiptType.REGISTERED
        )
        
        print(f"Действующих чеков: {len(response.content)}")
```

Варианты:

- `ReceiptType.REGISTERED` — только действующие чеки
- `ReceiptType.CANCELLED` — только аннулированные чеки
- `None` — все чеки *(по умолчанию)*

### Фильтрация по типу клиента

```python
from nalogovich.enums import BuyerType

async def get_checks_by_buyer():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Только чеки от юр. лиц
        response = await client.get_checks(
            buyer_type=BuyerType.COMPANY
        )
        
        print(f"Чеков от организаций: {len(response.content)}")
```

Варианты:

- `BuyerType.PERSON` — физические лица
- `BuyerType.COMPANY` — юридические лица
- `BuyerType.FOREIGN_AGENCY` — иностранные организации
- `None` — все типы *(по умолчанию)*

### Пагинация

Для работы с большим количеством чеков:

```python
async def get_checks_with_pagination():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        offset = 0
        limit = 50
        all_checks = []
        
        while True:
            response = await client.get_checks(
                offset=offset,
                limit=limit
            )
            
            all_checks.extend(response.content)
            
            if not response.has_more:
                break
            
            offset += limit
        
        print(f"Всего загружено чеков: {len(all_checks)}")
```

## Аннулирование чека

Если чек был создан ошибочно или клиент вернул товар:

```python
from nalogovich.enums import CommentReturn

async def cancel_check():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # UUID чека, который нужно аннулировать
        receipt_uuid = "200bzznrt0"
        
        result = await client.cancel_check(
            receipt_uuid=receipt_uuid,
            comment=CommentReturn.wrong_receipt  # Чек сформирован ошибочно
        )
        
        print(f"✅ Чек {receipt_uuid} аннулирован")
```

### Причины аннулирования

Вы можете указать стандартную причину из `CommentReturn`:

- `CommentReturn.wrong_receipt` — "Чек сформирован ошибочно"
- `CommentReturn.receipt_return` — "Чек возвращен"

Или указать свою причину:

```python
result = await client.cancel_check(
    receipt_uuid="200bzznrt0",
    comment="Возврат товара по желанию покупателя"
)
```

!!! warning "Важно"
    Аннулировать можно только действующие чеки. Уже аннулированный чек нельзя отменить повторно.

## Обработка ошибок

```python
from nalogovich.exeptions import ValidationError, ApiError

async def create_check_with_error_handling():
    try:
        async with NpdClient(inn="123456789012", password="your_password") as client:
            await client.auth()
            
            income = await client.create_check(
                name="Услуга",
                amount=5000.00,
                payment_type=PaymentType.CASH
            )
            
            print(f"✅ Чек создан: {income.approved_receipt_uuid}")
            
    except ValidationError as e:
        print(f"❌ Ошибка валидации: {e}")
        # Например, не указана сумма или название
        
    except ApiError as e:
        print(f"❌ Ошибка API: {e}")
        print(f"Код: {e.status_code}")
```

## Примеры использования

### Автоматическое создание чеков из CSV

```python
import csv
from nalogovich.enums import PaymentType

async def import_checks_from_csv():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        with open("incomes.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    income = await client.create_check(
                        name=row["service_name"],
                        amount=float(row["amount"]),
                        payment_type=PaymentType.CASH
                    )
                    print(f"✅ {row['service_name']}: {income.approved_receipt_uuid}")
                    
                except Exception as e:
                    print(f"❌ Ошибка при создании чека для {row['service_name']}: {e}")
```

### Статистика по чекам

```python
async def calculate_statistics():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        response = await client.get_checks()
        
        total_income = sum(check.total_amount for check in response.content)
        avg_check = total_income / len(response.content) if response.content else 0
        
        print(f"📊 Статистика за месяц:")
        print(f"  Всего чеков: {len(response.content)}")
        print(f"  Общий доход: {total_income:,.2f} ₽")
        print(f"  Средний чек: {avg_check:,.2f} ₽")
```
