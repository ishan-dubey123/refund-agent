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

# ---- Node 1: Extract entities ----
def extract_entities(state: AgentState) -> AgentState:
    last_message = state["messages"][-1] if state["messages"] else None
    user_message = last_message.content if last_message else ""
    
    logs = state.get("logs", [])
    
    # Connect to database to find customer ID in the message
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()
    
    # Try to find a customer ID in the user's message
    words = user_message.split()
    found_customer_id = None
    for word in words:
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (word,))
        if cursor.fetchone():
            found_customer_id = word
            break
    
    if found_customer_id:
        customer_id = found_customer_id
        logs.append({"step": "extract_entities", "output": f"Found customer ID in message: {customer_id}"})
    else:
        # Fallback: pick a customer with good history (<=3 returns)
        cursor.execute("SELECT customer_id FROM customers WHERE returns_last_12m <= 3 LIMIT 1")
        row = cursor.fetchone()
        customer_id = row[0] if row else "abc123"
        logs.append({"step": "extract_entities", "output": f"No customer ID found, using default: {customer_id}"})
    
    conn.close()
    
    # Parse other details: days ago, item condition
    order_id = "ORD001"
    days_ago = 10
    item_condition = "unused"
    
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
    
    state["customer_id"] = customer_id
    logs.append({"step": "extract_entities", "output": f"customer={customer_id}, order={order_id}, days_ago={days_ago}, condition={item_condition}"})
    state["logs"] = logs
    state["extracted_order_date"] = f"days_ago:{days_ago}"
    state["extracted_item_condition"] = item_condition
    state["extracted_order_id"] = order_id
    return state

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

# ---- Node 4: Make decision with personalized response ----
def make_decision(state: AgentState) -> AgentState:
    eligibility = state.get("eligibility", {})
    logs = state.get("logs", [])
    order_id = state.get("extracted_order_id", "ORD001")
    customer_id = state.get("customer_id")
    
    # Fetch customer name from the database
    customer_name = "Customer"
    if customer_id:
        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            customer_name = row[0]
    
    # Build personalized response
    if eligibility.get("eligible"):
        state["decision"] = "approve"
        state["refund_approved"] = True
        state["final_response"] = f"✅ {customer_name}, your refund of $49.99 has been approved for order {order_id}."
    else:
        reason = eligibility.get("reason", "Policy violation")
        state["decision"] = "deny"
        state["refund_approved"] = False
        state["final_response"] = f"❌ {customer_name}, your refund has been denied for order {order_id}. Reason: {reason}"
    
    logs.append({"step": "make_decision", "output": f"Decision: {state['decision']} for customer {customer_name}"})
    state["logs"] = logs
    return state

# ---- Build the LangGraph workflow ----
def build_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("retrieve_policy", retrieve_policy)
    workflow.add_node("check_eligibility", check_eligibility)
    workflow.add_node("make_decision", make_decision)
    
    workflow.set_entry_point("extract_entities")
    workflow.add_edge("extract_entities", "retrieve_policy")
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
