# Flags Train: Running the Bot

## Option 1: Docker

### Preparation

```powershell
# 1. Start PostgreSQL
docker compose up -d db

# 2. Apply migrations
docker compose --profile ops run --rm migrate

# 3. Sync countries into PostgreSQL
docker compose --profile ops run --rm sync

# 4. Run preflight checks
docker compose --profile ops run --rm preflight
```

### Start the bot

```powershell
# Start only the bot when the database is already running
docker compose up --build bot

# Or start both database and bot together
docker compose up --build db bot
```

### Optional Docker debug path

Use this only when the bot container looks healthy but the bot does not answer in Telegram.

```powershell
# Rebuild and restart the bot container
docker compose up -d --build bot

# Confirm container status
docker compose ps

# Inspect recent bot logs
docker compose logs --tail=100 bot
```

When debugging this scenario, check for:
- `Runtime preflight report`
- `Overall: READY`
- `Bot polling started`
- `Run polling for bot @...`

If the bot still does not answer, compare `.env` and `.env.docker`:
- local Python runs read `.env`
- Docker compose for this project uses `.env.docker`

One known failure mode is Telegram rejecting menu rendering with:
- `Bad Request: text must be non-empty`

If that appears in logs, inspect the menu handler first.

---

## Option 2: Local Python

### Preparation

```powershell
# 1. Make sure PostgreSQL is running
docker compose up -d db

# 2. Install dependencies
python -m pip install -e .[dev]

# 3. Apply migrations
python -m alembic upgrade head

# 4. Sync countries into the database
python scripts/sync_countries_to_db.py

# 5. Run preflight checks
python scripts/runtime_preflight.py
```

### Start the bot

```powershell
# Correct local entrypoint
python -m scripts.run_bot
```

---

## Important

| Requirement | Details |
|------------|--------|
| `.env` | Must be filled in locally (`BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS`) |
| Local start | Use `python -m scripts.run_bot`, not `python scripts/run_bot.py` |
| Sync | After fresh migrations, `sync` is required before quiz flows work |
| Preflight | Optional, but strongly recommended before startup |

---

## Quick checks

```powershell
# After startup, the bot should respond to /start in Telegram
```

If it does not respond:
- verify `BOT_TOKEN`
- make sure there is no second running bot process
- inspect startup logs for Telegram or database errors

---

## Troubleshooting

| Problem | Suggested fix |
|---------|---------------|
| Quiz does not work | Run `python scripts/sync_countries_to_db.py` or Docker `sync` |
| Bot does not answer | Check token, inspect logs, compare `.env` vs `.env.docker` |
| Migrations do not apply | Check `DATABASE_URL` and database reachability |
| Flag assets are missing | Run `fetch_countries_data.py` |
