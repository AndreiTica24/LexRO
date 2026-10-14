"""Download a law page from legislatie.just.ro and save the raw HTML locally."""

from pathlib import Path

import requests

BASE_URL = "https://legislatie.just.ro/Public/DetaliiDocument/{doc_id}"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def fetch_law(doc_id: int, name: str) -> Path:
    """Download one law page and save it as data/raw/<name>.html."""
    url = BASE_URL.format(doc_id=doc_id)
    headers = {"User-Agent": "Mozilla/5.0 (LexRO research project)"}

    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    response.encoding = "utf-8"  # Romanian diacritics

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"{name}.html"
    out_path.write_text(response.text, encoding="utf-8")

    print(f"Saved {url} -> {out_path} ({len(response.text):,} chars)")
    return out_path


if __name__ == "__main__":
    fetch_law(doc_id=309240, name="codul_muncii")