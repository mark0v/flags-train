# Flags Train

Telegram-бот для изучения флагов, столиц, языков, населения и валют стран ООН в формате Anki-подобного квиза.

## Что уже есть

- `aiogram 3` и inline-first UX
- `PostgreSQL + SQLAlchemy + Alembic`
- локализация `ru / en / de`
- локальный офлайн dataset: `data/normalized/countries.json`
- локальные SVG-флаги в `data/flags/`
- quiz modes: `mixed / review / new`
- межсессионный learning progress
- базовая статистика пользователя
- SRS-приоритизация на базе `proficiency_score`, `current_streak`, `next_review_at`
- встроенный `/admin` с безопасными catalog actions
- runtime preflight перед запуском
- startup logging и явный preflight report
- Dockerfile, `docker-compose.yml`, `.env.example`
- тесты и `ruff`

## Структура проекта

- `app/` - бот, сервисы, БД, локализация, доменная логика
- `alembic/` - миграции БД
- `data/normalized/` - локальный dataset стран
- `data/flags/` - локальные флаги
- `scripts/` - data pipeline, sync, preflight и dev/admin CLI
- `tests/` - unit и integration tests

## Быстрый старт

1. Создайте `.env` из `.env.example` и заполните `BOT_TOKEN`.

2. Установите зависимости:

```bash
pip install -e .[dev]
```

3. Проверьте локальный dataset:

```bash
python scripts/validate_countries_data.py
```

4. Примените миграции:

```bash
alembic upgrade head
```

5. Синхронизируйте каталог стран в БД:

```bash
python scripts/sync_countries_to_db.py
```

6. Выполните preflight:

```bash
python scripts/runtime_preflight.py
```

Пример ожидаемого вывода:

```text
Overall: READY
Dataset: OK (countries=193, range=AFG-ZWE)
Database: OK (revision=...)
Migrations: OK (current=..., expected=...)
```

7. Запустите бота:

```bash
python scripts/run_bot.py
```

## Docker Compose

Основной runtime:

```bash
docker compose up --build db bot
```

Подготовка локальных данных внутри Docker:

```bash
docker compose --profile setup run --rm data
```

Operational one-shot services:

```bash
docker compose --profile ops run --rm migrate
docker compose --profile ops run --rm sync
docker compose --profile ops run --rm preflight
```

Рекомендуемый порядок для первого запуска через Docker:

```bash
docker compose up -d db
docker compose --profile ops run --rm migrate
docker compose --profile ops run --rm sync
docker compose --profile ops run --rm preflight
docker compose up --build bot
```

`bot` больше не делает миграции автоматически при старте. Это сделано специально, чтобы запуск runtime был предсказуемым и безопаснее для production-like окружения.

`run_bot.py` теперь логирует:

- `APP_ENV`
- путь к локальному dataset
- путь к каталогу флагов
- количество admin IDs
- итоговый runtime preflight report

## Data Pipeline

Скрипт `scripts/fetch_countries_data.py`:

- загружает страны из открытого источника `restcountries`
- оставляет только государства-члены ООН
- нормализует поля под нужды бота
- сохраняет локальные SVG-флаги в `data/flags/`
- сохраняет итоговый dataset в `data/normalized/countries.json`

Проверка dataset:

```bash
python scripts/validate_countries_data.py
```

Рантайм бота не использует внешние API. Сеть нужна только на этапе подготовки локальных данных.

## Admin и ops

В боте для разрешённых `ADMIN_IDS` доступна команда `/admin`.

Сейчас через бота доступны:

- admin overview
- weakest / strongest progress
- catalog dashboard
- catalog health-check
- dataset revalidate
- sync preview
- confirmable catalog sync

Catalog dashboard в `/admin` теперь дополнительно показывает:

- когда был собран текущий dashboard
- время последнего изменения локального `countries.json`
- время последнего обновления DB catalog

CLI-утилиты:

```bash
python scripts/country_catalog_summary.py
python scripts/check_country_catalog.py
python scripts/admin_overview.py
python scripts/admin_progress_report.py
python scripts/runtime_preflight.py
```

## Проверки

Полный прогон:

```bash
pytest
ruff check app tests scripts
```

## Deploy checklist

Перед выкладкой стоит пройти этот минимум:

1. `python scripts/validate_countries_data.py`
2. `alembic upgrade head`
3. `python scripts/sync_countries_to_db.py`
4. `python scripts/runtime_preflight.py`
5. `pytest`
6. `ruff check app tests scripts`

Рекомендуемые env-поля для runtime:

- `APP_ENV`
- `DATABASE_URL`
- `COUNTRIES_DATA_PATH`
- `FLAGS_DIR`
- `LOG_LEVEL`
- `ADMIN_IDS`

Для Docker-потока те же шаги можно выполнить через `data`, `migrate`, `sync`, `preflight`.

## Что дальше легко нарастить

- более продвинутый review dashboard
- richer user stats screens
- более гибкие SRS-правила
- расширенную admin panel
- web-клиент поверх того же domain-слоя
