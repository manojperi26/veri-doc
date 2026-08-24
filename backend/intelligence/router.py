from intelligence.llm import chat_completion
from typing import Optional, Any
import json

def route_query(query: str, session: Optional[Any] = None) -> dict:
    """
    Classifies the query and sets retrieval depth.
    Defaults to Simple if LLM fails.
    """
    default_res = {"type": "Simple", "depth": 3}
        
    prompt = f"""
Classify the following user query into one of these types:
- Simple (Basic factual question) -> depth: 3
- Complex (Requires synthesizing information) -> depth: 8
- Comparison (Comparing entities or documents) -> depth: 8
- Summarization (Asking for a summary) -> depth: 10
- Reasoning (Requires logical deduction) -> depth: 8
- Multi-document (Explicitly asks about multiple sources) -> depth: 10
- Follow-up (Refers to previous context) -> depth: 5

Query: {query}

Return ONLY a JSON object with 'type' and 'depth' keys. No markdown formatting or other text.
"""
    try:
        content = chat_completion([{"role": "user", "content": prompt}], session=session, temperature=0.1)
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        data = json.loads(content)
        if "type" in data and "depth" in data:
            return data
    except Exception as e:
        print(f"Router failed: {e}")
        
    return default_res
