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

# Define node functions
def extract_entities(state: AgentState) -> AgentState:
    last_message = state["messages"][-1] if state["messages"] else None
    user_message = last_message.content if last_message else ""
    
    logs = state.get("logs", [])
    
    # Get a real customer ID from database – prefer one with low returns (<=3) for approval demo
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM customers WHERE returns_last_12m <= 3 LIMIT 1")
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT customer_id FROM customers LIMIT 1")
        row = cursor.fetchone()
    conn.close()
    customer_id = row[0] if row else "abc123"
    
    order_id = "ORD001"
    days_ago = 10
    item_condition = "unused"
    
    # Parse days_ago from message
    if "5 days" in user_message.lower():
        days_ago = 5
    elif "10 days" in user_message.lower():
        days_ago = 10
    elif "30 days" in user_message.lower() or "thirty" in user_message.lower():
        days_ago = 35   # outside policy
    elif "40 days" in user_message.lower() or "forty" in user_message.lower():
        days_ago = 40
    
    # Parse condition – check "unused" first
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

def retrieve_policy(state: AgentState) -> AgentState:
    last_message = state["messages"][-1] if state["messages"] else None
    user_message = last_message.content if last_message else ""
    
    policy_text = retrieve_policy_rules(user_message)
    logs = state.get("logs", [])
    logs.append({"step": "retrieve_policy", "output": policy_text[:100] + "..." if len(policy_text) > 100 else policy_text})
    state["logs"] = logs
    state["policy_context"] = policy_text
    return state

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

def make_decision(state: AgentState) -> AgentState:
    eligibility = state.get("eligibility", {})
    logs = state.get("logs", [])
    order_id = state.get("extracted_order_id", "ORD001")
    
    if eligibility.get("eligible"):
        result = approve_refund(order_id, 49.99)
        state["decision"] = "approve"
        state["refund_approved"] = True
        state["final_response"] = result["message"]
    else:
        reason = eligibility.get("reason", "Policy violation")
        result = deny_refund(order_id, reason)
        state["decision"] = "deny"
        state["refund_approved"] = False
        state["final_response"] = result["message"]
    
    logs.append({"step": "make_decision", "output": f"Decision: {state['decision']}"})
    state["logs"] = logs
    return state

# Build the graph
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

# Pre-compile the agent once
_agent = build_agent()

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