# AdRobot

Web-приложение для управления рекламными кампаниями в трекере **Keitaro**.

Обёртка над Keitaro, которая убирает ручную настройку: создаёт кампанию с двумя
потоками маршрутизации (Google Redirect + Offer Flow) и позволяет редактировать
офферы и веса распределения в существующих кампаниях.

## Возможности

- **Создание кампании**: название, GEO (ISO-коды, мультивыбор), офферы, домен.
  Автоматически создаются два потока:
  - *Google Redirect* — ловит пользователей из выбранных GEO и редиректит на Google;
  - *Offer Flow* — отправляет остальной трафик на выбранные офферы с равномерным стартовым распределением.
- **Список кампаний**: поиск, фильтр по статусу, переход к деталям.
- **Редактор**: просмотр потоков, добавление/удаление офферов, изменение `share`,
  автоматический пересчёт процентов распределения, сохранение полным PUT без потери настроек,
  защита от конкурентного редактирования (optimistic concurrency).
- **Асинхронное создание** через RabbitMQ + transactional outbox (статус операции, идемпотентность).
- **Операции**: история, статус с авто-обновлением, повтор (retry) упавших операций, аудит-лог.
- **Дашборд**: счётчики кампаний и операций, последние кампании и операции.
- **Безопасность и надёжность**: опциональная аутентификация API, rate limiting, security-заголовки,
  correlation-id, `/healthz` и `/readyz`, fail-fast при отсутствии секретов.

## Архитектура

Модульный монолит: FastAPI (backend) + отдельный Worker + Nuxt 3 (frontend).
Подробнее: [docs/architecture.md](docs/architecture.md).
Интеграция с Keitaro: [docs/keitaro-integration.md](docs/keitaro-integration.md).

## Технологический стек

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (async), asyncpg, Alembic, Pydantic v2, httpx, aio-pika.
- **Worker**: aio-pika (RabbitMQ), transactional outbox.
- **DB**: PostgreSQL 16; **Broker**: RabbitMQ 3.13.
- **Frontend**: Nuxt 3, Vue 3, TypeScript, Pinia, Tailwind CSS.

## Структура проекта

```text
backend/
  app/
    domain/         # сущности, value objects, исключения, порты репозиториев
    application/    # use cases, DTO, порты, билдеры payload'ов
    infrastructure/ # БД, репозитории, KeitaroClient, RabbitMQ, outbox
    presentation/   # роутеры, схемы, зависимости, обработчики ошибок
    worker/         # обработчик campaign.create
    main.py
  migrations/       # Alembic
  tests/            # unit + integration
frontend/           # Nuxt 3
docs/
docker-compose.yml
```

## Требования к окружению

- Docker и Docker Compose (v2+). Для локальной разработки — Python 3.12+ и Node 20+.

## Установка и запуск (Docker Compose)

```bash
git clone <repository-url>
cd adrobot

# 1. Подготовка переменных окружения
cp .env.example .env
#   отредактируйте .env: укажите KEITARO_API_TOKEN (и при необходимости остальные значения)

# 2. Запуск всего стека
docker compose up -d --build

# 3. Логи
docker compose logs -f

# 4. Остановка
docker compose down
```

Сервисы:

| Сервис | URL |
|---|---|
| Frontend (Nuxt 3) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| RabbitMQ management | http://localhost:15672 |

Миграции выполняются автоматически сервисом `migrate` перед стартом backend/worker.

## Настройка `.env`

| Переменная | Назначение |
|---|---|
| `KEITARO_BASE_URL` | Базовый URL Keitaro admin API |
| `KEITARO_API_TOKEN` | API-токен Keitaro |
| `KEITARO_TIMEOUT` / `KEITARO_MAX_RETRIES` | Таймаут и число повторов HTTP-запросов |
| `KEITARO_TRAFFIC_SOURCE_ID` | ID источника трафика (по умолчанию `836` FORTESTS) |
| `KEITARO_GROUP_ID` | ID группы кампаний (по умолчанию `10332` FORTESTS) |
| `GOOGLE_REDIRECT_URL` | URL для Google Redirect (по умолчанию `https://google.com`) |
| `DEFAULT_OFFER_SHARE` | Начальный `share` оффера (по умолчанию `100`) |
| `POSTGRES_*` | Подключение к PostgreSQL |
| `RABBITMQ_*` | Подключение к RabbitMQ |
| `CORS_ORIGINS` | Разрешённые origin'ы фронта |
| `LOG_LEVEL` | Уровень логирования (по умолчанию `INFO`) |
| `ADROBOT_API_TOKEN` | Опциональный общий токен API (пусто = аутентификация отключена) |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_PER_MINUTE` | Rate limiting на один IP |
| `NUXT_PUBLIC_API_BASE` / `NUXT_PUBLIC_API_TOKEN` / `NUXT_PUBLIC_MOCK` | Настройки SPA-фронта (встраиваются при сборке) |

Секреты хранятся только в `.env` (не в коде и не в Docker-образах); токен никогда не
передаётся на фронтенд.

## Миграции

```bash
docker compose run --rm migrate alembic upgrade head      # применить
docker compose run --rm migrate alembic revision --autogenerate -m "..."  # создать
```

## Тесты и линтинг

```bash
docker compose run --rm --no-deps backend pytest          # unit + integration (mock HTTP/SQLite)
docker compose run --rm --no-deps backend ruff check app  # линтинг
cd frontend && npm run typecheck && npm test              # frontend
```

## Примеры API-запросов

```bash
# Создание кампании (async -> 202)
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H 'Content-Type: application/json' \
  -d '{"name":"My Campaign","geo":["AU","MX"],"offer_ids":[25327,24800],"domain_id":1813}'
# -> {"operation_id":"...","status":"pending","message":"Campaign creation started"}

# Статус операции
curl http://localhost:8000/api/v1/operations/<operation_id>

# Повтор упавшей операции
curl -X POST http://localhost:8000/api/v1/operations/<operation_id>/retry

# Дашборд / аудит
curl http://localhost:8000/api/v1/dashboard
curl 'http://localhost:8000/api/v1/audit-logs?page_size=50'

# Готовность сервиса (DB / RabbitMQ / Keitaro)
curl http://localhost:8000/readyz

# Список кампаний
curl 'http://localhost:8000/api/v1/campaigns?search=&page=1&page_size=20'

# Обновление офферов потока (share: integer 1..100; base_fingerprint — для optimistic concurrency)
curl -X PUT http://localhost:8000/api/v1/streams/<stream_id>/offers \
  -H 'Content-Type: application/json' \
  -d '{"offers":[{"offer_id":25327,"share":100},{"offer_id":24800,"share":50}]}'
```

Полный контракт API — [docs/api.md](docs/api.md).

## Известные ограничения

- `/offers` Keitaro не поддерживает серверный поиск/пагинацию — AdRobot загружает
  список офферов и фильтрует/пагинирует на своей стороне.
- Имя кампании в Keitaro уникально: повторное создание кампании с уже занятым именем
  завершится ошибкой операции.
- `share` оффера в Keitaro — целое число `1..100` (значения больше 100 и дробные отклоняются).
- Конкурентное редактирование одного потока защищено повторным чтением полной
  конфигурации непосредственно перед PUT (другие настройки потока не теряются).
