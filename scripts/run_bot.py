from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.main import main as run_bot
from app.services.runtime_checks import (
    format_runtime_preflight_report,
    run_runtime_preflight,
    runtime_preflight_failure_message,
)

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def validate_runtime() -> None:
    settings = get_settings()
    report = asyncio.run(run_runtime_preflight(settings))
    logger.info("Runtime preflight report\n%s", format_runtime_preflight_report(report))
    if not report.is_ready:
        raise SystemExit(runtime_preflight_failure_message(report))


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "Starting Flags Train bot env=%s dataset=%s flags_dir=%s admins=%s",
        settings.app_env,
        settings.resolve_path(settings.countries_data_path),
        settings.resolve_path(settings.flags_dir),
        len(settings.admin_ids),
    )
    validate_runtime()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
