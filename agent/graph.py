from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from agent.state import AgentState
from agent.tools import (
    get_customer_info,
    retrieve_policy_rules,
    check_refund_eligibility,
    approve_refund,
    deny_refund
)
import json
import sqlite3
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# --- Load environment variables & Initialize Groq LLM ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0
)

# ---- Node 1: Extract entities (Hybrid: LLM + Fallback) ----
def extract_entities(state: AgentState) -> AgentState:
    last_message = state["messages"][-1] if state["messages"] else None
    user_message = last_message.content if last_message else ""
    
    logs = state.get("logs", [])
    
    customer_id = None
    days_ago = 10
    item_condition = "unused"
    
    # Step A: Try using LLM to extract structured data
    try:
        prompt = f"""
        Extract the following details from the user's refund request.
        User message: "{user_message}"

        Return ONLY a JSON object with these exact keys:
        - "customer_id": The customer ID (like '64572df8') if present, otherwise null.
        - "days_ago": The number of days ago the item was bought (as an integer).
        - "item_condition": Either "unused" or "used".

        Rules:
        - "unused" = unopened, sealed, new, untouched.
        - "used" = opened, damaged, worn, or explicitly says "used".
        - If days are not mentioned, set to 10.
        - Only output valid JSON. No markdown, no extra text.
        """

        response = llm.invoke(prompt)
        clean = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean)
        
        if data.get("customer_id") and data["customer_id"] != "null":
            customer_id = data["customer_id"]
        if data.get("days_ago"):
            days_ago = int(data["days_ago"])
        if data.get("item_condition"):
            item_condition = data["item_condition"]
            
        logs.append({"step": "extract_entities", "output": f"LLM extracted: {data}"})
        
    except Exception as e:
        logs.append({"step": "extract_entities", "output": f"LLM failed, using fallback. Error: {str(e)}"})
        
        # ---- Step B: FALLBACK to Regex ----
        words = user_message.split()
        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()
        
        for word in words:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (word,))
            if cursor.fetchone():
                customer_id = word
                break
        conn.close()
        
        if "5 days" in user_message.lower():
            days_ago = 5
        elif "10 days" in user_message.lower():
            days_ago = 10
        elif "30 days" in user_message.lower() or "thirty" in user_message.lower():
            days_ago = 35
        elif "40 days" in user_message.lower() or "forty" in user_message.lower():
            days_ago = 40
        
        if "unused" in user_message.lower():
            item_condition = "unused"
        elif "used" in user_message.lower():
            item_condition = "used"

    # ---- Step C: Verify the ID exists in database ----
    if customer_id:
        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (customer_id,))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            customer_id = None
            logs.append({"step": "extract_entities", "output": f"ID not found in database."})

    # ---- Step D: If NO ID, ASK the user and STOP the workflow ----
    if not customer_id:
        logs.append({"step": "extract_entities", "output": "No valid customer ID. Asking user to provide ID."})
        state["final_response"] = "❓ I couldn't find your customer ID. Could you please start your message with your Customer ID (e.g., '64572df8')?"
        state["customer_id"] = ""
        state["logs"] = logs
        # Set empty fields so the graph stops gracefully
        state["extracted_order_date"] = ""
        state["extracted_item_condition"] = ""
        state["extracted_order_id"] = ""
        return state

    # Store everything in state
    state["customer_id"] = customer_id
    logs.append({"step": "extract_entities", "output": f"Final: customer={customer_id}, days_ago={days_ago}, condition={item_condition}"})
    state["logs"] = logs
    state["extracted_order_date"] = f"days_ago:{days_ago}"
    state["extracted_item_condition"] = item_condition
    state["extracted_order_id"] = "ORD001"
    return state

# ---- Conditional Edge: Check if we should continue ----
def should_continue(state: AgentState) -> str:
    if state.get("customer_id") and state["customer_id"] != "":
        return "continue"
    else:
        return "end"

# ---- Node 2: Retrieve policy using RAG ----
def retrieve_policy(state: AgentState) -> AgentState:
    last_message = state["messages"][-1] if state["messages"] else None
    user_message = last_message.content if last_message else ""
    
    policy_text = retrieve_policy_rules(user_message)
    logs = state.get("logs", [])
    logs.append({"step": "retrieve_policy", "output": policy_text[:100] + "..." if len(policy_text) > 100 else policy_text})
    state["logs"] = logs
    state["policy_context"] = policy_text
    return state

# ---- Node 3: Check eligibility ----
def check_eligibility(state: AgentState) -> AgentState:
    customer_id = state.get("customer_id", "abc123")
    order_date = state.get("extracted_order_date", "days_ago:10")
    item_condition = state.get("extracted_item_condition", "unused")
    
    eligibility = check_refund_eligibility(order_date, item_condition, customer_id)
    logs = state.get("logs", [])
    logs.append({"step": "check_eligibility", "output": json.dumps(eligibility)})
    state["logs"] = logs
    state["eligibility"] = eligibility
    return state

# ---- Node 4: Make decision with personalized response & return count ----
def make_decision(state: AgentState) -> AgentState:
    eligibility = state.get("eligibility", {})
    logs = state.get("logs", [])
    order_id = state.get("extracted_order_id", "ORD001")
    customer_id = state.get("customer_id")
    
    # Fetch customer name and history from the database
    customer_name = "Customer"
    returns_count = 0
    if customer_id:
        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, returns_last_12m FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            customer_name = row[0]
            returns_count = row[1]
    
    # Build personalized response with return count
    if eligibility.get("eligible"):
        state["decision"] = "approve"
        state["refund_approved"] = True
        remaining = 3 - returns_count
        state["final_response"] = f"✅ {customer_name}, your refund of $49.99 has been approved for order {order_id}. (You have {remaining} return{'s' if remaining != 1 else ''} remaining this year.)"
    else:
        reason = eligibility.get("reason", "Policy violation")
        state["decision"] = "deny"
        state["refund_approved"] = False
        
        # Add history context to denial if it's a high-returns case
        if "returns in last 12 months" in reason:
            state["final_response"] = f"❌ {customer_name}, your refund has been denied for order {order_id}. {reason} (You have {returns_count} returns, limit is 3.)"
        else:
            state["final_response"] = f"❌ {customer_name}, your refund has been denied for order {order_id}. Reason: {reason}"
    
    logs.append({"step": "make_decision", "output": f"Decision: {state['decision']} for {customer_name} (Returns: {returns_count})"})
    state["logs"] = logs
    return state

# ---- Build the LangGraph workflow ----
def build_agent():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("retrieve_policy", retrieve_policy)
    workflow.add_node("check_eligibility", check_eligibility)
    workflow.add_node("make_decision", make_decision)
    
    # Set entry point
    workflow.set_entry_point("extract_entities")
    
    # Conditional edge: If no ID, stop here (ask for ID)
    workflow.add_conditional_edges(
        "extract_entities",
        should_continue,
        {
            "continue": "retrieve_policy",
            "end": END
        }
    )
    
    # Remaining edges
    workflow.add_edge("retrieve_policy", "check_eligibility")
    workflow.add_edge("check_eligibility", "make_decision")
    workflow.add_edge("make_decision", END)
    
    return workflow.compile()

# ---- Pre-compile the agent once ----
_agent = build_agent()

# ---- Entry point for the Streamlit app ----
def run_agent(user_message: str) -> tuple:
    """Run the agent and return (response, logs)."""
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "customer_id": "",
        "logs": [],
        "decision": "",
        "refund_approved": False,
        "final_response": "",
        "policy_context": "",
        "eligibility": {},
        "extracted_order_date": "",
        "extracted_item_condition": "",
        "extracted_order_id": ""
    }
    final_state = _agent.invoke(initial_state)
    return final_state["final_response"], final_state["logs"]