# Авторизация

Для работы с API "Мой Налог" (lknpd.nalog.ru) необходимо пройти авторизацию. Доступны три способа:

| Способ | Что нужно | Метод |
|---|---|---|
| ЛК ФЛ | ИНН + пароль от кабинета налогоплательщика | `auth()` |
| Госуслуги (ЕСИА) | Логин, пароль и одноразовый код | `auth_esia()` / `NpdClient.from_esia()` |
| Сохранённая сессия | Ранее полученные токены | `NpdClient.from_token()` |

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
from nalogovich.exceptions import AuthenticationError, ApiError

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

## Вход через Госуслуги (ЕСИА)

Если пароля от ЛК ФЛ нет, можно войти через Госуслуги — тем же путём, что и веб-кабинет:
библиотека запрашивает у ЛК НПД ссылку авторизации, проходит вход на `esia.gosuslugi.ru`
и обменивает полученный код на токены ЛК НПД.

Для этого нужна дополнительная зависимость:

```bash
pip install nalogovich[esia]
```

```python
from nalogovich.lknpd import NpdClient

async def esia_example():
    client = await NpdClient.from_esia(
        login="79001234567",              # телефон, email или СНИЛС
        password="пароль_от_госуслуг",
        totp_secret="JBSWY3DPEHPK3PXP", # секрет из приложения-аутентификатора
    )

    print(client.profile["displayName"], client.profile["inn"])
    await client.close()
```

Тот же вход на уже созданном клиенте:

```python
async with NpdClient() as client:
    await client.auth_esia(
        login="79001234567",
        password="пароль_от_госуслуг",
        totp_secret="JBSWY3DPEHPK3PXP",
    )
```

### Одноразовый код

`totp_secret` принимает как чистый base32-секрет, так и целиком строку из QR-кода:

```python
totp_secret = "otpauth://totp/gosuslugi?secret=JBSWY3DPEHPK3PXP&issuer=gosuslugi"
```

Секрет показывается один раз — при подключении входа по одноразовому коду в настройках
безопасности Госуслуг. Если секрета нет, можно передать уже сгенерированный код (живёт 30 секунд):

```python
await client.auth_esia(login=..., password=..., totp_code="123456")
```

!!! danger "Храните секреты вне кода"
    Пароль Госуслуг и TOTP-секрет дают полный доступ к учётной записи. Держите их в
    переменных окружения или менеджере секретов, не в исходниках и не в репозитории.

!!! warning "Ошибки входа"
    Проблемы на стороне Госуслуг приходят как `EsiaAuthError` (наследник
    `AuthenticationError`) — в `response_data` лежит исходный ответ ЕСИА.
    Если на аккаунте включён другой способ подтверждения (СМС, push), вход не пройдёт:
    поддерживается только код из приложения-аутентификатора.

## Сохранение и восстановление сессии

ЛК НПД не использует сессионные куки — только пару `token` / `refreshToken`. Их можно сохранить
и в следующий раз войти без пароля и одноразового кода:

```python
# После любой авторизации
saved = client.export_session()
# {"token": "...", "refresh_token": "...", "source_device_id": "..."}

# Позже, в другом процессе
client = NpdClient.from_token(**saved)
checks = await client.get_checks(limit=5)
```

!!! info "Срок жизни"
    `token` действует около часа, `refreshToken` — дольше. При истечении токена библиотека
    сама обновит его через `re_auth()`, если передан `refresh_token`. Когда протухнет и он,
    понадобится полноценный вход заново.

## Следующие шаги

- [Работа с чеками](checks.md) — создание и управление чеками
- [Работа со счетами](invoices.md) — выставление счетов клиентам

