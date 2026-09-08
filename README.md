# Rulebook Lens

An evidence-first question-answering service for university regulations. It answers only from its local corpus, displays the retrieved passages and scores beside every answer, and flags genuine policy contradictions instead of hiding them.

## Features

- `POST /ask` API and a responsive local web interface
- Three explicit outcomes: `answered`, `not_covered`, and `conflict`
- Citation cards with section, source file, excerpt, and similarity score
- Mixed corpus formats: Markdown policy chapters, CSV fee deadlines, and a PDF examination circular
- A deterministic, dependency-light retrieval pipeline that works offline
- Built-in evaluation suite: planted conflicts and 25 deliberately unanswerable questions
- Evidence Lab dashboard with corpus statistics, conflict test register, and JSON session export
- Human-review queue for conflicts, plus Docker deployment files for a repeatable company demo
- Optional OpenAI-grounded summaries that never control coverage, citations, or conflict decisions

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/build_corpus.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs.

## Optional OpenAI-grounded answers

The deterministic policy engine always determines citations, coverage, and conflicts. To add an AI-written plain-language summary for **answered** results only, configure the server with a key and a model name. Never commit the key.

```bash
cp .env.example .env
# Edit .env locally; do not commit it. Set:
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-5-mini
uvicorn app.main:app --reload
```

The integration uses the OpenAI Responses API with `store=False`. Conflict and not-covered outcomes intentionally bypass the model, ensuring that AI cannot conceal a contradiction or invent a policy.

## Deploy to Render

This repository includes `render.yaml` for a Docker-based Render Web Service. In
Render, create a **New + Blueprint**, connect
`https://github.com/sampada34/rulebook-lens`, and select the repository. Render
will use the tracked configuration, health-check `/health`, and deploy every new
commit to `main` automatically.

The optional OpenAI integration works without any source-code change: add
`OPENAI_API_KEY` and `OPENAI_MODEL=gpt-5-mini` as Render environment variables
in the dashboard. Do not place either value in `render.yaml` or commit a `.env`
file. The free deployment is suitable for a public demo; its local SQLite review
queue may be reset after a redeploy, so use a managed database before production.

## API

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question":"Can I sit an exam with 68% attendance?"}'
```

The response contains `status`, a plain-language `answer`, and visible `citations`.

## Evaluation

```bash
pytest -q
```

The repository includes `pytest.ini`, so both `pytest -q` and `python -m pytest -q`
run from the project directory resolve the local application package correctly.

The project includes `data/evaluation.json`, documenting the three intentional contradictions and 25 questions that should result in `not_covered`.

## Design note

This is a transparent retrieval prototype rather than a chatbot. It does not call an external LLM, so it cannot invent policy. Retrieval uses token similarity plus topic matching; the answer renderer only summarizes retrieved policy text.
