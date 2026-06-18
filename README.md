# 🛡️ RefundGuard – AI Customer Support Agent

**Agentic AI for e-commerce refund processing** | LangGraph + RAG + ChromaDB + Groq

---

## Problem Statement
E‑commerce support teams spend hours manually reviewing refund requests against policy documents and customer histories. RefundGuard automates this decision‑making using an agentic AI that enforces rules consistently, transparently, and **personalizes responses** based on actual CRM data.

## Solution Overview
A fully functional web application where a customer types their **unique ID** and their refund request. The AI agent:
- Extracts the customer ID using **Groq Llama 3** (with a regex fallback for reliability)
- Looks up the customer in the mock CRM database
- Retrieves relevant policy rules using RAG (ChromaDB + sentence‑transformers)
- Evaluates eligibility based on policy rules (return window, item condition) and customer history (return count)
- Responds with a **personalized approval or denial** including the customer's name and remaining return quota
- Shows full reasoning logs in real time for auditability

## Architecture

### Agent Framework – LangGraph
- State‑based graph with conditional nodes: `extract_entities` → `retrieve_policy` → `check_eligibility` → `make_decision`
- Conditional edge: if no valid Customer ID is found, the agent stops and asks the user to provide one (professional error handling)
- Tool calling: `get_customer_info`, `retrieve_policy_rules`, `check_refund_eligibility`, `approve_refund`, `deny_refund`

### Retrieval‑Augmented Generation (RAG)
- Policy document chunked and embedded using `all‑MiniLM‑L6‑v2` (sentence‑transformers)
- Stored in ChromaDB (local, persistent)
- At query time, relevant policy clauses are retrieved and fed to the agent

### LLM Integration – Groq
- **Groq Llama 3** is used for entity extraction (parsing Customer ID, days ago, and item condition from natural language)
- Fallback to regex if the LLM is unavailable – ensures the demo never breaks

### Frontend & Observability
- Streamlit chat interface with input at the top and newest messages first
- Side panel displays **real-time agent reasoning logs** (each step, inputs, outputs, decisions)
- Personalized responses with customer name and remaining return quota (e.g., *"You have 2 returns remaining this year."*)

### Mock Data
- SQLite database with 15 customer profiles (ID, name, order count, return count, lifetime value)
- Refund policy written as a plain text file

## Key Technical Decisions & Tradeoffs

**Groq LLM for extraction + Deterministic rules for decision**  
→ *Why*: The LLM handles messy natural language (e.g., "unopened", "sealed"), while the deterministic rules guarantee zero hallucination on approvals/denials. This is the industry standard for compliance-sensitive systems.

**Local embeddings (sentence‑transformers) over cloud embeddings**  
→ *Tradeoff*: Lower latency, zero cost, full privacy. Sacrificed potential accuracy of a larger cloud model (e.g., OpenAI embeddings).

**Conditional edge to ask for missing ID**  
→ *Benefit*: The agent doesn't guess or hallucinate a customer – it explicitly asks for the ID if missing, mimicking professional chatbot behavior.

**SQLite over PostgreSQL**  
→ *Tradeoff*: Simpler for demo, no separate server. Would replace in production.

## Dynamic Customer Lookup
Customers type their unique ID (e.g., `64572df8`) anywhere in the chat. The Groq LLM extracts it, the agent verifies it in the database, fetches the customer's name and return history, and personalizes the response.

## Edge Cases Demonstrated
- ✅ **Approval** – `"64572df8 I want to return an unused item I bought 5 days ago"` → approved with name and remaining quota
- ❌ **Denial (item condition)** – `"64572df8 I want to return a used item I bought 5 days ago"` → denied with specific reason
- ❌ **Denial (return window)** – `"64572df8 I want to return an unused item I bought 40 days ago"` → denied (outside 30 days)
- ❌ **Missing ID** – `"I want to return an unused item"` → agent asks for Customer ID

## Lessons Learned
- String matching for `"unused"` vs `"used"` taught me to handle substring overlaps carefully – solved by checking `"unused"` first.
- Groq LLM drastically improves flexibility for user input compared to regex alone.
- ChromaDB with local embeddings works reliably offline but requires initial model download.

## Hindsight & Future Improvements
- Replace regex fallback with a secondary small LLM for even better robustness.
- Add voice pipeline (OpenAI Realtime API or ElevenLabs) for omnichannel support.
- Deploy on Vercel or Streamlit Cloud for live access.
- Add human‑in‑the‑loop approval for high‑risk cases.

## Demo Video
[Loom link will be added after recording]

## Author
**Ishan Dubey**  
📧 dubeyishan02@gmail.com  
🔗 [linkedin.com/in/ishan-dubey](https://linkedin.com/in/ishan-dubey-a6553b219/)