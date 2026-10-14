"""Naive RAG: retrieve articles, then let the LLM answer only from them."""

import requests

from src.rag.retrieve import DenseRetriever

OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """Ești un asistent juridic pentru legislația română.
Răspunzi DOAR pe baza articolelor de lege primite în context.
Reguli:
- Răspunde în română, clar și concis.
- După fiecare afirmație pune sursa între paranteze drepte, ex. [1], [2], folosind numărul articolului din context.
- Dacă articolele din context nu conțin răspunsul, spune explicit că nu ai găsit informația. Nu inventa.
- Nu oferi consultanță juridică; explici ce spune legea."""


def build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(f"[{i}] {hit['law']}, {hit['article']}\n{hit['text']}")
    return "\n\n".join(blocks)


def answer(question: str, retriever: DenseRetriever, top_k: int = 5) -> dict:
    hits = retriever.search(question, top_k=top_k)
    user_msg = f"Context:\n{build_context(hits)}\n\nÎntrebare: {question}"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
            "options": {"temperature": 0.1},  # low = factual, less creative
        },
        timeout=180,
    )
    response.raise_for_status()

    return {
        "answer": response.json()["message"]["content"],
        "sources": [
            {"id": i, "article": h["article"], "law": h["law"], "url": h["url"]}
            for i, h in enumerate(hits, start=1)
        ],
    }


if __name__ == "__main__":
    retriever = DenseRetriever()
    result = answer("Câte zile de concediu de odihnă am pe an?", retriever)
    print(result["answer"])
    print("\nSurse:")
    for s in result["sources"]:
        print(f"  [{s['id']}] {s['law']}, {s['article']} — {s['url']}")