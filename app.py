import os
import math
import pandas as pd
import streamlit as st

from devops_analyzer.log_parser import get_log_summary
from devops_analyzer.agent import run_log_agent

SAMPLE_CSV_PATH = "data/sample_logs.csv"

st.set_page_config(
    page_title="DevOps Deployment Log Analyzer",
    page_icon="🛠️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    .stChatMessage { border-radius: 8px; }
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .main-header { 
        text-align: center; 
        color: #ffffff; 
        padding-bottom: 20px; 
    }
    .subheader { 
        text-align: center; 
        color: white; 
        padding-bottom: 20px; 
    }
    </style>
""", unsafe_allow_html=True)

# Helper function for cached CSV downloads
@st.cache_data
def convert_df_to_csv(df_to_export):
    return df_to_export.to_csv(index=False).encode("utf-8")

# State Management
if "page_index" not in st.session_state:
    st.session_state.page_index = 0
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! Upload a DevOps CSV log file or load sample data to start analysis."}
    ]
if "df" not in st.session_state:
    st.session_state.df = None

st.markdown("<h2 class='main-header'>🛠️ DevOps Deployment Log Analyzer 🛠️</h2>", unsafe_allow_html=True)
st.markdown("<h5 class='subheader'> AI-Powered Failure Root-Cause Analysis for CI/CD Pipeline Logs </h5>", unsafe_allow_html=True)

main_col, chat_col = st.columns([6, 4], gap="large")

with main_col:
    st.subheader("📂 Log Ingestion")
    
    # Dual Ingestion Layout: Upload CSV OR Load Preset Sample Dataset
    col_upload, col_sample = st.columns([3, 2])

    with col_upload:
        uploaded_file = st.file_uploader("Upload DevOps Pipeline Log (.csv)", type=["csv"])

    with col_sample:
        st.write("Don't have a CSV Logs? try this!")
        if st.button("🚀 Load Sample Dataset", use_container_width=True):
            if os.path.exists(SAMPLE_CSV_PATH):
                st.session_state.df = pd.read_csv(SAMPLE_CSV_PATH)
                st.session_state.page_index = 0
                st.success("Sample dataset loaded!")
                st.rerun()
            else:
                st.error(f"Sample file not found at `{SAMPLE_CSV_PATH}`.")

    # Process File Upload (Overrides session state if uploaded)
    if uploaded_file:
        if not uploaded_file.name.lower().endswith(".csv"):
            st.error("Invalid file format. Please upload a valid `.csv` file.")
            st.stop()

        allowed_types = ["text/csv", "application/vnd.ms-excel", "text/plain"]
        if uploaded_file.type and uploaded_file.type not in allowed_types:
            st.error("Security Alert: The uploaded file is not a valid CSV format.")
            st.stop()
            
        try:
            @st.cache_data
            def load_csv(file):
                return pd.read_csv(file)

            st.session_state.df = load_csv(uploaded_file)
        except Exception as e:
            st.error(f"Failed to process CSV file: {e}")

    # Render Dashboard Metrics & Data Preview if DataFrame is populated
    if st.session_state.df is not None:
        df = st.session_state.df
        summary = get_log_summary(df)

        # Metadata Metrics Summary
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", summary["total_logs"])
        m2.metric("Total Fields", len(summary["columns"]))
        m3.metric("Detected Levels", len(summary["level_counts"]))

        st.markdown("<div style='margin-top: 10px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        st.subheader("📊 Data Preview")

        max_pages = max(1, math.ceil(len(df) / 10))
        start_row = st.session_state.page_index * 10
        st.dataframe(df.iloc[start_row : start_row + 10], use_container_width=True)

        # Centered Pagination Controls
        b1, b2, b3 = st.columns([1, 2, 1])

        with b1:
            if st.button("⬅️ Previous", key="btn_prev", use_container_width=True) and st.session_state.page_index > 0:
                st.session_state.page_index -= 1
                st.rerun()

        with b2:
            st.markdown(
                f"<p style='text-align: center; margin-top: 6px; font-weight: 600; font-size: 15px;'>"
                f"Page {st.session_state.page_index + 1} of {max_pages}"
                f"</p>",
                unsafe_allow_html=True
            )

        with b3:
            if st.button("Next ➡️", key="btn_next", use_container_width=True) and st.session_state.page_index < max_pages - 1:
                st.session_state.page_index += 1
                st.rerun()

        st.write("---")

with chat_col:
    c_head, c_btn = st.columns([7, 3])
    with c_head:
        st.subheader("🤓 Log Analyzer")
    with c_btn:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "👋 Hi! Upload a DevOps CSV log file or load sample data to start analysis."}
            ]
            st.rerun()

    chat_container = st.container(height=660)
    with chat_container:
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ask about failure root causes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user").write(prompt)

        if st.session_state.df is None:
            no_df_msg = "⚠️ Please upload a CSV log file or load sample data before asking questions."
            st.session_state.messages.append({"role": "assistant", "content": no_df_msg})
            with chat_container:
                st.chat_message("assistant").write(no_df_msg)
            st.rerun()

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing log events..."):
                    response = run_log_agent(st.session_state.df, prompt, st.session_state.messages)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})