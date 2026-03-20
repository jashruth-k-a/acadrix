from groq import Groq
from config import get_settings
import faiss
import numpy as np

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

GROQ_MODEL = "llama-3.3-70b-versatile"

DIRECT_PROMPT = """You are Acadrix, a friendly and warm academic assistant — like a smart friend who happens to know everything about the topic.
Answer the student's question STRICTLY from the context provided below.

Rules you must NEVER break:
1. Answer ONLY from the context. Do not use outside knowledge.
2. READ ALL context chunks before answering. Synthesize a COMPLETE answer
   by combining information from every relevant chunk. Never say information
   is missing if it exists anywhere across the chunks.
3. NEVER explain your reasoning process or mention chunk numbers in your answer.
   Just give the answer directly and confidently as if you already knew it.
4. If the answer is genuinely not in ANY of the chunks, respond with ONLY:
   "This topic isn't covered in your uploaded materials."
   Do NOT add a Source line when refusing.
5. If the question is too vague or a follow-up without context (e.g. single
   words, pronouns with no prior context), respond with ONLY:
   "Could you clarify your question? It seems incomplete."
   Do NOT add a Source line for this either.
6. If you do answer, end with a citation line:
   Source: [file name, chunk number]
7. Format your answer clearly:
   - Use bullet points for lists
   - Use short paragraphs, not walls of text
   - Bold key terms using **term**
   - Keep tone friendly and conversational
8. Tone rules:
   - Write like you're explaining to a friend, not writing a textbook
   - Use simple, natural language
   - It's okay to say things like "basically", "think of it this way", "in simple terms"
   - Never sound robotic or overly formal

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


def search_with_index(question: str, index, chunks: list, top_k: int = 5):
    """Search a FAISS index directly using index and chunks objects."""
    from pipeline.vector_store import get_embeddings

    question_embedding = get_embeddings([question])
    distances, indices = index.search(
        np.array(question_embedding, dtype=np.float32), top_k
    )

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(chunks):
            chunk = chunks[idx].copy()
            chunk["score"] = float(distances[0][i])
            results.append(chunk)

    return results


def ask_acadrix(question: str, index=None, chunks: list = None,
                mode: str = "direct", top_k: int = 5):
    """
    Query the RAG pipeline.
    Pass index and chunks directly (loaded from GridFS).
    """
    if index is None or chunks is None:
        return {
            "answer": "No documents have been indexed yet. Please upload your study materials first.",
            "sources": []
        }

    relevant_chunks = search_with_index(question, index, chunks, top_k=top_k)

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
    is_refusal = (
        "isn't covered" in answer.lower()
        or "not covered" in answer.lower()
        or "could you clarify" in answer.lower()
    )

    if is_refusal:
        answer = answer.split("Source:")[0].strip()

    sources = [] if is_refusal or mode == "socratic" else [
        {"file": c["file_name"], "chunk": c["chunk_index"]}
        for c in relevant_chunks
    ]

    return {"answer": answer, "sources": sources}