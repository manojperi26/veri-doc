from intelligence.llm import chat_completion
from typing import Optional, Any
import json

def generate_questions(text: str, session: Optional[Any] = None) -> list:
    if not text:
        return []
        
    prompt = f"""
Based on the following document excerpt, suggest exactly 5 questions a user might ask:
1 Basic
1 Intermediate
1 Advanced
1 Comparison
1 Analytical

Document: {text[:4000]}

Return ONLY a JSON array of strings containing the 5 questions.
"""
    try:
        content = chat_completion([{"role": "user", "content": prompt}], session=session, temperature=0.1)
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        questions = json.loads(content)
        return questions[:5]
    except Exception as e:
        print(f"Question generation failed: {e}")
        return []

def generate_summary(text: str, session: Optional[Any] = None) -> dict:
    if not text:
        return {}
        
    prompt = f"""
Summarize the following document excerpt. Provide the result as a JSON object with these exact keys:
"Executive Summary" (string), "Key Topics" (array of strings), "Important Facts" (array of strings), "Key Numbers" (array of strings), "Conclusion" (string).

Document: {text[:6000]}

Return ONLY valid JSON.
"""
    try:
        content = chat_completion([{"role": "user", "content": prompt}], session=session, temperature=0.1)
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        return json.loads(content)
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return {}
