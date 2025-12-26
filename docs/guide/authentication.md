# Авторизация

Для работы с API "Мой Налог" (lknpd.nalog.ru) необходимо пройти авторизацию с использованием ИНН и пароля от Личного Кабинета Налогоплательщика.

## Базовая авторизация

Самый простой способ авторизации:

```python
from nalogovich.lknpd import NpdClient

async def auth_example():
    client = NpdClient(
        inn="123456789012",  # Ваш ИНН (12 цифр)
        password="your_password"  # Пароль от ЛК НПД
    )
    
    # Выполняем авторизацию
    auth_response = await client.auth()
    
    print(f"✅ Авторизация успешна!")
    print(f"Токен: {client.token[:20]}...")  # Первые 20 символов токена
    
    # Не забудьте закрыть сессию
    await client.close()
```

## Использование контекстного менеджера

**Рекомендуемый способ** — использовать контекстный менеджер `async with`:

```python
async def auth_with_context():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Ваш код здесь
        # Сессия автоматически закроется при выходе из блока with
```

!!! tip "Автоматическое закрытие сессии"
    Контекстный менеджер автоматически вызывает `client.close()` при выходе из блока, даже если произошла ошибка.

## Автоматическое обновление токена

Nalogovich автоматически обновляет токен при его истечении:

```python
async def auto_refresh_example():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Первый запрос
        checks1 = await client.get_checks()
        
        # ... прошло много времени, токен истёк ...
        
        # Nalogovich автоматически обновит токен при следующем запросе
        checks2 = await client.get_checks()  # Сработает автоматически
```

!!! info "Refresh Token"
    При первой авторизации Nalogovich сохраняет refresh token и использует его для автоматического получения нового access token.

## Обработка ошибок авторизации

Различные типы ошибок при авторизации:

```python
from nalogovich.lknpd import NpdClient
from nalogovich.exeptions import AuthenticationError, ApiError

async def handle_auth_errors():
    try:
        async with NpdClient(inn="123456789012", password="wrong_password") as client:
            await client.auth()
            
    except AuthenticationError as e:
        if e.status_code == 422:
            print("❌ Неверный ИНН или пароль")
        elif e.status_code == 401:
            print("❌ Неавторизован. Проверьте учетные данные")
        elif e.status_code == 403:
            print("❌ Доступ запрещён. Возможно, аккаунт заблокирован")
        else:
            print(f"❌ Ошибка авторизации: {e}")
        
        # Дополнительная информация
        print(f"Код ответа: {e.status_code}")
        print(f"Данные ответа: {e.response_data}")
        
    except ApiError as e:
        print(f"❌ Ошибка API: {e}")
```

### Типичные ошибки

| Код | Описание | Решение |
|-----|----------|---------|
| 422 | Неверный ИНН или пароль | Проверьте правильность учетных данных |
| 401 | Неавторизован | Убедитесь, что пароль актуален |
| 403 | Доступ запрещён | Проверьте статус аккаунта в ЛК НПД |

## Повторная авторизация вручную

Если нужно принудительно обновить токен:

```python
async def manual_reauth():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        # Работаем с API...
        
        # Принудительно обновляем токен
        await client.re_auth()
        
        # Продолжаем работу с новым токеном
```

## Проверка статуса авторизации

```python
async def check_auth_status():
    client = NpdClient(inn="123456789012", password="your_password")
    
    # Проверяем наличие токена
    if client.token is None:
        print("⚠️ Не авторизован")
        await client.auth()
    else:
        print("✅ Уже авторизован")
    
    await client.close()
```

## Следующие шаги

- [Работа с чеками](checks.md) — создание и управление чеками
- [Работа со счетами](invoices.md) — выставление счетов клиентам
