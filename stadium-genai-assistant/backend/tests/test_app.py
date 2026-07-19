import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app as flask_app
from services import rag


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


# --- Health endpoint ---

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "venue" in data


# --- Input validation on /chat ---

def test_chat_missing_message_returns_400(client):
    resp = client.post("/chat", json={})
    assert resp.status_code == 400


def test_chat_empty_message_returns_400(client):
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_chat_message_too_long_returns_400(client):
    resp = client.post("/chat", json={"message": "a" * 501})
    assert resp.status_code == 400


def test_chat_valid_message_returns_200(client):
    resp = client.post("/chat", json={"message": "Where is Gate A?"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_chat_rejects_non_json_body(client):
    resp = client.post("/chat", data="not json", content_type="text/plain")
    assert resp.status_code == 400


# --- Rate limiting ---

def test_chat_rate_limit_blocks_excessive_requests(client):
    for _ in range(20):
        client.post("/chat", json={"message": "test"})
    resp = client.post("/chat", json={"message": "one too many"})
    assert resp.status_code == 429


# --- Retrieval / RAG logic ---

def test_retrieve_context_returns_relevant_gate_info():
    context = rag.retrieve_context("accessible gate wheelchair")
    assert "accessible" in context.lower() or "gate" in context.lower()


def test_retrieve_context_never_empty():
    context = rag.retrieve_context("completely unrelated gibberish query xyz123")
    assert len(context.strip()) > 0


def test_venue_name_is_set():
    assert isinstance(rag.venue_name(), str)
    assert len(rag.venue_name()) > 0
