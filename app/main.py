from __future__ import annotations

import csv
import math
import re
from collections import Counter
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


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return answer_question(request.question)
