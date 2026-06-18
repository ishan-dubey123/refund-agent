import streamlit as st
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph import run_agent
import sqlite3
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="RefundGuard - AI Customer Support",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CUSTOM CSS FOR PROFESSIONAL LOOK ----------
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 0.5rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: transparent !important;
        padding: 0.5rem 0 !important;
    }
    
    /* User message styling */
    .stChatMessage[data-testid="user"] {
        background-color: #e8f0fe !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        border-left: 4px solid #1a73e8 !important;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant"] {
        background-color: #f1f3f4 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        border-left: 4px solid #34a853 !important;
    }
    
    /* Denial messages - red accent */
    .stChatMessage[data-testid="assistant"]:has(.stMarkdown:contains("❌")) {
        border-left: 4px solid #ea4335 !important;
    }
    
    /* Log entry styling */
    .log-entry {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #5f6368;
        font-size: 0.85rem;
    }
    
    .log-step {
        font-weight: 600;
        color: #1a73e8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .log-output {
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        color: #202124;
        white-space: pre-wrap;
        word-break: break-word;
        background-color: #ffffff;
        padding: 0.5rem;
        border-radius: 4px;
        margin-top: 0.25rem;
        border: 1px solid #e8eaed;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Title styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 0.1rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #5f6368;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #e8eaed;
        padding-bottom: 0.5rem;
    }
    
    /* Approval badge */
    .badge-approve {
        background-color: #34a853;
        color: white;
        padding: 0.1rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-deny {
        background-color: #ea4335;
        color: white;
        padding: 0.1rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Logs panel header */
    .logs-header {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
    }
    
    .logs-container {
        background-color: #f8f9fa;
        border-radius: 0 0 8px 8px;
        padding: 0.75rem;
        border: 1px solid #e8eaed;
        border-top: none;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        color: #9aa0a6;
        padding: 2rem 0;
        font-size: 0.9rem;
    }
    
    /* Chat container */
    .chat-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 0.25rem 0.5rem;
        border: 1px solid #e8eaed;
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Divider */
    .custom-divider {
        border-top: 2px solid #e8eaed;
        margin: 1.5rem 0 0.5rem 0;
    }
    
    /* Input box styling */
    .stChatInput {
        border: 2px solid #dadce0 !important;
        border-radius: 24px !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stChatInput:focus {
        border-color: #1a73e8 !important;
        box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.2) !important;
    }
    
    /* Sidebar customer table */
    .sidebar-table {
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- INITIALIZE SESSION STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 📊 Mock CRM Database")
    
    conn = sqlite3.connect("crm.db")
    df = pd.read_sql_query("SELECT customer_id, name, total_orders, returns_last_12m FROM customers LIMIT 5", conn)
    conn.close()
    
    st.dataframe(df, width='stretch', hide_index=True)
    st.caption("💡 Start your message with a **Customer ID** (e.g., `64572df8`)")
    
    st.divider()
    st.markdown("### 🛠️ System Status")
    st.markdown("✅ LangGraph Agent")
    st.markdown("✅ ChromaDB RAG")
    st.markdown("✅ Groq LLM")
    st.markdown("✅ SQLite CRM")
    
    st.divider()
    st.caption("Built for Foundersmax | AI Engineer Challenge")

# ---------- MAIN LAYOUT ----------
# Title
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-title">🛡️ RefundGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Agentic AI for e‑commerce refund processing  |  LangGraph + RAG + ChromaDB</div>', unsafe_allow_html=True)

# ---------- CREATE TWO COLUMNS ----------
chat_col, logs_col = st.columns([0.65, 0.35], gap="medium")

# ---------- CHAT COLUMN ----------
with chat_col:
    st.markdown("### 💬 Customer Chat")
    
    # Chat container with scroll
    chat_container = st.container()
    
    with chat_container:
        # Input box at TOP
        if prompt := st.chat_input("Type your refund request... (e.g., 64572df8 I want to return...)"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Call agent
            with st.spinner("🤔 Agent thinking..."):
                response, logs = run_agent(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.logs = logs
            
            st.rerun()
        
        # Display messages in REVERSE order (newest first)
        if st.session_state.messages:
            for msg in reversed(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    # Add badge for approvals/denials
                    content = msg["content"]
                    if "✅" in content:
                        st.markdown(f'<span class="badge-approve">APPROVED</span>', unsafe_allow_html=True)
                    elif "❌" in content:
                        st.markdown(f'<span class="badge-deny">DENIED</span>', unsafe_allow_html=True)
                    st.markdown(content)
        else:
            st.info("👋 Start by typing a refund request above. Include your Customer ID for a personalized response.")

# ---------- ADMIN LOGS COLUMN ----------
with logs_col:
    st.markdown("### 📋 Agent Reasoning Logs")
    
    # Logs container with header
    st.markdown('<div class="logs-header">🧠 Real‑Time Agent Trace</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="logs-container">', unsafe_allow_html=True)
        
        if st.session_state.logs:
            for log in st.session_state.logs:
                step = log.get("step", "unknown")
                output = log.get("output", "")
                
                # Format output nicely
                if output.startswith("{") or output.startswith("["):
                    # It's JSON – display as code
                    output_display = f"```json\n{output}\n```"
                else:
                    output_display = output
                
                st.markdown(f"""
                <div class="log-entry">
                    <div class="log-step">🔹 {step}</div>
                    <div class="log-output">{output}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">No logs yet.<br>Send a message to see agent reasoning.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption("© 2026 Ishan Dubey · Foundersmax AI Engineer Challenge")