# Flags Train

Telegram-бот для изучения флагов, столиц, языков, населения и валют стран ООН в формате Anki-подобного квиза.

## Что уже заложено

- aiogram 3 + inline-first UX
- PostgreSQL + SQLAlchemy + Alembic
- локализация `ru / en / de`
- локальный `countries.json` и локальная папка с флагами
- генератор квиза с повтором ошибочных вопросов
- Dockerfile, `docker-compose.yml`, `.env.example`
- unit-тесты для ядра квиза и подготовки данных

## Структура

- `app/` — бот, сервисы, БД, локализация
- `scripts/fetch_countries_data.py` — data pipeline, который скачивает открытые данные и сохраняет локально
- `data/normalized/` — нормализованный датасет
- `data/flags/` — локальные флаги
- `tests/` — unit-тесты

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

## Data pipeline

Скрипт `scripts/fetch_countries_data.py`:

- берёт страны из открытого источника `restcountries`
- фильтрует только `unMember == true`
- нормализует поля под нужды бота
- скачивает SVG-флаги локально в `data/flags`
- сохраняет итоговый файл `data/normalized/countries.json`

Рантайм бота не использует внешние API.

## Dev / Prod подход

- миграции применяются отдельно через Alembic
- конфиг читается из env
- данные лежат в volume и доступны контейнеру локально
- бот отделён от pipeline: данные можно обновлять вручную или отдельным job

## Что дальше легко нарастить

- накопительную статистику и прогресс
- spaced repetition
- админскую панель
- web-клиент поверх того же quiz/domain слоя
