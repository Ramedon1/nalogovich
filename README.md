# Nalogovich
### Асинхронная Python библиотека (SDK) для API "Мой Налог" (ЛК НПД)

[![PyPI version](https://img.shields.io/pypi/v/nalogovich.svg)](https://pypi.org/project/nalogovich/)
[![Python versions](https://img.shields.io/pypi/pyversions/nalogovich.svg)](https://pypi.org/project/nalogovich/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nalogovich** - библиотека для интеграции с сервисом "Мой Налог". Идеально подходит для автоматизации отчетности самозанятых, создания платежных ботов в Telegram или CRM-систем.

[Документация](#) | [Сообщить об ошибке](https://github.com/Ramedon1/nalogovich/issues)

---
## 📦 Установка

```bash
pip install nalogovich
```
Или через современный менеджер пакетов [uv](https://github.com/astral-sh/uv):
```bash
uv add nalogovich
```

## 🚀 Быстрый старт

Создание чека за 1 минуту:

```python
import asyncio
from nalogovich.lknpd import NpdClient

async def main():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Создаем новый чек
        receipt = await client.create_ticket(
            name="Консультационные услуги",
            amount=1500,
            quantity=1
        )
        
        print(f"Чек создан! URL: {receipt.url}")
        
        # Получаем список последних операций
        checks = await client.get_checks(limit=5)
        print(f"Последние операции: {len(checks.content)}")

if __name__ == "__main__":
    asyncio.run(main())
```
