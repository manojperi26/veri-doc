import os
import re
from typing import List, Dict, Any, Optional
from groq import Groq
from huggingface_hub import InferenceClient
from config import settings

def _strip_thinking_tags(text: str) -> str:
    """Remove <think>...</think> blocks that some models leak into responses."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Also strip partial/unclosed <think> blocks at the start
    cleaned = re.sub(r'^<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

PREFERRED_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

PREFERRED_HUGGINGFACE_MODELS = [
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]

def is_provider_error(exc: Exception) -> bool:
    """
    Returns True if the exception is an API/provider/network failure
    (suitable for fallback), and False if it's a programming bug.
    """
    if isinstance(exc, (TypeError, ValueError, AttributeError, KeyError, NameError, SyntaxError, IndexError, ImportError)):
        return False
    return True

def _get_active_groq_models(client: Groq) -> List[str]:
    try:
        models_data = client.models.list().data
        active_ids = {m.id for m in models_data}
        # Pick preferred models that exist in active_ids
        selected = [m for m in PREFERRED_GROQ_MODELS if m in active_ids]
        if not selected:
            # Fall back to any text generation model available
            selected = [m.id for m in models_data if "whisper" not in m.id and "guard" not in m.id]
        return selected if selected else PREFERRED_GROQ_MODELS
    except Exception as e:
        print(f"Could not fetch live Groq models: {e}")
        return PREFERRED_GROQ_MODELS

def _call_groq(messages: List[Dict[str, str]], api_key: str, temperature: float = 0.1) -> str:
    client = Groq(api_key=api_key)
    models_to_try = _get_active_groq_models(client)
    
    last_err = None
    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature
            )
            raw = response.choices[0].message.content.strip()
            return _strip_thinking_tags(raw)
        except Exception as e:
            if not is_provider_error(e):
                raise e
            last_err = e
            continue
            
    if last_err:
        raise last_err
    raise RuntimeError("No active Groq models succeeded.")

def _call_huggingface(messages: List[Dict[str, str]], api_key: str, temperature: float = 0.1) -> str:
    client = InferenceClient(api_key=api_key)
    
    last_err = None
    for model_name in PREFERRED_HUGGINGFACE_MODELS:
        try:
            response = client.chat_completion(
                messages=messages,
                model=model_name,
                temperature=max(0.01, temperature),
                max_tokens=2048,
            )
            raw = response.choices[0].message.content.strip()
            return _strip_thinking_tags(raw)
        except Exception as e:
            if not is_provider_error(e):
                raise e
            last_err = e
            continue
            
    if last_err:
        raise last_err
    raise RuntimeError("No Hugging Face models succeeded.")

def get_groq_client(session: Optional[Any] = None) -> Optional[Groq]:
    key = (session.groq_api_key if session and getattr(session, 'groq_api_key', None) else None) or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if key:
        return Groq(api_key=key)
    return None

def chat_completion(messages: List[Dict[str, str]], session: Optional[Any] = None, temperature: float = 0.1) -> str:
    groq_key = (session.groq_api_key if session and getattr(session, 'groq_api_key', None) else None) or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    huggingface_key = (session.huggingface_api_key if session and getattr(session, 'huggingface_api_key', None) else None) or settings.HUGGINGFACE_API_KEY or os.environ.get("HUGGINGFACE_API_KEY")

    groq_failed = False
    groq_error_msg = ""

    # ALWAYS try Groq first for every request
    if groq_key:
        try:
            return _call_groq(messages, api_key=groq_key, temperature=temperature)
        except Exception as e:
            if not is_provider_error(e):
                raise e
            groq_failed = True
            groq_error_msg = str(e)
            print(f"Groq primary provider failed: {e}. Attempting fallback to Hugging Face...")
    else:
        groq_failed = True
        groq_error_msg = "Groq API key not configured."

    # Attempt Hugging Face Fallback if Groq failed
    if huggingface_key:
        try:
            return _call_huggingface(messages, api_key=huggingface_key, temperature=temperature)
        except Exception as e:
            if not is_provider_error(e):
                raise e
            print(f"Hugging Face backup provider failed: {e}")
            raise RuntimeError(f"Both AI providers are temporarily unavailable. Groq error: {groq_error_msg}. Hugging Face error: {str(e)}")

    if groq_failed:
        raise RuntimeError(f"Both AI providers are temporarily unavailable. Groq error: {groq_error_msg}. (Hugging Face backup key not provided)")

    raise RuntimeError("No AI provider API keys configured.")
