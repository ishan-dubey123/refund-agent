import streamlit as st
import sys
import os

# Add project root to path so we can import agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph import run_agent
import sqlite3
import pandas as pd

# Page config
st.set_page_config(
    page_title="RefundGuard - AI Customer Support",
    page_icon="🛡️",
    layout="wide"
)

# Title
st.title("🛡️ RefundGuard - AI Customer Support Agent")
st.caption("Agentic AI for e-commerce refund processing | LangGraph + RAG + ChromaDB")

# Sidebar - Customer database preview
with st.sidebar:
    st.header("📊 Mock CRM Database")
    conn = sqlite3.connect("crm.db")
    df = pd.read_sql_query("SELECT customer_id, name, total_orders, returns_last_12m FROM customers LIMIT 5", conn)
    conn.close()
    st.dataframe(df, width='stretch')  # fixed from use_container_width
    st.caption("Demo: try 'return unused item 5 days ago' (approve) or 'return used item 5 days ago' (deny)")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []

# Create two columns: chat (70%) and admin logs (30%)
chat_col, logs_col = st.columns([0.7, 0.3])

# Chat interface
with chat_col:
    st.subheader("💬 Customer Chat")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Customer says..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Call the agent
        with st.chat_message("assistant"):
            with st.spinner("Agent thinking..."):
                response, logs = run_agent(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.logs = logs

# Admin logs panel
with logs_col:
    st.subheader("📋 Agent Reasoning Logs")
    log_container = st.container(height=400)
    with log_container:
        if st.session_state.logs:
            for log in st.session_state.logs:
                step = log.get("step", "unknown")
                output = log.get("output", "")
                st.text(f"🔹 {step}:")
                st.code(output, language="text", wrap_lines=True)
                st.divider()
        else:
            st.info("No logs yet. Send a message to see agent reasoning.")

# Footer
st.divider()
st.caption("Built with LangGraph, ChromaDB (RAG), Streamlit | Demo for Foundersmax")