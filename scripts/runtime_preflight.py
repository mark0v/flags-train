from __future__ import annotations

import asyncio

from app.config import get_settings
from app.services.runtime_checks import run_runtime_preflight


def main() -> None:
    settings = get_settings()
    report = asyncio.run(run_runtime_preflight(settings))
    if not report.dataset.is_valid:
        raise SystemExit(report.dataset.error or "Dataset validation failed.")
    if not report.database.is_reachable:
        raise SystemExit(report.database.error or "Database is not reachable.")
    if not report.database.migrations_match:
        raise SystemExit(
            "Database schema is out of date. "
            f"Current revision: {report.database.current_revision or '-'}. "
            f"Expected revision: {report.database.expected_revision}."
        )

    print(
        "Runtime preflight is OK. "
        f"Dataset countries: {report.dataset.countries_count}. "
        f"DB revision: {report.database.current_revision}."
    )


if __name__ == "__main__":
    main()
