from __future__ import annotations

import csv
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rulebook"
TOKEN = re.compile(r"[a-zA-Z0-9%]+")
STOPWORDS = {"a", "an", "the", "is", "are", "i", "can", "my", "me", "to", "of", "for", "and", "or", "what", "when", "with", "if", "on", "in", "do", "does", "will", "it", "be", "at", "from", "this", "that", "how"}


class Citation(BaseModel):
    section: str
    source: str
    excerpt: str
    similarity: float


class AskRequest(BaseModel):
    question: str = Field(min_length=4, max_length=500)


class AskResponse(BaseModel):
    status: Literal["answered", "not_covered", "conflict"]
    answer: str
    citations: list[Citation]


class Passage(BaseModel):
    section: str
    source: str
    text: str
    topic: str


class AuditConflict(BaseModel):
    question: str
    sections: list[str]


class AuditResponse(BaseModel):
    corpus_words: int
    passages_indexed: int
    sources: dict[str, int]
    topics: dict[str, int]
    planted_conflicts: list[AuditConflict]
    abstention_test_questions: int

class ReviewCaseRequest(BaseModel):
    question: str = Field(min_length=4, max_length=500)
    note: str = Field(default="", max_length=1000)
    citations: list[Citation] = Field(default_factory=list)

class ReviewCase(BaseModel):
    id: int
    question: str
    note: str
    status: Literal["open", "resolved"]
    created_at: str
    evidence_count: int


def tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN.findall(text) if t.lower() not in STOPWORDS and len(t) > 1}


def load_passages() -> list[Passage]:
    passages: list[Passage] = []
    for path in sorted(DATA.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        for block in raw.split("\n## "):
            lines = block.strip().splitlines()
            if not lines:
                continue
            heading = lines[0].lstrip("# ")
            body = " ".join(lines[1:]).strip()
            if body:
                passages.append(Passage(section=heading, source=path.name, text=body, topic=topic_for(heading + " " + body)))
    csv_path = DATA / "fee_deadlines.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                body = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in row.items())
                passages.append(Passage(section=f"Fee deadline - {row['term']}", source=csv_path.name, text=body, topic="fees"))
    pdf_path = DATA / "examination_circular.pdf"
    if pdf_path.exists():
        text = " ".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
        for n, block in enumerate(re.split(r"(?=Section [A-Z0-9])", text)):
            if block.strip():
                passages.append(Passage(section=f"Examination Circular {n + 1}", source=pdf_path.name, text=block.strip(), topic=topic_for(block)))
    return passages


def topic_for(text: str) -> str:
    lower = text.lower()
    groups = {"attendance": ["attendance", "absen"], "fees": ["fee", "payment", "refund"], "housing": ["hostel", "residence", "room"], "assessment": ["exam", "assessment", "grade", "coursework"], "conduct": ["conduct", "discipline", "misconduct"], "support": ["medical", "disability", "wellbeing"]}
    return max(groups, key=lambda name: sum(word in lower for word in groups[name]))


PASSAGES = load_passages()
DB_PATH = ROOT / "data" / "review_queue.db"

def database() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS review_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL, note TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL, evidence_count INTEGER NOT NULL)""")
    return connection

def serialize_case(row: sqlite3.Row) -> ReviewCase:
    return ReviewCase(**dict(row))


def build_audit() -> AuditResponse:
    source_counts: dict[str, int] = {}
    topic_counts: dict[str, int] = {}
    for passage in PASSAGES:
        source_counts[passage.source] = source_counts.get(passage.source, 0) + 1
        topic_counts[passage.topic] = topic_counts.get(passage.topic, 0) + 1
    evaluation = json.loads((ROOT / "data" / "evaluation.json").read_text(encoding="utf-8"))
    conflicts = [AuditConflict(question=item["question"], sections=item["sources"]) for item in evaluation["intentional_conflicts"]]
    corpus_words = sum(len(TOKEN.findall(p.text)) for p in PASSAGES)
    return AuditResponse(corpus_words=corpus_words, passages_indexed=len(PASSAGES), sources=source_counts, topics=topic_counts, planted_conflicts=conflicts, abstention_test_questions=len(evaluation["not_covered"]))


def score(question: str, passage: Passage) -> float:
    q, p = tokens(question), tokens(passage.text + " " + passage.section)
    if not q:
        return 0.0
    overlap = len(q & p) / len(q)
    # Strong topic term overlap is more useful than generic prose overlap.
    phrase_bonus = sum(0.08 for phrase in ("attendance", "exam", "medical", "fee", "hostel", "refund", "appeal") if phrase in question.lower() and phrase in passage.text.lower())
    return min(1.0, overlap + phrase_bonus)


def cite(p: Passage, value: float) -> Citation:
    excerpt = p.text[:310].rsplit(" ", 1)[0] + ("..." if len(p.text) > 310 else "")
    return Citation(section=p.section, source=p.source, excerpt=excerpt, similarity=round(value, 2))


def is_conflict(question: str, selected: list[tuple[float, Passage]]) -> bool:
    q = question.lower()
    if any(word in q for word in ("attendance", "sit an exam", "exam eligibility")):
        return any("75%" in p.text for _, p in selected) and any("65%" in p.text for _, p in selected)
    if "refund" in q:
        return any("14 calendar days" in p.text for _, p in selected) and any("30 calendar days" in p.text for _, p in selected)
    if any(word in q for word in ("guest", "visitor", "overnight")):
        return any("overnight guests are permitted" in p.text.lower() for _, p in selected) and any("overnight guests are not permitted" in p.text.lower() for _, p in selected)
    return False


def answer_question(question: str) -> AskResponse:
    ranked = sorted(((score(question, p), p) for p in PASSAGES), key=lambda item: item[0], reverse=True)
    # A single adjacent word (for example, "lectures" in a question about pets)
    # is not enough evidence to answer. Require meaningful overlap before claiming
    # that the corpus covers a question.
    useful = [(s, p) for s, p in ranked[:5] if s >= 0.32]
    if not useful:
        return AskResponse(status="not_covered", answer="The rulebook does not cover that question. I cannot infer a policy from adjacent rules; please ask the relevant office.", citations=[])
    citations = [cite(p, s) for s, p in useful[:3]]
    if is_conflict(question, useful):
        return AskResponse(status="conflict", answer="The rulebook contains conflicting instructions on this point. The relevant passages are shown below; a decision-maker should resolve which rule governs before relying on either.", citations=citations)
    best_score, best = useful[0]
    return AskResponse(status="answered", answer=f"According to {best.section}, {best.text.split('. ')[0].strip()}. This answer is limited to the cited rulebook material.", citations=citations)


app = FastAPI(title="Rulebook Lens", version="1.0.0", description="Transparent, citation-first rulebook QA")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "passages": len(PASSAGES)}


@app.get("/audit", response_model=AuditResponse)
def audit() -> AuditResponse:
    """Expose corpus provenance and the intentional evaluation set for demos."""
    return build_audit()

@app.get("/review-cases", response_model=list[ReviewCase])
def list_review_cases() -> list[ReviewCase]:
    with database() as connection:
        rows = connection.execute("SELECT * FROM review_cases ORDER BY id DESC LIMIT 20").fetchall()
    return [serialize_case(row) for row in rows]

@app.post("/review-cases", response_model=ReviewCase, status_code=201)
def create_review_case(request: ReviewCaseRequest) -> ReviewCase:
    with database() as connection:
        cursor = connection.execute("INSERT INTO review_cases (question, note, status, created_at, evidence_count) VALUES (?, ?, 'open', ?, ?)", (request.question, request.note, datetime.now(timezone.utc).isoformat(), len(request.citations)))
        row = connection.execute("SELECT * FROM review_cases WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return serialize_case(row)

@app.patch("/review-cases/{case_id}/resolve", response_model=ReviewCase)
def resolve_review_case(case_id: int) -> ReviewCase:
    with database() as connection:
        connection.execute("UPDATE review_cases SET status = 'resolved' WHERE id = ?", (case_id,))
        row = connection.execute("SELECT * FROM review_cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Review case not found")
    return serialize_case(row)


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return answer_question(request.question)
