# Flags Train

Telegram bot for learning the flags, capitals, languages, populations, and currencies of UN member states in an Anki-like quiz format.

## Current Features

- `aiogram 3` with inline-first UX
- `PostgreSQL + SQLAlchemy + Alembic`
- localization for `ru / en / de`
- local offline dataset: `data/normalized/countries.json`
- local SVG and PNG flags in `data/flags/`
- quiz modes: `mixed / review / new`
- cross-session learning progress
- user statistics
- SRS prioritization based on `proficiency_score`, `current_streak`, and `next_review_at`
- built-in `/admin` with safe catalog actions
- runtime preflight before startup
- startup logging with an explicit preflight report
- Dockerfile, `docker-compose.yml`, `.env.example`
- tests and `ruff`

## Project Structure

- `app/` - bot, services, database, localization, and domain logic
- `alembic/` - database migrations
- `data/normalized/` - local country dataset
- `data/flags/` - local flag assets
- `scripts/` - data pipeline, sync, preflight, and dev/admin CLI tools
- `tests/` - unit and integration tests

## Quick Start

1. Create `.env` from `.env.example` and fill in `BOT_TOKEN`.

2. Install dependencies:

```bash
pip install -e .[dev]
```

3. Validate the local dataset:

```bash
python scripts/validate_countries_data.py
```

4. Apply migrations:

```bash
alembic upgrade head
```

5. Sync the country catalog into the database:

```bash
python scripts/sync_countries_to_db.py
```

6. Run the preflight check:

```bash
python scripts/runtime_preflight.py
```

Expected output example:

```text
Overall: READY
Dataset: OK (countries=193, range=AFG-ZWE)
Database: OK (revision=...)
Migrations: OK (current=..., expected=...)
```

7. Start the bot:

```bash
python scripts/run_bot.py
```

## Docker Compose

Primary runtime:

```bash
docker compose up --build db bot
```

Prepare local data inside Docker:

```bash
docker compose --profile setup run --rm data
```

Operational one-shot services:

```bash
docker compose --profile ops run --rm migrate
docker compose --profile ops run --rm sync
docker compose --profile ops run --rm preflight
```

Recommended order for the first Docker-based launch:

```bash
docker compose up -d db
docker compose --profile ops run --rm migrate
docker compose --profile ops run --rm sync
docker compose --profile ops run --rm preflight
docker compose up --build bot
```

`bot` no longer runs migrations automatically on startup. This is intentional so runtime startup remains predictable and safer for production-like environments.

`run_bot.py` now logs:

- `APP_ENV`
- local dataset path
- flags directory path
- number of admin IDs
- final runtime preflight report

## Data Pipeline

The `scripts/fetch_countries_data.py` script:

- downloads country data from the public `restcountries` source
- keeps only UN member states
- normalizes fields for the bot's needs
- saves local SVG and PNG flags into `data/flags/`
- writes the final dataset to `data/normalized/countries.json`

Validate the dataset:

```bash
python scripts/validate_countries_data.py
```

The bot runtime does not use external APIs. Network access is only required during local data preparation.

## Admin and Ops

The bot exposes `/admin` for users listed in `ADMIN_IDS`.

Currently available inside the bot:

- admin overview
- weakest / strongest progress
- catalog dashboard
- catalog health-check
- dataset revalidation
- sync preview
- confirmable catalog sync

The catalog dashboard in `/admin` also shows:

- when the current dashboard snapshot was generated
- last modification time of local `countries.json`
- last update time of the database catalog

CLI tools:

```bash
python scripts/country_catalog_summary.py
python scripts/check_country_catalog.py
python scripts/admin_overview.py
python scripts/admin_progress_report.py
python scripts/runtime_preflight.py
```

## Checks

Full validation run:

```bash
pytest
ruff check app tests scripts
```

## Deploy Checklist

Before deployment, run at least this minimum set:

1. `python scripts/validate_countries_data.py`
2. `alembic upgrade head`
3. `python scripts/sync_countries_to_db.py`
4. `python scripts/runtime_preflight.py`
5. `pytest`
6. `ruff check app tests scripts`

Recommended runtime environment variables:

- `APP_ENV`
- `DATABASE_URL`
- `COUNTRIES_DATA_PATH`
- `FLAGS_DIR`
- `LOG_LEVEL`
- `ADMIN_IDS`

For the Docker workflow, the same steps can be executed through `data`, `migrate`, `sync`, and `preflight`.

## Easy Next Extensions

- a more advanced review dashboard
- richer user statistics screens
- more flexible SRS rules
- an expanded admin panel
- a web client on top of the same domain layer
