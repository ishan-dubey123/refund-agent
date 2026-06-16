from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str
    logs: List[Dict[str, Any]]
    decision: str
    refund_approved: bool
    final_response: str
    policy_context: str
    eligibility: dict
    extracted_order_date: str
    extracted_item_condition: str
    extracted_order_id: str