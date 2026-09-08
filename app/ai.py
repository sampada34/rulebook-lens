"""Optional grounded answer synthesis using the OpenAI Responses API.

This module is deliberately fail-closed: it never decides coverage, citations, or
conflict status. Those decisions stay in the deterministic policy engine.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

from .main_types import CitationLike

load_dotenv()


def synthesize(question: str, citations: list[CitationLike]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None
    try:
        from openai import OpenAI
        evidence = "\n\n".join(f"[{c.section} | {c.source}]\n{c.excerpt}" for c in citations)
        response = OpenAI(api_key=api_key).responses.create(
            model=model,
            store=False,
            max_output_tokens=180,
            instructions=(
                "You are Rulebook Lens, a careful university-policy assistant. "
                "Answer using ONLY the supplied evidence. Do not invent rules, dates, "
                "exceptions, or citations. State uncertainty when the evidence is limited. "
                "Do not mention being an AI. Use plain language in no more than 90 words."
            ),
            input=f"Question: {question}\n\nEvidence:\n{evidence}",
        )
        text = response.output_text.strip()
        return text or None
    except Exception:
        # An unavailable provider must never make a policy answer unavailable.
        return None
