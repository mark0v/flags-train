from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import orjson

from app.services.data_pipeline import (
    dataset_summary,
    is_supported_country,
    normalize_country,
    validate_dataset,
)

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = PROJECT_ROOT / "data" / "normalized" / "countries.json"
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"
CONCURRENCY_LIMIT = 8


async def download_flag(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    target_path: Path,
) -> None:
    async with semaphore:
        response = await client.get(url, timeout=60)
        response.raise_for_status()
        target_path.write_bytes(response.content)


def remove_stale_flags(expected_flag_files: set[str]) -> int:
    removed = 0
    for path in FLAGS_DIR.glob("*.svg"):
        if path.name not in expected_flag_files:
            path.unlink()
            removed += 1
    return removed


async def main() -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(RESTCOUNTRIES_URL, timeout=60)
        response.raise_for_status()
        payload = response.json()

        normalized: list[dict] = []
        tasks = []
        expected_flag_files: set[str] = set()
        for item in payload:
            if not is_supported_country(item):
                continue
            normalized_country = normalize_country(item)
            normalized.append(normalized_country)
            expected_flag_files.add(normalized_country["flag_file"])
            tasks.append(
                download_flag(
                    client,
                    semaphore,
                    item["flags"]["svg"],
                    FLAGS_DIR / normalized_country["flag_file"],
                )
            )

        await asyncio.gather(*tasks)
        normalized.sort(key=lambda row: row["localized_name"]["en"])
        validate_dataset(normalized, FLAGS_DIR)
        OUTPUT_JSON.write_bytes(orjson.dumps(normalized, option=orjson.OPT_INDENT_2))
        removed_flags = remove_stale_flags(expected_flag_files)
        summary = dataset_summary(normalized)
        print(
            "Saved "
            f"{summary['countries_count']} countries to {OUTPUT_JSON}. "
            f"Removed stale flags: {removed_flags}."
        )


if __name__ == "__main__":
    asyncio.run(main())
