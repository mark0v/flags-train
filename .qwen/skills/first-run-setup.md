# Flags Train: First Run Setup

## Quick Start

```powershell
# 1. Подними PostgreSQL
docker compose up -d db

# 2. Установи зависимости
pip install -e .[dev]

# 3. Подготовь данные (флаги + countries.json)
#    Можно запускать сколько угодно раз — безопасно перезаписывает
python scripts/fetch_countries_data.py

# 4. Примени миграции
python -m alembic upgrade head

# 5. Синхронизируй страны в БД
python scripts/sync_countries_to_db.py

# 6. Прогони preflight (опционально, проверка готовности)
python scripts/runtime_preflight.py

# 7. Запусти бота
python scripts/run_bot.py
```

## Детали по шагам

### Шаг 1: PostgreSQL

```powershell
docker compose up -d db
```

Проверка:
```powershell
docker compose ps db
```

### Шаг 2: Зависимости

```powershell
pip install -e .[dev]
```

Устанавливает: aiogram, SQLAlchemy, Alembic, asyncpg, pydantic-settings + dev-зависимости (pytest, ruff).

### Шаг 3: Data Pipeline

```powershell
python scripts/fetch_countries_data.py
```

Скачивает:
- 193 флага ООН в `data/flags/`
- Нормализованный `data/normalized/countries.json`

**Важно:** Бот работает без внешних API, все данные локальные.

### Шаг 4: Миграции БД

```powershell
python -m alembic upgrade head
```

Создаёт таблицы:
- `users` — пользователи Telegram
- `quiz_runs` — запуски квизов
- `quiz_answers` — ответы на вопросы
- `user_learning_progress` — прогресс обучения (SRS)
- `countries` — каталог стран

### Шаг 5: Синхронизация каталога

```powershell
python scripts/sync_countries_to_db.py
```

Загружает 193 страны из `data/normalized/countries.json` в таблицу `countries`.

**Без этого шага квиз не работает!**

### Шаг 6: Preflight (опционально)

```powershell
python scripts/runtime_preflight.py
```

Проверяет:
- ✅ БД доступна
- ✅ `countries.json` существует
- ✅ Флаги на месте
- ✅ Каталог синхронизирован

### Шаг 7: Запуск бота

```powershell
python scripts/run_bot.py
```

Или напрямую:
```powershell
python -m app.main
```

## Docker (альтернатива)

Для запуска через Docker:

```powershell
# .env должен содержать BOT_TOKEN
docker compose up --build
```

Бот применит миграции и запустится автоматически.

## Проверка работы

1. Отправь `/start` в Telegram
2. Выбери язык (RU/EN/DE)
3. Нажми **"Начать квиз"**
4. Выбери 10 стран + категорию "Флаг"
5. Квиз должен показать первый вопрос с флагом

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| `alembic: command not found` | Используй `python -m alembic` |
| Квиз завис на старте | Запусти `python scripts/sync_countries_to_db.py` |
| Нет флагов / устарели данные | Запусти `python scripts/fetch_countries_data.py` (безопасно) |
| БД недоступна | `docker compose up -d db` |

**Можно ли запускать `fetch_countries_data.py` повторно?**

Да, скрипт идемпотентный:
- Перезаписывает `countries.json`
- Обновляет флаги
- Удаляет устаревшие флаги
