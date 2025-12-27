<p align="left">
  <img src="docs/assets/icon.svg" alt="Nalogovich Logo" width="150">
</p>

# Nalogovich
### Асинхронная Python библиотека (SDK) для API "Мой Налог" (ЛК НПД)

[![PyPI version](https://img.shields.io/pypi/v/nalogovich.svg)](https://pypi.org/project/nalogovich/)
[![Python versions](https://img.shields.io/pypi/pyversions/nalogovich.svg)](https://pypi.org/project/nalogovich/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CodeFactor](https://www.codefactor.io/repository/github/ramedon1/nalogovich/badge)](https://www.codefactor.io/repository/github/ramedon1/nalogovich)

**Nalogovich** - библиотека для интеграции с сервисом "Мой Налог". Идеально подходит для автоматизации отчетности самозанятых, создания платежных ботов в Telegram или CRM-систем.

[Документация](https://nalogovich.readthedocs.io/ru/latest/) | [Сообщить об ошибке](https://github.com/Ramedon1/nalogovich/issues)

---
## Установка

```bash
pip install nalogovich
```
Или через менеджер пакетов [uv](https://github.com/astral-sh/uv):
```bash
uv add nalogovich
```

## Быстрый старт

Создание чека:

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
        
        checks = await client.get_checks(limit=5)
        print(f"Последние операции: {len(checks.content)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### С остальными примерами и методами можно ознакомиться в [документации](https://nalogovich.readthedocs.io/ru/latest/)

## Как получить пароль для использования Nalogovich

Если вы не знаете свой пароль или он у вас не установлен, то его можно установить вручную (даже не зная его):

1.  Перейдите в [Личный кабинет налогоплательщика ФЛ](https://lkfl2.nalog.ru/).
2.  Авторизуйтесь через **Госуслуги (ЕСИА)** или любым удобным способом, который вам подходит.
3.  Зайдите в **Настройки профиля** → **Безопасность** → **Изменить пароль**.
4.  Установите новый пароль.

> Установленный пароль станет единым для входа в кабинет Физлица и в сервис «Мой налог». Используйте его вместе с вашим ИНН для авторизации в библиотеке.