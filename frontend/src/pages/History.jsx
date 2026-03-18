import { useState, useEffect } from "react";
import { getHistory, deleteHistoryItem, clearHistory } from "../api";
import Sidebar from "../components/Sidebar";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchHistory = async () => {
    try {
      const res = await getHistory(50);
      setHistory(res.data.history ?? []);
    } catch {
      setError("Failed to load history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleDelete = async (id) => {
    try {
      await deleteHistoryItem(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
    } catch {
      setError("Failed to delete item.");
    }
  };

  const handleClear = async () => {
    if (!confirm("Clear all history? This cannot be undone.")) return;
    try {
      await clearHistory();
      setHistory([]);
    } catch {
      setError("Failed to clear history.");
    }
  };

  const formatDate = (iso) =>
    new Date(iso).toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    });

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h2>Query History</h2>
            <p className="page-subtitle">
              {history.length} quer{history.length !== 1 ? "ies" : "y"}
            </p>
          </div>
          {history.length > 0 && (
            <button className="btn-danger" onClick={handleClear}>
              Clear All
            </button>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">🕓</p>
            <p className="empty-title">No history yet</p>
            <p className="empty-sub">Your query history will appear here.</p>
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => (
              <div key={item.id} className="history-card">
                <div className="history-card-header">
                  <span className="history-date">{formatDate(item.created_at)}</span>
                  <button
                    className="btn-icon"
                    onClick={() => handleDelete(item.id)}
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
                <p className="history-question">{item.question}</p>
                <p className="history-answer">{item.answer}</p>
                {item.sources?.length > 0 && (
                  <div className="sources">
                    <div className="sources-list">
                      {item.sources.map((s, i) => (
                        <span key={i} className="source-tag">
                          {s.file} · chunk {s.chunk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
