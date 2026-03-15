from __future__ import annotations

import asyncio

from app.config import get_settings
from app.services.runtime_checks import (
    format_runtime_preflight_report,
    run_runtime_preflight,
    runtime_preflight_failure_message,
)


def main() -> None:
    settings = get_settings()
    report = asyncio.run(run_runtime_preflight(settings))
    print(format_runtime_preflight_report(report))
    if not report.is_ready:
        raise SystemExit(runtime_preflight_failure_message(report))


if __name__ == "__main__":
    main()
