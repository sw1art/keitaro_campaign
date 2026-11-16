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
- **Асинхронное создание** через RabbitMQ + transactional outbox: saga-этапы
  (`создание кампании → Google Redirect → Offer Flow → проверка`), идемпотентность,
  частичное сохранение при сбоях (`partially_failed` / `needs_attention`), повтор упавших операций.
- **Операции**: история, статус с авто-обновлением и прогрессом по этапам, повтор (retry), аудит-лог.
- **Дашборд**: счётчики кампаний и операций, последние кампании и операции.
- **Безопасность и надёжность**: опциональная аутентификация API, rate limiting, security-заголовки,
  correlation-id, `/healthz` + `/health/live` + `/health/ready` + `/health/keitaro`, fail-fast при отсутствии секретов,
  кэш справочников с ручным сбросом, защита от конкурентного редактирования.

## Архитектура

Модульный монолит: FastAPI (backend) + отдельный Worker + Nuxt 3 (frontend).
Подробнее: [docs/architecture.md](docs/architecture.md).
Интеграция с Keitaro: [docs/keitaro-integration.md](docs/keitaro-integration.md).

## Что сделано сверх ТЗ

Исходное ТЗ требовало: FastAPI + SQLAlchemy (async), создание кампании с двумя
потоками, редактор офферов с пересчётом долей, RabbitMQ + Worker + outbox, миграции,
Docker Compose, тесты и README. Сверх этого реализовано:

- **Аналитика (версия 1.1)** на базе Keitaro Custom Reports API (`POST /report/build`):
  - дашборд с 13 метриками (clicks, unique clicks, conversions, leads, sales, rejected,
    CR, cost, revenue, profit, ROI, EPC, CPA) и дельтами к прошлому периоду;
  - графики динамики (Clicks/Conversions, Revenue/Cost/Profit, ROI, CR) по дням;
  - аналитика отдельной кампании (потоки / офферы / GEO);
  - **Offer Performance** — сравнение планового (`share`) и фактического распределения трафика;
  - GEO-аналитика по странам;
  - экспорт CSV.
- **Saga для создания кампании** — этапы (`creating_campaign → creating_google_stream →
  creating_offer_stream → verifying → completed`), статусы `partially_failed` / `needs_attention`,
  прогресс по этапам, реконсилиация при таймауте (сначала проверяем, не создался ли объект).
- **Безопасность**: опциональная API-аутентификация (`ADROBOT_API_TOKEN`), rate limiting,
  security-заголовки, correlation-id, fail-fast при отсутствии секретов.
- **Наблюдаемость**: `/healthz`, `/readyz` + `/health/live`, `/health/ready`, `/health/keitaro`,
  логирование запросов с correlation-id, ошибки с correlation-id в теле ответа.
- **Конкурентное редактирование**: optimistic concurrency (fingerprint офферов → `409`).
- **Кэш справочников** (TTL 5 минут, ручной сброс `POST /dictionaries/refresh`, обход кэша при сохранении).
- **Операции**: повтор упавшей (`POST /operations/{id}/retry`), аудит-лог, дашборд-эндпоинт.
- **Расширенные фильтры/сортировка/пагинация** кампаний (домен, источник, группа; сортировка по всем колонкам).
- **Тесты отказоустойчивости**: частичный сбой, повторная доставка, недоступность брокера, конфликт редактирования.
- **Проверка и документирование реальных контрактов Keitaro** (в т.ч. Custom Reports) —
  [docs/keitaro-integration.md](docs/keitaro-integration.md).

## Паттерны и приёмы (и почему)

| Приём | Зачем применён |
|---|---|
| **Clean Architecture** (domain / application / infrastructure / presentation) | Домен не зависит от FastAPI/SQLAlchemy/Keitaro — бизнес-правила тестируются изолированно, внешние системы заменяемы в тестах. |
| **Adapter Pattern** (`KeitaroClient` + `campaign_builder`) | Вся работа с Keitaro и преобразование его моделей — в одном месте. Смена версии/полей API Keitaro — точечные правки в адаптере, а не по всему коду. |
| **Repository Pattern** (порты в domain, реализации в infrastructure) | Сервисы не знают про ORM; в тестах подставляются SQLite/fake-репозитории. |
| **Dependency Injection** (FastAPI `Depends` + явные зависимости сервисов) | Явные зависимости, нет глобального состояния, лёгкая тестируемость. |
| **Transactional Outbox** | Операция и событие пишутся в одной транзакции БД, публикация в RabbitMQ — отдельно (best-effort + poller). Не теряем события при недоступности брокера. |
| **Saga + идемпотентность + частичный результат** | Каждый этап сохраняет созданный ID. Повторная доставка/retry не создаёт дублей, частично выполненные операции сохраняются и дозавершаются. |
| **Optimistic Concurrency** (fingerprint → `409`) | Предотвращает перезапись чужих правок без блокировок и без потери настроек потока. |
| **Retry / DLQ** (`campaign.create` → `.retry` → `.dlq`) | Временные ошибки переживаются с повторными попытками; окончательно упавшие задачи изолируются и не блокируют очередь. |
| **Кэширование с обходом на сохранении** (TTL + сброс + `fresh=True`) | Меньше запросов к Keitaro на чтение, но при сохранении всегда перепроверяем актуальное состояние. |
| **Correlation ID + логирование запросов** | Сквозная трассировка запроса, диагностика ошибок по `X-Request-ID`. |
| **Defense in depth** (валидация и на backend, и на frontend) | Frontend не доверяем — все бизнес-правила проверяются на сервере. |
| **Keitaro как источник истины** | Списки/детали читаются напрямую из Keitaro; Postgres хранит только операции/историю/связи. Нет рассинхронизации, доступны и кампании, созданные вне AdRobot. |
| **Event-driven для длительных операций** (RabbitMQ + Worker) | HTTP-запрос не блокируется длительным созданием; worker можно масштабировать отдельно. |
| **Async I/O везде** (httpx, aio-pika, asyncpg, async SQLAlchemy) | Высокая пропускная способность при множестве внешних вызовов без блокировки event loop. |
| **Pydantic v2 + единая форма ошибок** (`{error:{code,message,correlation_id}}`) | Строгий и предсказуемый контракт API. |
| **Модульный монолит (не микросервисы)** | Один репозиторий/код с отдельным процессом Worker: простота деплоя без сетевых накладок микросервисов, при этом асинхронность сохранена. |
| **«Сначала проверь контракты»** (задание §21) | До написания кода проверены реальные payload/ответы Keitaro и Custom Reports API; расхождения зафиксированы в документации. |

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
cd keitaro_campaign

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
- Реальная маршрутизация (клик по URL кампании) с «неизвестным GEO» и «нет доступных
  офферов» требует ручного клик-теста с известными IP — см. [docs/keitaro-integration.md](docs/keitaro-integration.md).
- Кэш справочников — in-memory с TTL 5 минут (не распределённый); сброс — `POST /api/v1/dictionaries/refresh`.
