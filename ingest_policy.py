import os
import chromadb
from chromadb.utils import embedding_functions

# Force cache to be inside project folder
os.environ["HF_HOME"] = os.path.join(os.getcwd(), "hf_cache")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(os.getcwd(), "hf_cache")

# Use ChromaDB's embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Connect to ChromaDB (persistent)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="refund_policy",
    embedding_function=embedding_fn
)

# Read policy file
with open("policy.txt", "r") as f:
    policy_text = f.read()

# Split into chunks (by non-empty lines)
chunks = [chunk.strip() for chunk in policy_text.split("\n") if chunk.strip()]

# Add to ChromaDB
for i, chunk in enumerate(chunks):
    collection.upsert(
        ids=[f"chunk_{i}"],
        documents=[chunk],
        metadatas=[{"source": "policy.txt", "index": i}]
    )

print(f"✅ Ingested {len(chunks)} policy chunks into ChromaDB")
print("Sample chunk:", chunks[0] if chunks else "None")