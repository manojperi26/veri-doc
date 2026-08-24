from intelligence.llm import chat_completion
from typing import Optional, Any

def rewrite_query(query: str, chat_history: list, session: Optional[Any] = None) -> str:
    """
    Rewrites a context-dependent follow-up question into a standalone query.
    chat_history should be list of dicts: {"role": "user"/"assistant", "content": "..."}
    """
    if not chat_history:
        return query
        
    history_str = ""
    for msg in chat_history[-6:]:  # Last 6 turns
        history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
    prompt = f"""
Given the following conversation history and a new user query, rewrite the user query to be a standalone question that captures all necessary context from the history.
If the query is already standalone, return it exactly as is.
DO NOT answer the question. ONLY return the rewritten query.

Conversation History:
{history_str}

New Query: {query}

Rewritten Query:"""
    
    try:
        content = chat_completion([{"role": "user", "content": prompt}], session=session, temperature=0.1)
        return content.strip()
    except Exception as e:
        print(f"Query rewrite failed: {e}")
        
    return query
