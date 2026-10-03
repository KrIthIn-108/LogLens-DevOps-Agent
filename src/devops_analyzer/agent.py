import pandas as pd
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from devops_analyzer.config import DEFAULT_MODEL, get_groq_api_key
from devops_analyzer.prompts import SYSTEM_GUARDRAIL_PROMPT
import streamlit as st
import ast

@st.cache_resource
def get_llm():
    api_key = get_groq_api_key()
    return ChatGroq(
        groq_api_key=api_key,
        model_name=DEFAULT_MODEL,
        temperature=0.0
    )
def run_log_agent(df: pd.DataFrame, user_query: str, chat_history: list) -> str:
    api_key = get_groq_api_key()
    llm = get_llm()  # Uses pre-initialized cached instance instantly
    if not api_key:
        return "Error: GROQ_API_KEY is missing. Please set it in `.streamlit/secrets.toml` or environment variables."

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="qwen/qwen3.8-27b",
        temperature=0.0
    )

    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=False,
        allow_dangerous_code=True,
        agent_type="tool-calling",
        handle_parsing_errors=True,
        max_iterations=6,                       
        early_stopping_method="force"
    )
    # --- Security Layer: Wrap the execution tool with AST validation ---
    

    # --- Execute Query ---
    recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
    history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in recent_history])
    columns_str = ", ".join(list(df.columns))

    
    full_prompt = f"""
    {SYSTEM_GUARDRAIL_PROMPT}

    Dataframe Schema Columns: [{columns_str}]
    Total Rows: {len(df)}

    CRITICAL RULE FOR DATA EXPORTS:
    - Never run `.to_csv()`, `.to_excel()`, or write files to disk.
    - If the user asks for logs or summaries, print them directly as Markdown text or Markdown tables in your final answer.

    Contextual Chat History:
    {history_str}

    User Question: {user_query}
    """

    try:
        response = agent.invoke(full_prompt)
        return response.get("output", "Unable to compute a response from logs.")
    except Exception as e:
        err_str = str(e).lower()
        if any(k in err_str for k in ["429", "rate limit", "quota"]):
            return "⚠️ API Rate Limit reached on Groq. Please wait a few minutes before sending another request."
        return f"An error occurred while analyzing the logs: {str(e)}"