import os
import sys

# Force all HF cache to project folder BEFORE any model loading
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF_CACHE = os.path.join(PROJECT_ROOT, "hf_cache")
os.environ["HF_HOME"] = HF_CACHE
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_CACHE

# Create cache folder if not exists
os.makedirs(HF_CACHE, exist_ok=True)

import sqlite3
import chromadb
from chromadb.utils import embedding_functions

# Database paths
CRM_DB = os.path.join(PROJECT_ROOT, "crm.db")
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# Initialize ChromaDB with embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-V2"
)
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
policy_collection = chroma_client.get_or_create_collection(
    name="refund_policy",
    embedding_function=embedding_fn
)

def get_customer_info(customer_id: str) -> dict:
    conn = sqlite3.connect(CRM_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, name, email, total_orders, returns_last_12m, lifetime_value FROM customers WHERE customer_id = ?",
        (customer_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "customer_id": row[0],
            "name": row[1],
            "email": row[2],
            "total_orders": row[3],
            "returns_last_12m": row[4],
            "lifetime_value": row[5]
        }
    return {"error": "Customer not found"}

def retrieve_policy_rules(query: str) -> str:
    results = policy_collection.query(query_texts=[query], n_results=3)
    if results['documents'] and results['documents'][0]:
        return "\n".join(results['documents'][0])
    return "No relevant policy found."

def check_refund_eligibility(order_date: str, item_condition: str, customer_id: str) -> dict:
    customer = get_customer_info(customer_id)
    if "error" in customer:
        return {"eligible": False, "reason": "Customer not found"}
    
    days_ago = 10
    if "days_ago" in order_date:
        try:
            days_ago = int(order_date.split(":")[1])
        except:
            pass
    
    if days_ago > 30:
        return {"eligible": False, "reason": f"Order is {days_ago} days old, outside 30-day return window"}
    if item_condition.lower() != "unused":
        return {"eligible": False, "reason": "Item must be unused and in original packaging"}
    if customer["returns_last_12m"] > 3:
        return {"eligible": False, "reason": f"Customer has {customer['returns_last_12m']} returns in last 12 months, requires manual review"}
    
    return {"eligible": True, "reason": "All policy conditions met"}

def approve_refund(order_id: str, amount: float) -> dict:
    return {"status": "approved", "order_id": order_id, "amount": amount, "message": f"✅ Refund of ${amount} approved for order {order_id}"}

def deny_refund(order_id: str, reason: str) -> dict:
    return {"status": "denied", "order_id": order_id, "reason": reason, "message": f"❌ Refund denied for order {order_id}: {reason}"}