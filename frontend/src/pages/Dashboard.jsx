import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { listDocuments, uploadDocument, deleteDocument } from "../api";
import Sidebar from "../components/Sidebar";

export default function Dashboard() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef();

  const fetchDocs = async () => {
    try {
      const res = await listDocuments();
      setDocuments(res.data.documents ?? []);
    } catch {
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    setError("");

    try {
      await uploadDocument(formData);
      await fetchDocs();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this document?")) return;
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setError("Failed to delete document.");
    }
  };

  const statusBadge = (status) => {
    const map = {
      ready:      { label: "Ready",      cls: "badge-ready"      },
      processing: { label: "Processing", cls: "badge-processing" },
      error:      { label: "Error",      cls: "badge-error"      },
    };
    const s = map[status] ?? { label: status, cls: "" };
    return <span className={`badge ${s.cls}`}>{s.label}</span>;
  };

  const formatSize = (bytes) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (iso) =>
    iso
      ? new Date(iso).toLocaleDateString("en-IN", {
          day: "numeric", month: "short", year: "numeric",
        })
      : "—";

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h2>Documents</h2>
            <p className="page-subtitle">
              {documents.length} document{documents.length !== 1 ? "s" : ""} uploaded
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              style={{ display: "none" }}
              onChange={handleUpload}
            />
            <button
              className="btn-upload"
              onClick={() => fileInputRef.current.click()}
              disabled={uploading}
            >
              {uploading ? "Uploading…" : "+ Upload Document"}
            </button>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="empty-state">
            <div className="spinner" />
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">📄</p>
            <p className="empty-title">No documents yet</p>
            <p className="empty-sub">Upload a PDF, Word doc, or text file to get started.</p>
          </div>
        ) : (
          <div className="doc-grid">
            {documents.map((doc) => (
              <div key={doc.id} className="doc-card">
                <div className="doc-card-top">
                  <span className="doc-file-icon">📄</span>
                  {statusBadge(doc.status)}
                </div>
                <p className="doc-name" title={doc.original_name}>
                  {doc.original_name}
                </p>
                <p className="doc-meta">
                  {formatSize(doc.file_size)} · {formatDate(doc.created_at)}
                </p>
                <div className="doc-actions">
                  <button
                    className="btn-ask"
                    disabled={doc.status !== "ready"}
                    onClick={() => navigate(`/query?doc=${doc.id}`)}
                  >
                    Ask
                  </button>
                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(doc.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
