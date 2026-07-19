import os
import time
from collections import defaultdict, deque

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from services import rag
from services.genai_client import generate_response, GenAIError

load_dotenv()

app = Flask(__name__)
CORS(app)

MAX_MESSAGE_LENGTH = 500
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20

# In-memory rate limiter keyed by client IP. Simple and dependency-free -
# fine for a hackathon prototype; swap for Redis in production.
_request_log = defaultdict(deque)


def _is_rate_limited(client_id: str) -> bool:
    now = time.time()
    window = _request_log[client_id]
    while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    window.append(now)
    return False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "venue": rag.venue_name()}), 200


@app.route("/chat", methods=["POST"])
def chat():
    client_id = request.remote_addr or "unknown"
    if _is_rate_limited(client_id):
        return jsonify({"error": "Too many requests. Please slow down."}), 429

    body = request.get_json(silent=True)
    if not body or "message" not in body:
        return jsonify({"error": "Request body must include a 'message' field."}), 400

    message = str(body.get("message", "")).strip()
    language_hint = str(body.get("language", "")).strip()[:20]

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message too long. Keep it under {MAX_MESSAGE_LENGTH} characters."
        }), 400

    context = rag.retrieve_context(message)

    try:
        reply = generate_response(message, context, language_hint)
    except GenAIError:
        return jsonify({
            "error": "The assistant is temporarily unavailable. Please try again shortly."
        }), 502

    return jsonify({
        "reply": reply,
        "venue": rag.venue_name(),
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
