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

## Existing REG.RU deployment

Если приложение уже размещено на REG.RU, создайте рядом с `server.py` файл
`.env` по образцу `.env.example`, затем перезапустите приложение.

Убедитесь, что после обновления установлены зависимости:

```bash
pip install -r requirements.txt
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
