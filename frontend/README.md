# AdRobot — Frontend

Фронтенд веб-приложения AdRobot: создание и настройка рекламных кампаний Keitaro.
Оборачивает FastAPI-бэкенд AdRobot (контракт — `docs/api.md` в корне репозитория).

## Технологии

- Nuxt 3 (SPA, `ssr: false`) + Vue 3 + TypeScript (strict)
- Pinia (состояние редактирования и тостов)
- Tailwind CSS (через `@nuxtjs/tailwindcss`)
- Vitest (юнит-тесты бизнес-правил)

## Структура

```
frontend/
├── app.vue                  # корневой компонент
├── layouts/default.vue      # единый layout (шапка/навигация/футер)
├── pages/
│   ├── index.vue            # дашборд
│   ├── campaigns/index.vue  # список кампаний
│   ├── campaigns/create.vue # форма создания
│   ├── campaigns/[id].vue   # редактор кампании
│   └── operations/[id].vue  # статус операции
├── components/              # UI-компоненты (Tailwind, без Nuxt UI)
├── composables/useApi.ts    # единая точка доступа к API (real | mock)
├── stores/                  # Pinia-сторы
├── types/                   # DTO контракта API
├── utils/                   # чистые функции (распределение, форматирование, API-клиент)
├── mock/                    # изолированный mock-режим (NUXT_PUBLIC_MOCK=true)
├── tests/                   # юнит-тесты
├── nuxt.config.ts
├── tailwind.config.ts
├── Dockerfile
└── .dockerignore
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000/api/v1` | Базовый URL бэкенда |
| `NUXT_PUBLIC_MOCK` | `false` | `true` — включить встроенный mock |

Обе переменные читаются на этапе сборки/dev (в SPA публичная часть `runtimeConfig`
встраивается в бандл). Для dev-режима достаточно задать их перед запуском `npm run dev`.

## Запуск в dev

```bash
cd frontend
npm install

# реальный бэкенд (по умолчанию http://localhost:8000/api/v1)
npm run dev

# или с mock-режимом, без бэкенда
NUXT_PUBLIC_MOCK=true npm run dev
```

Приложение откроется на `http://localhost:3000`.

## Сборка и тесты

```bash
npm run build      # сборка SPA в .output
npm run preview    # предпросмотр собранного приложения
npm run typecheck  # проверка типов (nuxt typecheck)
npm run test       # юнит-тесты (Vitest)
```

## Docker

```bash
cd frontend
docker build -t adrobot-frontend .
docker run --rm -p 3000:3000 adrobot-frontend
```

Dockerfile — multi-stage (`node:20-alpine`): `npm ci` → `npm run build` →
запуск `node .output/server/index.mjs`. Порт `3000`.

## Mock-режим

Изолированная имитация бэкенда (`mock/mockApi.ts` + `mock/data.ts`), реализующая
тот же интерфейс `AdRobotApi`, что и реальный HTTP-клиент. Позволяет проверить
рендеринг, кнопки и пересчёт процентов без запуска FastAPI.

Включение:

```bash
NUXT_PUBLIC_MOCK=true npm run dev
```

Mock хранит состояние в памяти: создание кампании проходит стадии
`pending → processing → completed` (удобно для проверки автоопроса на странице
статуса операции), список кампаний пополняется, а `PUT /streams/{id}/offers`
обновляет поток.

## Бизнес-правила

Реализованы в чистых функциях `utils/distribution.ts` (покрыты тестами):

- Процент распределения: `share / sum(shares) * 100`, отображается ровно с 2 знаками.
  Округление влияет только на отображение, `share` никогда не изменяется.
- `share` должен быть целым числом в диапазоне `1..100` (иначе сохранение заблокировано;
  значения `>100` и дробные значения отвергаются — проверено на живом Keitaro).
- Пустой список офферов сохранить нельзя.
- Перед сохранением, если локальная конфигурация отличается от серверной,
  показывается подтверждение (сводка «добавлено / удалено / изменено»).

## Допущения и отклонения от контракта

- Выбор офферов всегда использует только **активные** офферы (`GET /offers` с
  `state=active`). Контракт не описывает способ получения неактивных офферов,
  а требование «только активные по умолчанию» выполняется; отдельного
  переключателя неактивных не добавлено, чтобы не придумывать параметры API.
- «Текущий этап» операции на странице статуса выводится из `status`/`type`
  (поле `stage` в контракте `GET /operations/{id}` отсутствует) — отдельное поле
  не изобреталось.
- Счётчики «успешных/неуспешных операций» на дашборде считаются по последним
  100 операциям (`GET /operations?page_size=100`), т.к. контракт не предоставляет
  отдельного endpoint со сводкой по статусам.
- `NUXT_PUBLIC_API_BASE` для SPA встраивается на этапе сборки; для изменения в
  контейнере задавайте переменную при сборке образа.
