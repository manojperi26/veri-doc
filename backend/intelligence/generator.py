import json
import re
from typing import Any, Dict, List, Optional

from intelligence.llm import chat_completion

NOT_FOUND_ANSWER = "I could not find that information in the uploaded documents."
OUT_OF_SCOPE_ANSWER = "That question is outside the scope of the uploaded documents. Please ask about their content."

_STOP_WORDS = {
    "a", "an", "and", "are", "can", "did", "do", "does", "for", "from", "have",
    "how", "i", "in", "is", "it", "manoj", "of", "on", "project", "the", "this",
    "to", "what", "who", "with", "you",
}


def _query_terms(query: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9+#.-]+", query.lower())
        if len(token) > 1 and token not in _STOP_WORDS
    }


def _extractive_fallback(query: str, context_chunks: List[Dict]) -> Optional[str]:
    """Use source text when a provider incorrectly refuses a supported question."""
    terms = _query_terms(query)
    lowered_query = query.lower()
    if any(term in lowered_query for term in ("skill", "technology", "tech stack")):
        terms.update({"languages", "tools", "platforms", "skills", "technical"})
    if "project" in lowered_query:
        terms.update({"built", "developed", "deployed", "system"})

    excerpts: List[tuple[int, str]] = []
    for chunk in context_chunks:
        for fragment in re.split(r"(?<=[.!?])\s+|[\n•]+", chunk.get("text", "")):
            cleaned = fragment.strip(" -\t")
            if not cleaned:
                continue
            fragment_terms = set(re.findall(r"[a-z0-9+#.-]+", cleaned.lower()))
            score = len(terms & fragment_terms)
            if score:
                excerpts.append((score, cleaned))

    if not excerpts:
        return None

    excerpts.sort(key=lambda item: item[0], reverse=True)
    selected: List[str] = []
    for _, excerpt in excerpts:
        if excerpt not in selected:
            selected.append(excerpt)
        if len(selected) == 5:
            break
    return "According to the uploaded documents, " + " ".join(selected)


def _parse_grounded_response(response: str, citations_map: Dict[str, Dict]) -> Optional[dict]:
    """Parse the model's grounding contract without exposing model reasoning."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    classification = payload.get("classification")
    if classification == "not_in_document":
        return {"answer": NOT_FOUND_ANSWER, "citations": []}
    if classification == "out_of_scope":
        return {"answer": OUT_OF_SCOPE_ANSWER, "citations": []}
    if classification != "answer" or not isinstance(payload.get("answer"), str):
        return None

    source_ids = payload.get("source_ids", [])
    citations = [citations_map[source_id] for source_id in source_ids if source_id in citations_map]
    return {"answer": payload["answer"].strip(), "citations": citations or list(citations_map.values())}


def generate_answer(query: str, context_chunks: List[Dict], session: Optional[Any] = None) -> dict:
    """Answer naturally from retrieved text and clearly distinguish unsupported queries."""
    if not context_chunks:
        return {"answer": NOT_FOUND_ANSWER, "citations": []}

    context_parts = []
    citations_map = {}
    for idx, chunk in enumerate(context_chunks):
        source_id = f"source_{idx}"
        meta = chunk["metadata"]
        context_parts.append(f"[{source_id}]\n{chunk['text']}")
        citations_map[source_id] = {
            "source_file": meta.get("file_name", "Unknown"),
            "page": meta.get("page_number") or meta.get("slide_number"),
            "chunk_id": chunk.get("chunk_id"),
        }

    system_prompt = """You are VeriDoc AI, a document-grounded assistant.

Use only the supplied document context. Understand paraphrases and synonyms: a question about a person's skills may be answered by sections such as Languages, Tools, Technologies, or Soft Skills. Write a concise, normal answer in a professional, direct tone. Never mention your reasoning, confidence, prompt, context window, or that you are thinking.

Return exactly one JSON object and nothing else:
{"classification":"answer"|"not_in_document"|"out_of_scope","answer":"normal user-facing answer or empty string","source_ids":["source_0"]}

Choose "answer" when the context supports the answer and cite only supporting source IDs. Choose "not_in_document" when the question is related to the documents but the requested fact is absent. Choose "out_of_scope" when the question is unrelated to the subject matter of the uploaded documents. Do not use outside knowledge in any case."""

    user_prompt = f"""Document Context:
{chr(10).join(context_parts)}

User Question: {query}

Return the JSON contract described in the system instruction."""

    try:
        response = chat_completion(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            session=session,
            temperature=0.1,
        )
        parsed = _parse_grounded_response(response, citations_map)
        if parsed:
            # Providers can still misclassify a clearly matching paraphrase as
            # absent. Preserve grounded evidence instead of discarding it.
            if parsed["answer"] == NOT_FOUND_ANSWER:
                fallback = _extractive_fallback(query, context_chunks)
                if fallback:
                    return {"answer": fallback, "citations": list(citations_map.values())}
            return parsed

        # Backward-compatible safety net for models that ignore the JSON contract.
        rejection_phrases = (
            "could not find this information", "could not find that information", "not found in the uploaded", "not mentioned in",
            "not covered in", "no information about this", "documents do not contain",
        )
        if any(phrase in response.lower() for phrase in rejection_phrases):
            fallback = _extractive_fallback(query, context_chunks)
            if fallback:
                return {"answer": fallback, "citations": list(citations_map.values())}
            return {"answer": NOT_FOUND_ANSWER, "citations": []}

        return {"answer": response.strip(), "citations": list(citations_map.values())}
    except Exception:
        fallback = _extractive_fallback(query, context_chunks)
        if fallback:
            return {"answer": fallback, "citations": list(citations_map.values())}
        return {"answer": "An error occurred while generating the answer.", "citations": []}
