# 🛡️ RefundGuard – AI Customer Support Agent

**Agentic AI for e-commerce refund processing** | LangGraph + RAG + Streamlit

---

## Problem Statement
E‑commerce support teams spend hours manually reviewing refund requests against policy documents and customer histories. RefundGuard automates this decision‑making using an agentic AI that enforces rules consistently, transparently, and **personalizes responses** based on actual CRM data.

## Solution Overview
A fully functional web application where a customer types their **unique ID** and their refund request. The AI agent:
- Looks up the customer in the mock CRM database
- Retrieves relevant policy rules using RAG (ChromaDB)
- Evaluates eligibility based on policy and customer history
- Responds with a **personalized approval or denial** (e.g., *"✅ Nicholas Hodges, your refund has been approved..."*)
- Shows full reasoning logs in real time for auditability

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
- Personalized responses with customer name from the database

### Mock Data
- SQLite database with 15 customer profiles (ID, name, order count, return count, lifetime value)
- Refund policy written as a plain text file

## Key Technical Decisions & Tradeoffs

**Local embeddings (sentence‑transformers) over cloud embeddings**  
→ *Tradeoff*: Lower latency, zero cost, full privacy. Sacrificed potential accuracy of a larger cloud model (e.g., OpenAI embeddings).

**Rule‑based entity extraction instead of LLM call**  
→ *Tradeoff*: Faster, deterministic, no extra API cost. Less robust to varied phrasing; acceptable for this scope. The agent detects customer IDs by scanning the chat message for known database IDs.

**LangGraph over raw function calling**  
→ *Benefit*: Built‑in state management, easier to add human‑in‑the‑loop or conditional edges later.

**SQLite over PostgreSQL**  
→ *Tradeoff*: Simpler for demo, no separate server. Would replace in production.

## Dynamic Customer Lookup
Customers type their unique ID (e.g., `64572df8`) as the first word in the chat. The agent extracts it, queries the database, and fetches the customer's name and return history. This demonstrates real‑world CRM integration and dynamic tool calling.

## Edge Cases Demonstrated
- ✅ **Approval** – `"64572df8 I want to return an unused item I bought 5 days ago"` → approved with name
- ❌ **Denial (item condition)** – `"64572df8 I want to return a used item I bought 5 days ago"` → denied with reason
- ❌ **Denial (return window)** – `"64572df8 I want to return an unused item I bought 40 days ago"` → denied (outside 30 days)
- ❌ **Denial (high‑risk customer)** – customer with >3 returns → manual review required

## Lessons Learned
- String matching for `"unused"` vs `"used"` taught me to handle substring overlaps carefully.
- Scanning chat messages for customer IDs is a simple but effective way to simulate CRM integration.
- ChromaDB with local embeddings works reliably offline but requires initial model download.
- Real‑time log streaming to the admin panel is straightforward with Streamlit’s `st.empty()` container.

## Hindsight & Future Improvements
- Replace keyword‑based extraction with a small LLM (Groq Llama 3) for better intent parsing.
- Add voice pipeline (OpenAI Realtime API or ElevenLabs) for omnichannel support.
- Deploy on Vercel or Streamlit Cloud for live access.
- Add human‑in‑the‑loop approval for edge cases.

## Demo Video
[Insert Loom link here]

## Author
**Ishan Dubey**  
📧 dubeyishan02@gmail.com  
🔗 [linkedin.com/in/ishan-dubey](https://linkedin.com/in/ishan-dubey-a6553b219/)
