# BLACKJACK · CENTURY 21 — AMO Dashboard

Аналитический дашборд для агентства недвижимости.

## Подключение к AmoCRM

Секреты задаются только в переменных окружения хостинга. Не добавляйте токены
в GitHub или frontend.

Для долгосрочного токена:

```text
AMO_SUBDOMAIN=c21pp
AMO_TOKEN=<долгосрочный токен AmoCRM>
DASHBOARD_USER=<логин для входа в дашборд>
DASHBOARD_PASSWORD=<сложный пароль для входа в дашборд>
```

Для OAuth вместо `AMO_TOKEN`:

```text
AMO_SUBDOMAIN=c21pp
AMO_ACCESS_TOKEN=<access token>
AMO_REFRESH_TOKEN=<refresh token>
AMO_CLIENT_ID=<integration id>
AMO_CLIENT_SECRET=<secret key>
```

## Deploy on Railway

1. Подключите этот GitHub-репозиторий к Railway.
2. Откройте сервис: **Variables**.
3. Добавьте `AMO_SUBDOMAIN`, `AMO_TOKEN`, `DASHBOARD_USER` и
   `DASHBOARD_PASSWORD`.
4. Дождитесь redeploy.
5. Проверьте `/api/health`: поля `amo_configured` и
   `dashboard_auth_configured` должны быть `true`.
