# 🛡️ RefundGuard – AI Customer Support Agent

**Agentic AI for e-commerce refund processing** | LangGraph + RAG + Streamlit

---

## Problem Statement
E‑commerce support teams spend hours manually reviewing refund requests against policy documents and customer history. RefundGuard automates this decision‑making using an agentic AI that enforces rules consistently and transparently.

## Solution Overview
A fully functional web application where a customer chats naturally and the AI agent approves or denies refunds based on:
- Refund policy (30‑day window, item condition, restocking fees)
- Customer history (return frequency, lifetime value)

The agent shows its **reasoning logs** in real time for auditability.

## Architecture

### Agent Framework – LangGraph
- State‑based graph with nodes: `extract_entities` → `retrieve_policy` → `check_eligibility` → `make_decision`
- Tool calling: `get_customer_info`, `retrieve_policy_rules`, `check_refund_eligibility`, `approve_refund`, `deny_refund`

### Retrieval‑Augmented Generation (RAG)
- Policy document chunked and embedded using `all‑MiniLM‑L6‑v2` (sentence‑transformers)
- Stored in ChromaDB (local, persistent)
- At query time, relevant policy clauses are retrieved and fed to the agent

### Frontend & Observability
- Streamlit chat interface for customer interaction
- Side panel displays **agent reasoning logs** (each step, inputs, outputs, decisions)

### Mock Data
- SQLite database with 15 customer profiles (name, order count, return count, lifetime value)
- Refund policy written as a plain text file

## Key Technical Decisions & Tradeoffs

**Local embeddings (sentence‑transformers) over cloud embeddings**  
→ *Tradeoff*: Lower latency, zero cost, full privacy. Sacrificed potential accuracy of a larger cloud model (e.g., OpenAI embeddings).

**Rule‑based entity extraction instead of LLM call**  
→ *Tradeoff*: Faster, deterministic, no extra API cost. Less robust to varied phrasing; acceptable for this scope.

**LangGraph over raw function calling**  
→ *Benefit*: Built‑in state management, easier to add human‑in‑the‑loop or conditional edges later.

**SQLite over PostgreSQL**  
→ *Tradeoff*: Simpler for demo, no separate server. Would replace in production.

## Edge Cases Demonstrated
- ✅ **Approval** – unused item, within 30 days, customer with low return history
- ❌ **Denial (item condition)** – used item, even within 30 days
- ❌ **Denial (return window)** – unused item but 40 days old
- ❌ **Denial (high‑risk customer)** – >3 returns in 12 months, requires manual review

## Lessons Learned
- String matching for `"unused"` vs `"used"` taught me to handle substring overlaps carefully.
- ChromaDB with local embeddings works reliably offline but requires initial model download.
- Real‑time log streaming to the admin panel is straightforward with Streamlit’s `st.empty()` container.

## Hindsight & Future Improvements
- Replace keyword‑based extraction with a small LLM (Groq Llama 3) for better intent parsing.
- Add voice pipeline (OpenAI Realtime API or ElevenLabs) for omnichannel support.
- Deploy on Vercel or Streamlit Cloud for live access.
- Add human‑in‑the‑loop approval for edge cases.

## Author
**Ishan Dubey**  
📧 dubeyishan02@gmail.com  
🔗 [linkedin.com/in/ishan-dubey](https://linkedin.com/in/ishan-dubey-a6553b219/)