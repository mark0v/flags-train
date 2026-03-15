from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import orjson

from app.services.data_pipeline import normalize_country

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = PROJECT_ROOT / "data" / "normalized" / "countries.json"
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"

async def download_flag(client: httpx.AsyncClient, url: str, target_path: Path) -> None:
    response = await client.get(url, timeout=60)
    response.raise_for_status()
    target_path.write_bytes(response.content)


async def main() -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(RESTCOUNTRIES_URL, timeout=60)
        response.raise_for_status()
        payload = response.json()

        normalized: list[dict] = []
        tasks = []
        for item in payload:
            if not item.get("unMember") or not item.get("currencies") or not item.get("cca2"):
                continue
            normalized_country = normalize_country(item)
            normalized.append(normalized_country)
            tasks.append(
                download_flag(
                    client,
                    item["flags"]["svg"],
                    FLAGS_DIR / normalized_country["flag_file"],
                )
            )

        await asyncio.gather(*tasks)
        normalized.sort(key=lambda row: row["localized_name"]["en"])
        OUTPUT_JSON.write_bytes(orjson.dumps(normalized, option=orjson.OPT_INDENT_2))
        print(f"Saved {len(normalized)} countries to {OUTPUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
