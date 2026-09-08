# Rulebook Lens

An evidence-first question-answering service for university regulations. It answers only from its local corpus, displays the retrieved passages and scores beside every answer, and flags genuine policy contradictions instead of hiding them.

## Features

- `POST /ask` API and a responsive local web interface
- Three explicit outcomes: `answered`, `not_covered`, and `conflict`
- Citation cards with section, source file, excerpt, and similarity score
- Mixed corpus formats: Markdown policy chapters, CSV fee deadlines, and a PDF examination circular
- A deterministic, dependency-light retrieval pipeline that works offline
- Built-in evaluation suite: planted conflicts and 25 deliberately unanswerable questions

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/build_corpus.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs.

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

The project includes `data/evaluation.json`, documenting the three intentional contradictions and 25 questions that should result in `not_covered`.

## Design note

This is a transparent retrieval prototype rather than a chatbot. It does not call an external LLM, so it cannot invent policy. Retrieval uses token similarity plus topic matching; the answer renderer only summarizes retrieved policy text.
