# LexRO — Development Journal

Short log of what was done and why. Source material for the final documentation.

---

## 2026-10-14 — Repo setup, data pipeline, naive RAG v0.1

### Repo & environment
- Monorepo at `C:\Users\GOGUL\Documents\LexRO` (same layout as Licenta-BioAI): `AI-Module/` (Python) + `BackEnd/lexro-api/` (Java).
- Code lives on Windows; Python runs in WSL via `/mnt/c/...`; Java will run natively on Windows in IntelliJ.
- Repo created and published with GitHub Desktop (no Git CLI on Windows needed).
- Added `.gitattributes` forcing LF line endings, to avoid the CRLF/LF issues from the thesis project.
- Verified workflow: edit in VS Code (Remote-WSL) → change visible in GitHub Desktop.
- Dedicated conda env `lexro` (Python 3.11), separate from the SSL projects.

### Data: Codul Muncii
- Source: legislatie.just.ro, document ID **309240** (consolidated version of 27.04.2026). An older ID (302270) was not the latest version — always check "istoric consolidări".
- `src/scrapers/fetch.py`: downloads the raw HTML once into `data/raw/` (avoids hitting the site on every test).
- `src/scrapers/parse.py`: parses articles using the site's CSS classes (`S_ART`, `S_ART_TTL`, `S_ART_BDY`, `S_ALN`).
  - Removed noise: amendment notes (`S_PAR`), editor notes (`S_NTA`), repealed paragraphs ("Abrogat").
  - Each article keeps a direct anchor URL (`...309240#id_artA1014`) for clickable citations.
  - Result: **297 articles** in `data/processed/codul_muncii.json`.
- `data/` is gitignored; data is reproducible by re-running the two scripts.

### Infrastructure
- Docker Desktop: enabled WSL integration for Ubuntu.
- WSL could not reach Windows `localhost` (Ollama) → set `networkingMode=mirrored` in `%USERPROFILE%\.wslconfig`.
- Qdrant 1.19.2 in Docker, data on a **named Docker volume** (not `/mnt/c/` — risk of corruption on the Windows filesystem). Dashboard: `localhost:6333/dashboard`.
- Ollama on Windows with `llama3.1:8b` (Q4_K_M), already available from the thesis.
- PyTorch **2.14.1+cu130** — the CUDA 13.0 build is required for the RTX 5070 (Blackwell, sm_120).

### Naive RAG v0.1
- Embeddings: `BAAI/bge-m3` (1024-dim, multilingual, contrastively trained). Sanity check: question↔leave article 0.72 vs question↔tax sentence 0.417.
- `src/rag/ingest.py`: embeds `law + article + text`, stores vectors + full article payload in Qdrant collection `lexro_articles` (297 points, ~10s).
- `src/rag/retrieve.py`: dense top-k search. Correct article ranked #1 on all 3 test questions (Art. 145 leave, Art. 81 resignation, Art. 121 overtime).
- `src/rag/generate.py`: top-5 articles as numbered context → llama3.1 (temperature 0.1) with a prompt that forces answering only from context and citing [n].
- First end-to-end answer correct and cited (Art. 145, 20 working days).

### Observations / next
- Retrieval scores are tightly clustered (0.63–0.70): correct article wins narrowly → motivates reranking (stage 4).
- Off-topic neighbours (e.g. dismissal articles for a resignation question) → reranker should filter these.
- Answers are minimal and all 5 sources are listed even if only [1] is cited → improve prompt, show only cited sources, verify citations (stage 5).
- Next: build a ~30-question test set with gold articles, measure Recall@5 → baseline for the ablation study.