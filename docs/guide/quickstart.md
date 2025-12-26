# Быстрый старт

## Первый запрос

Давайте создадим простую программу, которая подключается к API и получает список чеков:

```python
import asyncio
from nalogovich.lknpd import NpdClient

async def main():
    # Создаём клиента с вашими учетными данными
    async with NpdClient(
        inn="123456789012",  # Ваш ИНН
        password="your_password"  # Ваш пароль от ЛК НПД
    ) as client:
        # Выполняем авторизацию
        await client.auth()
        
        # Получаем список чеков
        response = await client.get_checks()
        
        # Выводим информацию о чеках
        print(f"Найдено чеков: {len(response.content)}")
        print(f"Есть ещё чеки: {response.has_more}")
        
        for check in response.content:
            print(f"Чек: {check.approved_receipt_uuid}")
            print(f"Сумма: {check.total_amount} ₽")
            print(f"Дата: {check.operation_time}")
            print(f"Тип оплаты: {check.payment_type}")

if __name__ == "__main__":
    asyncio.run(main())
```

!!! tip "Использование контекстного менеджера"
    Обратите внимание на использование `async with` — это автоматически закрывает сессию после завершения работы.

## Создание чека

Теперь создадим чек (зарегистрируем доход):

```python
from nalogovich.lknpd import NpdClient
from nalogovich.enums import PaymentType

async def create_receipt():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Создаём чек
        income = await client.create_check(
            name="Консультация по Python",
            amount=5000.00,
            payment_type=PaymentType.CASH  # Наличные или карта
        )
        
        print(f"✅ Чек создан!")
        print(f"UUID: {income.approved_receipt_uuid}")
```

!!! success "Чек создан"
    После выполнения этого кода чек будет зарегистрирован в системе ФНС.

## Фильтрация чеков

Вы можете фильтровать чеки по различным параметрам:

```python
from datetime import datetime, timedelta
from nalogovich.enums import SortBy, ReceiptType

async def filter_checks():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Получаем чеки за последнюю неделю
        week_ago = datetime.now() - timedelta(days=7)
        
        response = await client.get_checks(
            from_date=week_ago,
            to_date=datetime.now(),
            sort_by=SortBy.total_amount_desc,  # Сортировка по сумме (по убыванию)
            receipt_type=ReceiptType.REGISTERED,  # Только действующие чеки
            limit=10  # Максимум 10 чеков
        )
        
        for check in response.content:
            print(f"{check.total_amount} ₽ — {check.name}")
```

## Обработка ошибок

Всегда оборачивайте вызовы API в блоки `try-except`:

```python
from nalogovich.lknpd import NpdClient
from nalogovich.exeptions import AuthenticationError, ApiError, ValidationError

async def safe_request():
    try:
        async with NpdClient(inn="123456789012", password="wrong_password") as client:
            await client.auth()
            
    except AuthenticationError as e:
        print(f"❌ Ошибка авторизации: {e}")
        print(f"Код ответа: {e.status_code}")
        
    except ApiError as e:
        print(f"❌ Ошибка API: {e}")
        print(f"Код: {e.status_code}")
        
    except ValidationError as e:
        print(f"❌ Ошибка валидации: {e}")
```

## Дальше - больше, знакомимся с методами библиотеки

- [Авторизация](authentication.md) — подробнее о процессе авторизации
- [Работа с чеками](checks.md) — все возможности работы с чеками
- [Работа со счетами](invoices.md) — выставление счетов клиентам
