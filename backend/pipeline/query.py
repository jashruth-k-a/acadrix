from groq import Groq
from pipeline.vector_store import search_index, search_multiple_indexes
from config import get_settings

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

GROQ_MODEL = "llama3-8b-8192"

DIRECT_PROMPT = """You are Acadrix, a document-grounded academic assistant.
Answer the student's question STRICTLY from the context provided below.

Rules you must NEVER break:
1. Answer ONLY from the context. Do not use outside knowledge.
2. If the answer is not in the context, respond with ONLY this exact sentence and nothing else:
   "This topic isn't covered in your uploaded materials."
   Do NOT add a Source line when refusing.
3. If you do answer, end with a citation line:
   Source: [file name, chunk number]
4. Keep answers clear and student-friendly.

Context:
{context}

Question: {question}

Answer:"""

SOCRATIC_PROMPT = """You are Acadrix in Socratic mode — a Socratic academic tutor.
Instead of giving the answer directly, guide the student to discover it themselves
using ONLY the context provided below.

Rules you must NEVER break:
1. Do NOT give the answer directly.
2. Ask 1-2 guiding questions that lead the student toward the answer.
3. Base your guiding questions ONLY on the context below.
4. If the topic isn't in the context, say ONLY:
   "This topic isn't covered in your uploaded materials."

Context:
{context}

Student's question: {question}

Your guiding questions:"""


def ask_acadrix(question: str, index_path: str = None, index_paths: list = None,
                mode: str = "direct", top_k: int = 5):
    """
    Query the RAG pipeline.
    - Pass index_path for a single document query.
    - Pass index_paths (list) to query across multiple documents.
    """
    if index_paths:
        relevant_chunks = search_multiple_indexes(question, index_paths, top_k=top_k)
    elif index_path:
        relevant_chunks = search_index(question, index_path, top_k=top_k)
    else:
        return {
            "answer": "No documents have been indexed yet. Please upload your study materials first.",
            "sources": []
        }

    if not relevant_chunks:
        return {
            "answer": "No documents have been indexed yet. Please upload your study materials first.",
            "sources": []
        }

    context_parts = []
    for chunk in relevant_chunks:
        context_parts.append(
            f"[{chunk['file_name']} — chunk {chunk['chunk_index']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    if mode == "socratic":
        prompt = SOCRATIC_PROMPT.format(context=context, question=question)
    else:
        prompt = DIRECT_PROMPT.format(context=context, question=question)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024
    )

    answer = response.choices[0].message.content
    is_refusal = "isn't covered" in answer.lower() or "not covered" in answer.lower()

    sources = [] if is_refusal else [
        {"file": c["file_name"], "chunk": c["chunk_index"]}
        for c in relevant_chunks
    ]

    return {"answer": answer, "sources": sources}