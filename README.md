# Flags Train

Telegram-бот для изучения флагов, столиц, языков, населения и валют стран ООН в формате Anki-подобного квиза.

## Что уже заложено

- aiogram 3 + inline-first UX
- PostgreSQL + SQLAlchemy + Alembic
- локализация `ru / en / de`
- локальный `countries.json` и локальная папка с флагами
- статистика, межсессионный прогресс и базовый spaced repetition
- режимы квиза: `mixed / review / new`
- Dockerfile, `docker-compose.yml`, `.env.example`
- unit-тесты для ядра квиза, статистики и подготовки данных

## Структура

- `app/` - бот, сервисы, БД, локализация
- `scripts/fetch_countries_data.py` - data pipeline для загрузки и нормализации локальных данных
- `data/normalized/` - нормализованный датасет
- `data/flags/` - локальные флаги
- `tests/` - unit-тесты

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните `BOT_TOKEN`.
2. Подготовьте локальные данные:

```bash
python scripts/fetch_countries_data.py
```

3. Запустите через Docker:

```bash
docker compose up --build
```

Или локально:

```bash
pip install -e .[dev]
alembic upgrade head
python -m app.main
```

## Data Pipeline

Скрипт `scripts/fetch_countries_data.py`:

- берет страны из открытого источника `restcountries`
- фильтрует только `unMember == true`
- сохраняет только страны, у которых есть валюта и двухбуквенный код флага
- нормализует поля под нужды бота
- скачивает SVG-флаги локально в `data/flags`
- сохраняет итоговый файл `data/normalized/countries.json`

Рантайм бота не использует внешние API. Сеть нужна только для подготовки локального датасета.

## Dev / Prod

- миграции применяются отдельно через Alembic
- конфиг читается из env
- данные лежат локально и доступны контейнеру через volume
- data pipeline отделен от рантайма бота: данные можно обновлять вручную или отдельным job

## Что дальше легко нарастить

- отдельный review dashboard
- более гибкие интервалы SRS
- админскую панель
- web-клиент поверх того же quiz/domain слоя
