# Stadium Assistant — GenAI Fan Support for FIFA World Cup 2026

A conversational, multilingual GenAI assistant that helps fans navigate stadium
operations in real time — built for the PromptWars Challenge 4 (AI Code Submission).

## Problem Statement Alignment

The challenge asks for a GenAI-enabled solution that improves **navigation,
crowd management, accessibility, transportation, sustainability, multilingual
assistance, operational intelligence, or real-time decision support** during
the FIFA World Cup 2026.

This project focuses deliberately on three of those pillars, done well,
rather than all eight, done shallowly:

- **Navigation** — fans ask natural-language questions ("where's the nearest
  restroom to Gate B?") and get grounded, specific answers instead of
  scrolling a static PDF map.
- **Accessibility** — the assistant surfaces accessible gates, restrooms,
  and services by default, and the chat UI itself is built to WCAG-friendly
  standards (see [Accessibility](#accessibility) below).
- **Multilingual assistance** — the underlying LLM is instructed to always
  respond in the same language the fan used, so no language-switching UI is
  needed — it's automatic and works for any language the model supports.

## How It Works

```
Fan question → Flask API → Retrieval layer (stadium_data.json)
             → Gemini LLM (grounded on retrieved context)
             → Natural-language answer
```

The retrieval layer is intentionally simple: a keyword-matching lookup over a
structured JSON dataset of gates, restrooms, transport options, and
accessibility services. This keeps the whole system inspectable, fast, and
fully testable offline — no vector database required for a prototype at this
scale. It's designed so a real venue's live data (occupancy sensors, transit
APIs, etc.) could be swapped in without changing the app's architecture.

The GenAI layer never invents facts about the venue — it's instructed to
answer only from the retrieved context, and to say so plainly when it
doesn't know something.

## Project Structure

```
stadium-genai-assistant/
├── backend/
│   ├── app.py                  # Flask API: /chat, /health
│   ├── data/stadium_data.json  # Mock venue dataset (gates, restrooms, transport, FAQs)
│   ├── services/
│   │   ├── rag.py              # Keyword retrieval over the dataset
│   │   └── genai_client.py     # Gemini API wrapper + offline fallback
│   ├── tests/test_app.py       # Pytest suite (10 tests)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/App.jsx             # Chat UI
    ├── src/App.css
    └── .env.example
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then add your real GEMINI_API_KEY
python app.py                   # runs on http://localhost:5000
```

**Note:** if `GEMINI_API_KEY` is left unset, the app still runs fully —
it falls back to a deterministic offline response mode. This is intentional,
so the app (and its tests) can be evaluated without requiring a live API key.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # points to your backend URL
npm run dev                     # runs on http://localhost:5173
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

## Accessibility

- Semantic HTML with ARIA labels (`role="log"`, `aria-live="polite"` on the
  chat feed so screen readers announce new messages)
- Full keyboard navigation with visible focus states
- `prefers-reduced-motion` respected
- High-contrast dark theme with WCAG-AA-compliant text contrast
- The assistant itself surfaces accessible-entrance and accessible-restroom
  info by default when asked about gates or facilities

## Security

- No API keys hardcoded — read only from environment variables via `.env`
  (which is git-ignored)
- Input validation on every request (empty/oversized messages rejected)
- Per-IP rate limiting on the `/chat` endpoint to prevent abuse
- Provider failures degrade gracefully (502 with a friendly message) instead
  of leaking stack traces

## Known Limitations & Next Steps

- Retrieval is keyword-based, not semantic — a real deployment would swap
  in embeddings (e.g. a small vector store) for more accurate matches on
  paraphrased questions.
- The dataset is mock data for one demo venue — a production version would
  connect to live occupancy sensors, ticketing systems, and transit APIs.
- Rate limiting is in-memory (per-process) — would move to Redis for a
  multi-instance deployment.
- Next module planned: crowd-density alerts for organizers, using the same
  retrieval + LLM pattern established here.

## Tech Stack

React (Vite) · Flask · Google Gemini API · Pytest
