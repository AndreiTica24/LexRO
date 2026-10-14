# AI-Module

Python service for LexRO — RAG pipeline over Romanian legislation.

## Setup

```bash
conda create -n lexro python=3.11 -y
conda activate lexro
pip install -r requirements.txt
```

## Structure

- `src/scrapers/` — fetchers for legislatie.just.ro (one script per law)
- `data/raw/` — raw HTML saved from scrapers
- `data/processed/` — structured JSON (articles split, cleaned, ready for ingestion)

## Status

Early scaffolding — scraper for Codul Muncii in progress.