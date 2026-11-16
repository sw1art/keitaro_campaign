# AdRobot

> Веб-приложение для управления рекламными кампаниями в трекере **Keitaro**: от создания кампании до аналитики эффективности офферов.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Nuxt 3](https://img.shields.io/badge/Frontend-Nuxt%203-00DC82?logo=nuxt.js&logoColor=white)](https://nuxt.com)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![RabbitMQ](https://img.shields.io/badge/Queue-RabbitMQ-FF6600?logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com)
[![Grafana](https://img.shields.io/badge/Logs-Grafana%2FLoki-F46800?logo=grafana&logoColor=white)](https://grafana.com)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

---

## Оглавление

- [AdRobot](#adrobot)
  - [Оглавление](#оглавление)
  - [Что это](#что-это)
  - [🚀 Быстрый старт](#-быстрый-старт)
    - [Требования](#требования)
    - [Запуск](#запуск)
    - [Что запустилось](#что-запустилось)
  - [Возможности](#возможности)
  - [Как это работает](#как-это-работает)
  - [Технологический стек](#технологический-стек)
  - [Настройка `.env`](#настройка-env)
  - [Миграции, тесты, линтинг](#миграции-тесты-линтинг)
  - [Примеры API](#примеры-api)
  - [Логирование и наблюдаемость](#логирование-и-наблюдаемость)
  - [Что сделано сверх ТЗ](#что-сделано-сверх-тз)
  - [Паттерны и приёмы](#паттерны-и-приёмы)
  - [Известные ограничения](#известные-ограничения)

---

## Что это

**AdRobot** — обёртка над рекламным трекером [Keitaro](https://keitaro.io), которая избавляет от ручной настройки кампаний. Вместо кликов по админке трекера вы управляете всем через удобный веб-интерфейс.

Две главные задачи:

| | Задача | Что делает |
|---|---|---|
| 🛠 | **Создание кампаний** | По названию, GEO, офферам и домену автоматически создаёт кампанию с двумя потоками трафика |
| 📊 | **Аналитика и редактор** | Показывает эффективность и позволяет править распределение трафика между офферами |

Схема одной кампании:

```text
                    ВХОДЯЩИЙ ТРАФИК
                          │
                          ▼
                 ┌────────────────┐
                 │ Google Redirect │   ← GEO-фильтр (country = accept)
                 └────────────────┘
                    │          │
             GEO совпал     GEO не совпал
                    │          │
                    ▼          ▼
              google.com   ┌─────────────┐
                           │  Offer Flow  │  ← без фильтров (fallback)
                           └─────────────┘
                           распределение по share
                    ┌──────────┬──────────┐
                    ▼          ▼          ▼
                 Offer A    Offer B    Offer C
```

Ключевая идея — замкнутый цикл управления рекламой:

```text
Создание кампании → Анализ эффективности офферов → Корректировка share → Повторный анализ
```

---

## 🚀 Быстрый старт

### Требования

- **Docker** и **Docker Compose** (v2+).

### Запуск

```bash
# 1. Клонируйте репозиторий
git clone [<repository-url>](https://github.com/sw1art/keitaro_campaign.git)
cd keitaro_campaign

# 2. Создайте .env из примера и укажите токен Keitaro
cp .env.example .env
#    отредактируйте KEITARO_API_TOKEN в .env

# 3. Поднимите весь стек (первая сборка займёт пару минут)
docker compose up -d --build

# 4. Логи
docker compose logs -f

# 5. Остановка
docker compose down
```

### Что запустилось

| Сервис | URL | Назначение |
|---|---|---|
| 🖥 **Frontend** | http://localhost:3000 | Веб-интерфейс (Nuxt 3) |
| 🔌 **Backend API** | http://localhost:8000 | REST API (FastAPI) |
| 📖 **Swagger** | http://localhost:8000/docs | Интерактивная документация API |
| 🐇 **RabbitMQ** | http://localhost:15672 | Очереди сообщений (management) |
| 📈 **Grafana** | http://localhost:3001 | Дашборд логов (`admin`/`admin`) |
| 🪵 **Loki** | http://localhost:3100 | Хранилище логов |

Миграции базы данных выполняются автоматически сервисом `migrate` перед стартом backend/worker.

---

## Возможности

**Создание кампании**
- Название, GEO (ISO-коды, мультивыбор), офферы, домен.
- Автоматически два потока: *Google Redirect* (GEO-фильтр) и *Offer Flow* (fallback с равномерным `share=100`).

**Редактирование**
- Просмотр потоков, добавление/удаление офферов, изменение `share`.
- Автопересчёт процентов распределения, сохранение полным `PUT` без потери настроек.
- Защита от конкурентного редактирования (optimistic concurrency).

**Аналитика** (Keitaro Custom Reports)
- Дашборд с 13 метриками и дельтами к прошлому периоду.
- Графики динамики (Clicks/Conversions, Revenue/Cost/Profit, ROI, CR).
- Аналитика кампании (потоки / офферы / GEO).
- **Offer Performance**: сравнение планового и фактического `share`.
- GEO-аналитика, экспорт CSV.

**Надёжность и эксплуатация**
- Асинхронное создание через RabbitMQ + transactional outbox, saga-этапы, идемпотентность.
- Повтор упавших операций, аудит-лог, история операций.
- Health-проверки, структурированные логи (structlog + Grafana/Loki).

**Безопасность**
- Опциональная API-аутентификация, rate limiting, security-заголовки, correlation-id.

---

## Как это работает

Модульный монолит: **FastAPI** (backend) + отдельный **Worker** + **Nuxt 3** (frontend).

```text
             Frontend (Nuxt 3, SPA)
                     │
                     ▼
              FastAPI  (/api/v1)
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
   Кампании      Аналитика       Офферы
        └────────────┼─────────────┘
                     ▼
             Application layer
                     ▼
               Domain layer
                     ▼
              Infrastructure
              /            \
             ▼              ▼
       PostgreSQL        Keitaro API
             ▲
             │
         RabbitMQ ◄── Worker
```

- **Keitaro — источник истины**: списки и детали читаются напрямую из Keitaro, Postgres хранит только операции/историю/связи.
- **Создание кампании** идёт асинхронно через RabbitMQ: `pending → creating_campaign → creating_google_stream → creating_offer_stream → verifying → completed`.

Подробнее: [docs/architecture.md](docs/architecture.md) · [docs/keitaro-integration.md](docs/keitaro-integration.md) · [docs/api.md](docs/api.md).

---

## Технологический стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), asyncpg, Alembic, Pydantic v2, httpx, structlog |
| Worker | aio-pika (RabbitMQ), transactional outbox |
| База данных | PostgreSQL 16 |
| Брокер | RabbitMQ 3.13 |
| Frontend | Nuxt 3, Vue 3, TypeScript, Pinia, Tailwind CSS, Chart.js |
| Наблюдаемость | structlog, Promtail, Loki, Grafana |
| Деплой | Docker, Docker Compose |

---

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
| `LOG_LEVEL` / `LOG_FORMAT` | Уровень логирования и формат (`json`/`console`) |
| `ADROBOT_API_TOKEN` | Опциональный общий токен API (пусто = аутентификация отключена) |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_PER_MINUTE` | Rate limiting на один IP |
| `NUXT_PUBLIC_*` | Настройки SPA-фронта (встраиваются при сборке) |
| `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | Доступ к Grafana |

> 🔐 Секреты хранятся только в `.env` (не в коде и не в Docker-образах); токен никогда не передаётся на фронтенд.

---

## Миграции, тесты, линтинг

```bash
# Миграции
docker compose run --rm migrate alembic upgrade head                    # применить
docker compose run --rm migrate alembic revision --autogenerate -m "..." # создать

# Тесты
docker compose run --rm --no-deps backend pytest          # unit + integration
docker compose run --rm --no-deps backend ruff check app  # линтинг
cd frontend && npm run typecheck && npm test              # frontend
```

---

## Примеры API

```bash
# Создание кампании (асинхронно → 202 + operation_id)
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H 'Content-Type: application/json' \
  -d '{"name":"My Campaign","geo":["AU","MX"],"offer_ids":[25327,24800],"domain_id":1813}'

# Статус операции
curl http://localhost:8000/api/v1/operations/<operation_id>

# Обновление офферов потока (share: integer 1..100)
curl -X PUT http://localhost:8000/api/v1/streams/<stream_id>/offers \
  -H 'Content-Type: application/json' \
  -d '{"offers":[{"offer_id":25327,"share":100},{"offer_id":24800,"share":50}]}'

# Аналитика
curl 'http://localhost:8000/api/v1/analytics/overview?range=last_7_days'
curl 'http://localhost:8000/api/v1/analytics/offers?campaign_id=211913'
```

Полный контракт — [docs/api.md](docs/api.md).

---

## Логирование и наблюдаемость

Backend и Worker пишут **структурированные JSON-логи через structlog** (с `correlation_id`, маскированием секретов и этапами saga). Логи собираются в **Loki** через **Promtail** и визуализируются в **Grafana** (готовый дашборд «AdRobot Logs»).

```text
app (structlog JSON) ──▶ stdout ──▶ Promtail ──▶ Loki ──▶ Grafana
```

Откройте http://localhost:3001 → дашборд **AdRobot Logs**.

---

## Что сделано сверх ТЗ

Исходное ТЗ: FastAPI + SQLAlchemy, создание кампании с двумя потоками, редактор офферов, RabbitMQ + Worker + outbox, миграции, Docker, тесты, README. Сверх этого:

- **Аналитика v1.1** (Custom Reports): дашборд с 13 метриками и дельтами, графики, аналитика кампании, Offer Performance (план vs факт), GEO, CSV-экспорт.
- **Saga создания кампании**: этапы, `partially_failed` / `needs_attention`, прогресс, реконсилиация при таймауте.
- **Безопасность**: API-аутентификация, rate limiting, security-заголовки, correlation-id, fail-fast.
- **Наблюдаемость**: structlog + Grafana/Loki/Promtail, health-эндпоинты.
- **Конкурентное редактирование** (optimistic concurrency), **кэш справочников**, **retry/аудит/дашборд**.
- **Расширенные фильтры/сортировка/пагинация** кампаний.
- **Тесты отказоустойчивости** и **документирование реальных контрактов Keitaro**.

---

## Паттерны и приёмы

| Приём | Зачем |
|---|---|
| **Clean Architecture** (domain/application/infrastructure/presentation) | Домен не зависит от фреймворков — бизнес-правила тестируются изолированно, внешние системы заменяемы. |
| **Adapter Pattern** (`KeitaroClient` + `campaign_builder`) | Вся работа с Keitaro и преобразование его моделей — в одном месте. |
| **Repository Pattern** | Сервисы не знают про ORM; в тестах подставляются SQLite/fake-репозитории. |
| **Dependency Injection** | Явные зависимости, нет глобального состояния. |
| **Transactional Outbox** | Событие и операция пишутся в одной транзакции; публикация в RabbitMQ — отдельно. |
| **Saga + идемпотентность** | Каждый этап сохраняет созданный ID — повторная доставка не создаёт дублей. |
| **Optimistic Concurrency** | Fingerprint состояния → `409` при конфликте, без блокировок. |
| **Retry / DLQ** | Временные ошибки переживаются, упавшие задачи изолируются. |
| **Кэш с обходом на сохранении** | Меньше запросов на чтение, но при сохранении — перепроверка live-состояния. |
| **Correlation ID + structlog** | Сквозная трассировка запроса и ошибок. |
| **Keitaro как источник истины** | Нет рассинхронизации, доступны и кампании, созданные вне AdRobot. |
| **Event-driven + Async I/O** | HTTP не блокируется длительными операциями; worker масштабируется отдельно. |
| **«Сначала проверь контракты»** | До кода проверены реальные payload/ответы Keitaro; расхождения задокументированы. |

---

## Известные ограничения

- `/offers` Keitaro не поддерживает серверный поиск/пагинацию — AdRobot фильтрует/пагинирует на своей стороне (кэш 5 минут, сброс `POST /api/v1/dictionaries/refresh`).
- Имя кампании в Keitaro уникально: повторное создание с тем же именем вернёт ошибку операции.
- `share` оффера — целое число `1..100` (больше 100 и дробные отклоняются).
- Реальная маршрутизация (клик по URL кампании) с «неизвестным GEO» и «нет офферов» требует ручного клик-теста с известными IP — см. [docs/keitaro-integration.md](docs/keitaro-integration.md).
