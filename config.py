import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Read from env vars first, then fall back to Streamlit Cloud secrets."""
    value = os.getenv(key)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
ORCHESTRATOR_MODEL = _get_secret("ORCHESTRATOR_MODEL", "gpt-5.4-mini")
NANO_MODEL = _get_secret("NANO_MODEL", "gpt-5.4-nano")
REGULATORY_VECTOR_STORE_ID = _get_secret("REGULATORY_VECTOR_STORE_ID")
