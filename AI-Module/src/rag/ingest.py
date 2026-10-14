"""Embed parsed law articles with bge-m3 and store them in Qdrant."""

import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

AI_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = AI_ROOT / "data" / "processed"

QDRANT_URL = "http://localhost:6333"
COLLECTION = "lexro_articles"
EMBED_MODEL = "BAAI/bge-m3"
VECTOR_DIM = 1024


def article_to_text(article: dict) -> str:
    """Text that gets embedded: law + article number give context to the body."""
    return f"{article['law']}, {article['article']}\n{article['text']}"


def ingest(law_files: list[str]) -> None:
    articles = []
    for name in law_files:
        path = PROCESSED_DIR / f"{name}.json"
        articles.extend(json.loads(path.read_text(encoding="utf-8")))
    print(f"Loaded {len(articles)} articles from {len(law_files)} law(s)")

    model = SentenceTransformer(EMBED_MODEL, device="cuda")
    model.max_seq_length = 2048  # long enough for any article, keeps VRAM in check

    vectors = model.encode(
        [article_to_text(a) for a in articles],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    client = QdrantClient(url=QDRANT_URL)
    # Rebuild from scratch on every run so the index always matches the JSON
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )

    points = [
        PointStruct(id=i, vector=vec.tolist(), payload=article)
        for i, (article, vec) in enumerate(zip(articles, vectors))
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    count = client.count(COLLECTION).count
    print(f"Indexed {count} articles into '{COLLECTION}'")


if __name__ == "__main__":
    ingest(["codul_muncii"])