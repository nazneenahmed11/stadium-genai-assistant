"""
Lightweight retrieval layer for the stadium assistant.

For a hackathon-scale prototype we don't need a full vector database -
a keyword-matching retriever over a small structured JSON dataset is
transparent, fast, fully offline-testable, and easy to explain to judges.
It can be swapped for a real vector store (e.g. Chroma, FAISS) later
without changing the rest of the app.
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stadium_data.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    STADIUM_DATA = json.load(f)


def _flatten_records():
    """Turn the structured JSON into a flat list of (text, source_dict) pairs."""
    records = []

    for gate in STADIUM_DATA.get("gates", []):
        text = (
            f"{gate['name']}: {gate['description']} "
            f"Accessible: {'yes' if gate['accessible'] else 'no'}. "
            f"Average wait: {gate['avg_wait_minutes']} minutes."
        )
        records.append((text, {"type": "gate", **gate}))

    for r in STADIUM_DATA.get("restrooms", []):
        text = (
            f"Restroom at {r['location']}. "
            f"Accessible: {'yes' if r['accessible'] else 'no'}. "
            f"Average queue: {r['avg_queue_minutes']} minutes."
        )
        records.append((text, {"type": "restroom", **r}))

    for t in STADIUM_DATA.get("transport_options", []):
        text = (
            f"{t['mode']}: {t['details']} "
            f"Last departure after match: {t['last_departure_after_match']}."
        )
        records.append((text, {"type": "transport", **t}))

    for a in STADIUM_DATA.get("accessibility_services", []):
        records.append((a, {"type": "accessibility_service", "detail": a}))

    for faq in STADIUM_DATA.get("faqs", []):
        text = f"Q: {faq['question']} A: {faq['answer']}"
        records.append((text, {"type": "faq", **faq}))

    return records


_RECORDS = _flatten_records()


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Return the top_k most relevant records to the query as a single
    context string, using simple keyword overlap scoring.
    """
    query_words = set(query.lower().split())
    scored = []

    for text, _meta in _RECORDS:
        text_words = set(text.lower().replace(",", "").replace(".", "").split())
        overlap = len(query_words & text_words)
        if overlap > 0:
            scored.append((overlap, text))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [text for _score, text in scored[:top_k]]

    # Fallback: if nothing matched by keyword, give the model a general
    # snapshot so it can still answer broad questions like "tell me about the venue"
    if not top:
        top = [text for text, _meta in _RECORDS[:top_k]]

    return "\n".join(f"- {t}" for t in top)


def venue_name() -> str:
    return STADIUM_DATA.get("venue_name", "the stadium")
