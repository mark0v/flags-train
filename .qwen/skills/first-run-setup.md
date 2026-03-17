# Flags Train: First Run Setup

## Goal

Use this guide for the very first local setup of the project or when rebuilding a fresh environment.

The project needs three things before the bot can answer quiz questions:
- PostgreSQL
- local country data and flags
- a synced `countries` catalog in the database

---

## Local Python path

### 1. Start PostgreSQL

```powershell
docker compose up -d db
```

Optional check:

```powershell
docker compose ps db
```

### 2. Install dependencies

```powershell
python -m pip install -e .[dev]
```

This installs runtime dependencies and developer tools such as `pytest` and `ruff`.

### 3. Prepare local data

```powershell
python scripts/fetch_countries_data.py
```

This prepares:
- local flags in `data/flags/`
- normalized country data in `data/normalized/countries.json`

The runtime is designed to work offline after this step.

### 4. Apply migrations

```powershell
python -m alembic upgrade head
```

This creates the application schema, including:
- `users`
- `quiz_runs`
- `quiz_answers`
- `user_learning_progress`
- `countries`

### 5. Sync countries into PostgreSQL

```powershell
python scripts/sync_countries_to_db.py
```

This step is required. Without it, the quiz catalog is not available to the bot.

### 6. Run runtime preflight

```powershell
python scripts/runtime_preflight.py
```

This verifies:
- database connectivity
- dataset presence and validity
- local flag availability
- migration state

### 7. Start the bot

```powershell
python -m scripts.run_bot
```

Use this module form for local startup.

---

## Docker path

### Preparation

```powershell
docker compose up -d db
docker compose --profile ops run --rm migrate
docker compose --profile ops run --rm sync
docker compose --profile ops run --rm preflight
```

### Start the bot

```powershell
docker compose up --build bot
```

Important:
- local Python runs use `.env`
- Docker runs in this project use `.env.docker`

If the bot works locally but not in Docker, compare those two files first.

---

## Minimal verification

After startup:
1. Open the bot in Telegram.
2. Send `/start`.
3. Select a language.
4. Start a quiz.
5. Confirm that the first question appears with a flag and answer buttons.

---

## Common problems

| Problem | Suggested fix |
|---------|---------------|
| `alembic` is not found | Use `python -m alembic upgrade head` |
| Quiz does not start | Run `python scripts/sync_countries_to_db.py` |
| Flags or dataset are missing | Run `python scripts/fetch_countries_data.py` |
| Database is unavailable | Run `docker compose up -d db` |
| Docker bot does not answer | Check `docker compose logs --tail=100 bot` and compare `.env` vs `.env.docker` |

---

## Safe reruns

These setup steps are safe to rerun when needed:
- `python scripts/fetch_countries_data.py`
- `python scripts/sync_countries_to_db.py`
- `python scripts/runtime_preflight.py`

This is useful after updating data, recreating the database, or validating a new environment.
