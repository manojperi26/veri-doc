<div align="center"> VeriDoc AI

An Adaptive Multi-Document RAG System for Grounded Question Answering
</div>

VeriDoc is a production-grade Retrieval-Augmented Generation (RAG) assistant that answers questions strictly from user-uploaded documents, with page-and-file level citations. It combines dense + sparse hybrid retrieval, an adaptive query router, contextual compression, and conversation memory into a modular pipeline built from independent, swappable components.

📹 Demo
[▶ Watch the demo video](https://claude.ai/chat/ADD_YOUR_GOOGLE_DRIVE_LINK_HERE)

✨ Features
* **Multi-format ingestion** — PDF, DOCX, PPTX, and TXT files in a single session
* **Grounded answers only** — responds strictly from uploaded documents, never general knowledge, with explicit fallback when the answer isn't found
* **Adaptive RAG Decision Layer** — an LLM-based router is available to classify queries and set retrieval depth (currently bypassed in the active chat flow to use a standard depth of 8 for robust results)
* **Hybrid retrieval** — dense vector search (in-memory NumPy-based) fused with sparse keyword search (BM25)
* **Cross-encoder reranking** — candidate pool reranked before compression using a Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
* **Contextual compression** — retains the top 5 reranked chunks directly to preserve complete evidence and prevent critical information loss
* **Conversation memory + query rewriting** — stores conversation history and supports rewriting follow-up questions (rewriter currently bypassed in main flow to prevent query meaning distortion)
* **Structured document summarization** — auto-generates summaries per document based on the first chunk of the text
* **Suggested questions** — auto-generates 5 leveled questions per document
* **OCR fallback** — automatically OCRs PDF pages with insufficient extractable text (less than 50 characters)
* **Session reset** — full wipe of vectors, BM25 index, chunks, memory, and cached summaries on demand

🏗️ Architecture
```
Documents (PDF/DOCX/PPTX/TXT)
│
Document Loaders + OCR fallback
│
Text Cleaner
│
Chunker (paragraph-based, 1000 size / 150 overlap)
│
Embedder (all-MiniLM-L6-v2) ──► Dense Index (In-Memory Vector Store)
│
Tokenizer ──► Sparse Index (BM25)
│
┌────────────────────────┐
│  User Query             │
└────────────────────────┘
│
Adaptive Router (modular, default: bypassed to top_k=8)
│
Query Rewriter (modular, default: bypassed to query)
│
Hybrid Retriever (dense + BM25, weighted fusion)
│
Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2, top-8)
│
Contextual Compressor (top-5 chunks)
│
Answer Generator (Groq llama-3.3-70b-versatile / Hugging Face fallback) ──► Answer + Citations
│
Conversation Memory (trimmed to last 6 messages)
```

🔩 Components
| # | Component | What it does |
|---|---|---|
| 1 | **Document Loaders** | Parses PDF/DOCX/PPTX/TXT into page/slide-level text; PDFs extracted via `pypdf`, low-text pages (< 50 chars) retried through OCR (`pytesseract` + `pdf2image`, 200 DPI). DOCX and PPTX parsed via `python-docx` and `python-pptx` respectively. |
| 2 | **Text Cleaner** | Unicode normalization (NFKC), line-ending standardization (`\n`), removes redundant spaces, and collapses more than 2 consecutive newlines (keeping up to `\n\n`). |
| 3 | **Document Sample Extractor** | Extracts the text of the first chunk of the document (up to 4000 characters for questions, 6000 for summaries) to feed the Summarizer and Suggested Question Generator. |
| 4 | **Chunker** | Dependency-free, paragraph-based: splits text by `\n\n+` and groups them into chunks up to 1000 characters with an overlap of 150 characters, snapping to word boundaries. |
| 5 | **Embedder** | Generates embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384-dim), L2-normalizes embeddings. |
| 6 | **Dense Index** | In-Memory Vector Store (NumPy-based, cosine similarity on L2-normalized vectors); scoped per session, wiped and rebuilt on reset. |
| 7 | **Sparse Index** | In-memory BM25Okapi (`rank_bm25`); tokenizes text (lowercased, punctuation removed) and builds index, rebuilt after every ingest. |
| 8 | **Hybrid Retriever** | Fuses dense vector store search with sparse BM25 retrieval. Normalizes scores in each result set using min-max scaling, then combines them into a weighted score (60% Dense + 40% BM25). Returns the top-k (15) candidates. |
| 9 | **Adaptive Router** | Classifies each query into 7 types (Simple, Complex, Comparison, Summarization, Reasoning, Multi-document, Follow-up) via LLM to set depth, but currently bypassed in the active chat flow (which uses a default retrieval depth of 8). |
| 10 | **Query Rewriter** | Rewrites context-dependent follow-up questions using the last 6 messages of conversation history, but currently bypassed in the active chat flow. |
| 11 | **Cross-Encoder Reranker** | Reorders top 15 hybrid results using `cross-encoder/ms-marco-MiniLM-L-6-v2`, keeping the top 8. |
| 12 | **Contextual Compressor** | Returns the top 5 reranked chunks directly to preserve context, avoiding secondary LLM rewrites that could lose evidence. |
| 13 | **Answer Generator** | Groq `llama-3.3-70b-versatile` (primary, temperature 0.1) or Hugging Face Inference API fallback. Returns JSON containing classification (`answer`, `not_in_document`, `out_of_scope`), answer string, and source IDs. Answers strictly from retrieved context with explicit fallback: `"I could not find that information in the uploaded documents."` (with extractive string matching backup on failure). |
| 14 | **Conversation Memory** | Maintains a list of conversation messages trimmed to the last 6 messages. |
| 15 | **Document Summarizer** | Generates summary from the first chunk of the document using LLM, returning a JSON object with keys: `"Executive Summary"`, `"Key Topics"`, `"Important Facts"`, `"Key Numbers"`, `"Conclusion"`. |
| 16 | **Suggested Question Generator** | Generates exactly 5 questions (Basic, Intermediate, Advanced, Comparison, Analytical) from the first chunk of the document as a JSON array of strings. |
| 17 | **Session Manager** | API routes (`routes.py`) and orchestrator functions in `rag_service.py` (`process_document`, `chat`, `reset_session`, `clear_chat`) coordinate the ingestion, retrieval, reranking, answering, and state management per session. |

🛠️ Tech Stack
| Component | Technology |
|---|---|
| **LLM** | Groq — llama-3.3-70b-versatile (primary), Hugging Face InferenceClient (fallback) |
| **Dense retrieval** | In-memory NumPy-based vector store |
| **Sparse retrieval** | BM25Okapi (rank_bm25) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| **Reranker** | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| **Document parsing** | pypdf, python-docx, python-pptx |
| **OCR** | pytesseract, pdf2image, Poppler, Tesseract |
| **Web framework** | FastAPI, uvicorn |
| **Config/env** | python-dotenv, pydantic-settings |

⚙️ Configuration
| Parameter | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | 1000 | Characters per chunk |
| `CHUNK_OVERLAP` | 150 | Overlap between chunks |
| `DENSE_WEIGHT` | 0.6 | Weight for Pinecone score in fusion |
| `BM25_WEIGHT` | 0.4 | Weight for BM25 score in fusion |
| `RERANK_CANDIDATE_POOL` | 15 | Chunks fed to reranker |
| `RERANK_TOP_N` | 8 | Chunks kept after reranking |
| `COMPRESSION_TOP_N` | 5 | Chunks passed through compression |
| `MEMORY_WINDOW` | 6 | Past conversation messages retained (user + assistant) |
| `ENABLE_OCR_FALLBACK` | True | OCR pages with low extractable text |
| `OCR_MIN_CHARS_PER_PAGE`| 50 | Threshold to trigger OCR |
| `OCR_DPI` | 200 | Rendering resolution for OCR |

> [!NOTE]
> Router and query rewriter parameters are defined in their respective modules but bypassed in the default chat execution path to maintain raw query context.

🚀 Quickstart
```bash
# 1. Clone the repo
git clone https://github.com/manojperi26/veri-doc.git
cd veri-doc

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create a .env file with:
# GROQ_API_KEY=your_key_here
# HUGGINGFACE_API_KEY=your_key_here (Optional fallback)

# 5. (Optional) Install OCR binaries for scanned PDF support
# Ubuntu: sudo apt install tesseract-ocr poppler-utils
# macOS: brew install tesseract poppler
```

Usage
You can import the module functions directly in Python:
```python
# Import the service functions and configuration
from services import rag_service
from config import settings

# Configure API keys (or load via python-dotenv)
settings.update(groq_key="your_groq_api_key")

# Upload and process a document
with open("your_file.pdf", "rb") as f:
    file_bytes = f.read()
    rag_service.process_document(file_bytes, "your_file.pdf", "pdf", session_id="my_session")

# Ask questions
result = rag_service.chat("your question", session_id="my_session")
print("Answer:", result["answer"])
print("Citations:", result["citations"])

# Reset the session (clears documents, vector store, BM25 store, memory)
rag_service.reset_session(session_id="my_session")
```

Output format:
```json
{
  "answer": "Plain-prose response grounded only in retrieved context",
  "citations": [
    {
      "source_file": "report.pdf",
      "page": 4,
      "chunk_id": "doc_id_4_0"
    }
  ]
}
```
If the answer isn't in the documents:
`"I could not find that information in the uploaded documents."`

📦 Deployment Status
* **✅ Local Deployment** — Fully functional and tested locally. The complete pipeline — multi-format ingestion with OCR fallback, hybrid retrieval, adaptive routing, reranking, compression, Groq answer generation, and session management — runs end-to-end.
* **⏸️ Cloud Deployment** — No permanent public deployment is maintained, due to the storage/compute footprint of the full stack (sentence-transformer embeddings, cross-encoder reranker, OCR binaries, local vector search). This is a hosting/resource constraint, not a limitation of the application — the system has been fully implemented and tested locally. A paid instance or dedicated ML hosting environment would be required for a permanent live demo.

📝 Notes
* Each component (loader, chunker, retriever, router, rewriter, reranker, compressor, memory) is independent and swappable without touching the others
* Dependency-light by design — chunking, dense retrieval, and document loading are custom implementations rather than heavy framework abstractions (no LangChain)
* Every LLM call expecting structured output (router, compression, summarization, suggested questions) strips markdown code fences before JSON parsing and has an explicit fallback path on failure

<div align="center">
Built by [Manoj](https://github.com/manojperi26) · [LinkedIn](https://linkedin.com/in/manojperi26)
</div>
