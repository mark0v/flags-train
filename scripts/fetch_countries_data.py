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
from app.services.flag_previews import build_flag_preview

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
RESTCOUNTRIES_FIELDS = [
    "name",
    "translations",
    "capital",
    "languages",
    "currencies",
    "population",
    "cca2",
    "cca3",
    "flags",
    "unMember",
]
EXTRA_UN_MEMBER_LOOKUPS = ["guinea-bissau"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = PROJECT_ROOT / "data" / "normalized" / "countries.json"
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"
CONCURRENCY_LIMIT = 8
HTTP_HEADERS = {
    "User-Agent": "flags-train-data-pipeline/0.1 (+https://github.com/openai/codex)",
    "Api-User-Agent": "flags-train-data-pipeline/0.1",
}


async def download_flag(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    target_path: Path,
    *,
    normalize_preview: bool = False,
) -> None:
    async with semaphore:
        response = await client.get(url, timeout=60)
        response.raise_for_status()
        target_path.write_bytes(response.content)
        if normalize_preview:
            build_flag_preview(target_path, target_path)


async def fetch_country_lookup(client: httpx.AsyncClient, country_name: str) -> dict:
    response = await client.get(
        f"https://restcountries.com/v3.1/name/{country_name}",
        params={"fields": ",".join(RESTCOUNTRIES_FIELDS)},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload:
        raise ValueError(f"Country lookup returned no results for {country_name}.")
    return payload[0]


def remove_stale_flags(expected_flag_files: set[str]) -> int:
    removed = 0
    for path in list(FLAGS_DIR.glob("*.svg")) + list(FLAGS_DIR.glob("*.png")):
        if path.name not in expected_flag_files:
            path.unlink()
            removed += 1
    return removed


async def main() -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with httpx.AsyncClient(follow_redirects=True, headers=HTTP_HEADERS) as client:
        response = await client.get(
            RESTCOUNTRIES_URL,
            params={"fields": ",".join(RESTCOUNTRIES_FIELDS)},
            timeout=60,
        )
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
            svg_flag_file = normalized_country["flag_file"]
            png_flag_file = Path(svg_flag_file).with_suffix(".png").name
            expected_flag_files.add(svg_flag_file)
            expected_flag_files.add(png_flag_file)
            tasks.extend(
                [
                    download_flag(
                        client,
                        semaphore,
                        item["flags"]["svg"],
                        FLAGS_DIR / svg_flag_file,
                    ),
                    download_flag(
                        client,
                        semaphore,
                        item["flags"]["png"],
                        FLAGS_DIR / png_flag_file,
                        normalize_preview=True,
                    ),
                ]
            )

        existing_codes = {country["code"] for country in normalized}
        for country_name in EXTRA_UN_MEMBER_LOOKUPS:
            extra_item = await fetch_country_lookup(client, country_name)
            if extra_item["cca3"] in existing_codes:
                continue
            normalized_country = normalize_country(extra_item)
            normalized.append(normalized_country)
            existing_codes.add(normalized_country["code"])
            svg_flag_file = normalized_country["flag_file"]
            png_flag_file = Path(svg_flag_file).with_suffix(".png").name
            expected_flag_files.add(svg_flag_file)
            expected_flag_files.add(png_flag_file)
            tasks.extend(
                [
                    download_flag(
                        client,
                        semaphore,
                        extra_item["flags"]["svg"],
                        FLAGS_DIR / svg_flag_file,
                    ),
                    download_flag(
                        client,
                        semaphore,
                        extra_item["flags"]["png"],
                        FLAGS_DIR / png_flag_file,
                        normalize_preview=True,
                    ),
                ]
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
