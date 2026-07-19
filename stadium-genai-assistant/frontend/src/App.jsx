import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

const SUGGESTED_QUESTIONS = [
  "Is Gate C wheelchair accessible?",
  "Where's the nearest restroom to Gate B?",
  "How do I get home after the match?",
  "What time do gates open?",
];

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "Hi! I'm your stadium assistant for the FIFA World Cup 2026. " +
        "Ask me about gates, accessibility, restrooms, or transport — " +
        "in any language.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError("");
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong. Please try again.");
      } else {
        setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
      }
    } catch (err) {
      setError("Couldn't reach the assistant. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    sendMessage(input);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Stadium Assistant</h1>
        <p className="subtitle">FIFA World Cup 2026 · GenAI Fan Support</p>
      </header>

      <main
        className="chat-window"
        role="log"
        aria-live="polite"
        aria-label="Conversation with stadium assistant"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.role === "user" ? "message-user" : "message-assistant"}`}
          >
            <span className="message-role" aria-hidden="true">
              {msg.role === "user" ? "You" : "Assistant"}
            </span>
            <p>{msg.text}</p>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant" aria-live="polite">
            <span className="message-role" aria-hidden="true">Assistant</span>
            <p className="typing-indicator">Thinking…</p>
          </div>
        )}

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      <div className="suggestions" aria-label="Suggested questions">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            className="suggestion-chip"
            onClick={() => sendMessage(q)}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>

      <form className="input-bar" onSubmit={handleSubmit}>
        <label htmlFor="chat-input" className="visually-hidden">
          Type your question to the stadium assistant
        </label>
        <input
          id="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about gates, accessibility, transport…"
          disabled={loading}
          maxLength={500}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
