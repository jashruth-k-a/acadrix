# Acadrix

> AI in Education (EdTech) focused on syllabus-bound, hallucination free answers with adaptive study modes.

Acadrix is a RAG-powered academic assistant that lets students upload their study materials and ask questions getting precise, document-grounded answers with zero hallucination. Built for students who want to study smarter, not harder.

---

## Features

- **Document-Grounded Answers** — Responses are strictly sourced from uploaded materials. If it's not in your documents, Acadrix won't make it up.
- **Adaptive Study Modes** — Switch between Direct Answer mode for quick answers and Socratic mode for guided learning through questions.
- **Multi-Document Support** — Upload multiple documents and query across all of them simultaneously.
- **Query History** — Every question and answer is saved and accessible for review.
- **JWT Authentication** — Secure user accounts with token-based authentication.
- **Source Citations** — Every answer includes the source file and chunk it was derived from.

---

## Tech Stack

**Frontend**
- React + Vite
- React Router
- Axios
- React Markdown

**Backend**
- FastAPI
- MongoDB (Atlas)
- FAISS — vector similarity search
- Sentence Transformers — document embeddings
- Groq (LLaMA 3.3 70B) — LLM inference
- JWT — authentication
- PyMuPDF / pypdfium2 — PDF parsing

---

## Project Structure

```
acadrix/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── query.py
│   │   └── history.py
│   └── pipeline/
│       ├── ingest.py
│       ├── query.py
│       └── vector_store.py
└── frontend/
    └── src/
        ├── api.js
        ├── App.jsx
        ├── index.css
        ├── components/
        │   ├── Sidebar.jsx
        │   └── ProtectedRoute.jsx
        ├── context/
        │   └── AuthContext.jsx
        └── pages/
            ├── Login.jsx
            ├── Register.jsx
            ├── Dashboard.jsx
            ├── Query.jsx
            └── History.jsx
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB Atlas account
- Groq API key

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder (see `.env.example`):

```bash
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000`
API docs at `http://127.0.0.1:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend/` folder:
```
VITE_API_URL=http://127.0.0.1:8000
```

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `DATABASE_NAME` | Database name (e.g. `acadrix`) |
| `JWT_SECRET_KEY` | Secret key for JWT token signing |
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `UPLOAD_DIR` | Directory for uploaded files (e.g. `uploads`) |
| `FAISS_INDEX_PATH` | Directory for FAISS indexes (e.g. `faiss_index`) |
| `DEBUG` | `true` for development, `false` for production |

### Frontend — `frontend/.env`

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend API URL |

---

## Deployment

- **Backend** — [Render](https://render.com) — Root directory: `backend`
- **Frontend** — [Vercel](https://vercel.com) — Root directory: `frontend`

---

## How It Works

1. User uploads a PDF or document
2. Backend parses and chunks the document
3. Chunks are embedded using Sentence Transformers and stored in a FAISS index
4. User asks a question
5. FAISS retrieves the most relevant chunks via similarity search
6. Chunks + question are sent to LLaMA 3.3 70B via Groq
7. LLM generates a grounded answer strictly from the retrieved context
8. Answer + source citations are returned to the user

---

## License

MIT

---

Built by [Jashruth K A](https://github.com/jashruth-k-a)
