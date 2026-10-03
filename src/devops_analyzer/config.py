import os
import streamlit as st

# Recommended models on Groq
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "qwen-2.5-32b"

def get_groq_api_key() -> str:
    """Retrieve Groq API key from Streamlit secrets or environment variables."""
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.environ.get("GROQ_API_KEY", "")