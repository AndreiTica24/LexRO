"""Dense retrieval: find the law articles closest in meaning to a question."""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_URL = "http://localhost:6333"
COLLECTION = "lexro_articles"
EMBED_MODEL = "BAAI/bge-m3"


class DenseRetriever:
    def __init__(self):
        self.model = SentenceTransformer(EMBED_MODEL, device="cuda")
        self.client = QdrantClient(url=QDRANT_URL)

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        query_vec = self.model.encode(question, normalize_embeddings=True)
        hits = self.client.query_points(
            collection_name=COLLECTION,
            query=query_vec.tolist(),
            limit=top_k,
        ).points
        return [{**hit.payload, "score": hit.score} for hit in hits]


if __name__ == "__main__":
    retriever = DenseRetriever()
    questions = [
        "Câte zile de concediu de odihnă am pe an?",
        "Ce preaviz trebuie să dau dacă îmi dau demisia?",
        "Angajatorul mă poate obliga să fac ore suplimentare?",
    ]
    for q in questions:
        print(f"\n? {q}")
        for hit in retriever.search(q, top_k=5):
            print(f"  {hit['score']:.3f}  {hit['article']:<16} {hit['text'][:90]}")