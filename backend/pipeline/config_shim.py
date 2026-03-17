"""
Shim so pipeline files (ingest.py, vector_store.py, query.py, embeddings.py)
can continue doing `from config import X` without changes.
Place this file as pipeline/config.py — Python will find it first when
the pipeline modules do their imports.
"""
import sys
import os

# Make sure backend/ is on the path so we can import the real config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import get_settings

_s = get_settings()

# ── Values your pipeline files expect ─────────────────────────────────────────
GROQ_API_KEY    = _s.groq_api_key
GROQ_MODEL      = "llama3-8b-8192"          # Groq model used in query.py
INDEX_PATH      = _s.faiss_index_path       # base path, routers will pass per-user sub-paths
DOCUMENTS_PATH  = _s.upload_dir
CHUNK_SIZE      = 1000
CHUNK_OVERLAP   = 200