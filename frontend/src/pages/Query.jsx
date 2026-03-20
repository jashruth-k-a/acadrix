import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { queryDocuments, listDocuments } from "../api";
import Sidebar from "../components/Sidebar";
import ReactMarkdown from "react-markdown";

const STORAGE_KEY = "acadrix_chat_messages";

export default function Query() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [question, setQuestion] = useState("");
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(searchParams.get("doc") || "");
  const [mode, setMode] = useState("direct");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef();
  const inputRef = useRef();

  useEffect(() => {
    listDocuments()
      .then((res) =>
        setDocuments((res.data.documents ?? []).filter((d) => d.status === "ready"))
      )
      .catch(() => {});
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAsk = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || loading) return;

    const newMessage = { role: "user", content: q };
    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);
    setQuestion("");
    setLoading(true);

    // Build history for context (last 6 messages max)
    const history = updatedMessages.slice(-6).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await queryDocuments({
        question: q,
        document_id: selectedDoc || null,
        mode,
        top_k: 5,
        history,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.answer, sources: res.data.sources ?? [] },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again.", sources: [] },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="chat-layout">
        {/* Controls bar */}
        <div className="query-controls-bar">
          <div className="field">
            <label>Document</label>
            <select value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)}>
              <option value="">All documents</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.original_name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Mode</label>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="direct">Direct Answer</option>
              <option value="socratic">Socratic</option>
            </select>
          </div>
          {messages.length > 0 && (
            <button className="btn-danger" onClick={handleClearChat}>
              Clear Chat
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p className="empty-icon">💬</p>
              <p className="empty-title">
                {mode === "socratic" ? "Socratic Mode" : "Ask anything"}
              </p>
              <p className="empty-sub">
                {mode === "socratic"
                  ? "Instead of giving you the Direct Answer, I'll guide you with Questions to help you think it through and arrive at the Answer!"
                  : "Questions are answered from your uploaded documents."}
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-bubble">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
                {msg.sources?.length > 0 && (
                  <div className="sources">
                    <p className="sources-label">Sources</p>
                    <div className="sources-list">
                      {msg.sources.map((s, j) => (
                        <span key={j} className="source-tag">
                          {s.file} · chunk {s.chunk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-bubble typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form className="chat-input-bar" onSubmit={handleAsk}>
          <input
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents…"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "…" : "Ask"}
          </button>
        </form>
      </main>
    </div>
  );
}