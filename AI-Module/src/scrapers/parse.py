"""Parse a raw law HTML from legislatie.just.ro into structured articles (JSON)."""

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

AI_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = AI_ROOT / "data" / "raw"
PROCESSED_DIR = AI_ROOT / "data" / "processed"
BASE_URL = "https://legislatie.just.ro/Public/DetaliiDocument/{doc_id}"

# Editorial noise we never want in the article text
NOISE_CLASSES = ["S_PAR", "S_NTA", "TAG_COLLAPSED"]


def clean(text: str) -> str:
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", text).strip()


def parse_article(art, doc_id: int, law: str, law_id: str) -> dict | None:
    title_tag = art.find(class_="S_ART_TTL")
    body = art.find(class_="S_ART_BDY")
    if title_tag is None or body is None:
        return None

    # Drop modification notes and editor notes before extracting text
    for noise in body.find_all(class_=NOISE_CLASSES):
        noise.decompose()

    paragraphs = [clean(aln.get_text(" ")) for aln in body.find_all(class_="S_ALN")]
        # Drop empty paragraphs and repealed paragraphs like "(5) Abrogat."
    paragraphs = [
        p for p in paragraphs
        if p and not re.fullmatch(r"(\([^)]*\)\s*)?abrogat\.?", p, flags=re.IGNORECASE)
    ]
    text = "\n".join(paragraphs) if paragraphs else clean(body.get_text(" "))

    name_tag = art.find(class_="S_ART_DEN")
    article = clean(title_tag.get_text())

    return {
        "law": law,
        "law_id": law_id,
        "article": article,
        "name": clean(name_tag.get_text()) if name_tag else "",
        "text": text,
        "paragraphs": paragraphs,
        "repealed": text.lower().startswith("abrogat"),
        "url": f"{BASE_URL.format(doc_id=doc_id)}#{art.get('id', '')}",
    }


def parse_law(name: str, doc_id: int, law: str, law_id: str) -> Path:
    html = (RAW_DIR / f"{name}.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    articles = []
    for art in soup.find_all(class_="S_ART"):
        parsed = parse_article(art, doc_id, law, law_id)
        if parsed:
            articles.append(parsed)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{name}.json"
    out_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")

    repealed = sum(a["repealed"] for a in articles)
    print(f"{law}: {len(articles)} articles ({repealed} repealed) -> {out_path}")
    return out_path


if __name__ == "__main__":
    parse_law(
        name="codul_muncii",
        doc_id=309240,
        law="Codul Muncii",
        law_id="Legea nr. 53/2003",
    )