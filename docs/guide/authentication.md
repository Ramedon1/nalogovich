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

```

!!! tip "Автоматическое закрытие сессии"
    Контекстный менеджер автоматически вызывает `client.close()` при выходе из блока, даже если произошла ошибка.

## Автоматическое обновление токена

Nalogovich автоматически обновляет токен при его истечении:

```python
async def auto_refresh_example():
    async with NpdClient(inn="123456789012", password="your_password") as client:
        await client.auth()
        
        checks1 = await client.get_checks()
        
        # ... прошло много времени, токен истёк ...
        
        # Nalogovich автоматически обновит токен при следующем запросе
        checks2 = await client.get_checks()  # Сработает автоматически
```

!!! info "Refresh Token"
    При первой авторизации Nalogovich сохраняет refresh token и использует его для автоматического получения нового access token.

## Обработка ошибок авторизации

`auth()` и запросы к ЛК НПД внутри `auth_esia()` выбрасывают `AuthenticationError`
при HTTP 401, 403 и 422. Другие ошибки ответа и сетевые ошибки запросов к ЛК НПД
выбрасываются как `ApiError`. Текст ответа сервера доступен в `response_data`.

Ошибки входа на самом портале Госуслуг приходят как `EsiaAuthError`. Этот класс
наследуется от `AuthenticationError`, поэтому его нужно перехватывать первым.
Если для входа не передан обязательный одноразовый код, возникает `ValidationError`.

```python
from nalogovich.lknpd import NpdClient
from nalogovich.exceptions import (
    ApiError,
    AuthenticationError,
    EsiaAuthError,
    ValidationError,
)

async def login_with_esia():
    try:
        async with NpdClient() as client:
            await client.auth_esia(
                login="79001234567",
                password="your_password",
                totp_code="123456",
            )
            return client.profile

    except EsiaAuthError as e:
        print(f"Ошибка входа на Госуслугах: {e}")
    except AuthenticationError as e:
        print(f"ЛК НПД отклонил авторизацию (HTTP {e.status_code}): {e}")
    except ValidationError as e:
        print(f"Некорректные параметры входа: {e}")
    except ApiError as e:
        print(f"Ошибка запроса к ЛК НПД (HTTP {e.status_code}): {e}")
```

При входе по ИНН через `auth()` обработка такая же, кроме `EsiaAuthError` и
`ValidationError`: их этот способ входа не использует. Смотрите сообщение
исключения и `response_data`; один код HTTP 422 не всегда означает неверный пароль.

Сетевые ошибки запросов непосредственно к ЕСИА пока не преобразуются библиотекой
и могут приходить как исключения `curl_cffi`.

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


## Вход через Госуслуги (ЕСИА)

Если пароля от ЛК ФЛ нет, можно войти через Госуслуги — тем же путём, что и веб-кабинет:
библиотека запрашивает у ЛК НПД ссылку авторизации, проходит вход на `esia.gosuslugi.ru`
и обменивает полученный код на токены ЛК НПД. Для этого типа авторизации обязательно нужно подкючить двухфакторную аутентификацию через приложение-аутентификатор (TOTP).


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

