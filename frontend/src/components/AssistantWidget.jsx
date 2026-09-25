import { useState } from "react";
import { api } from "../services/api";

const starterQuestions = [
  "How do I submit a problem?",
  "How does government verification work?",
  "How can a university receive a notification?",
];

export default function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi. I can help you use the Challenge to Impact application." },
  ]);
  const [busy, setBusy] = useState(false);

  async function ask(text = message) {
    const question = text.trim();
    if (!question || busy) return;
    setMessage("");
    setMessages((current) => [...current, { role: "user", text: question }]);
    setBusy(true);
    try {
      const result = await api("/api/assistant/chat", { method: "POST", body: { message: question } });
      setMessages((current) => [...current, { role: "assistant", text: result.answer }]);
    } catch (error) {
      setMessages((current) => [...current, { role: "assistant", text: error.message || "The assistant is temporarily unavailable." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="assistant-widget">
      {open && (
        <section className="assistant-panel" aria-label="Challenge to Impact assistant">
          <header className="assistant-header">
            <div><span className="assistant-orb">AI</span><div><strong>Impact assistant</strong><small>Application help only</small></div></div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close assistant">×</button>
          </header>
          <div className="assistant-messages" aria-live="polite">
            {messages.map((item, index) => <div className={`assistant-message ${item.role}`} key={`${item.role}-${index}`}>{item.text}</div>)}
            {busy && <div className="assistant-message assistant typing"><span /><span /><span /></div>}
          </div>
          {messages.length === 1 && <div className="assistant-starters">{starterQuestions.map((question) => <button type="button" key={question} onClick={() => ask(question)}>{question}</button>)}</div>}
          <form className="assistant-form" onSubmit={(event) => { event.preventDefault(); ask(); }}><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask about this application" aria-label="Ask the application assistant" /><button type="submit" disabled={busy || !message.trim()} aria-label="Send question">→</button></form>
          <p className="assistant-disclaimer">AI decision-support only. Do not share passwords or API keys.</p>
        </section>
      )}
      <button type="button" className={`assistant-launcher ${open ? "is-open" : ""}`} onClick={() => setOpen((value) => !value)} aria-expanded={open}><span className="assistant-launcher-icon">✦</span><span>Ask AI</span></button>
    </div>
  );
}
