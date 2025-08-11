# Put this at the very top of the file
from __future__ import annotations

# Now, other imports can follow
import pymongo
import os
import json
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection



# ==============================
# Configuration (edit to suit)
# ==============================
DEFAULT_DB = os.getenv("DB_NAME", "test")
DEFAULT_COLL = os.getenv("COLLECTION_NAME", "baffle_collection")
USE_ATLAS_VECTOR = os.getenv("USE_ATLAS_VECTOR", "1") == "1"
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "rag_vector_index")

# Which fields should be concatenated for RAG text?
TEXT_FIELDS = [
    "notes",
    "remarks",
    "description",
    "content",
]

# Safe-list for structured querying. Add your schema keys here.
ALLOWED_FIELDS = {
    "_id",
    "leadId",
    "name",
    "phone",
    "email",
    "city",
    "pincode",
    "crmStage",
    "telecallerName",
    "telecaller.name",
    "role",
    "createdAt",
    "modifiedAt",
    "notes",
    "remarks",
    "description",
    "content",
}

# =======================
# MongoDB connections
# =======================
@st.cache_resource(show_spinner=False)
def get_mongo() -> MongoClient:
    uri = os.getenv("MONGO_URI")
    if not uri:
        st.stop()
    client = MongoClient(uri)
    return client


def get_collection(client: MongoClient, db_name: str, coll_name: str) -> Collection:
    return client[db_name][coll_name]

# =======================
# Embeddings utilities
# =======================
@st.cache_resource(show_spinner=False)
def get_embedder():
    # Use the embeddings from Atlas or other models
    pass

def build_rag_text(doc: Dict[str, Any]) -> str:
    parts = []
    for f in TEXT_FIELDS:
        val = doc.get(f)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    # Fallback: include a couple common fields if no text fields are present
    if not parts:
        for f in ["name", "remarks", "notes"]:
            val = doc.get(f)
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())
    return " \\n".join(parts)

# =======================
# Vector search paths
# =======================
def atlas_vector_search(coll: Collection, query_vec: List[float], k: int = 5) -> List[Dict[str, Any]]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vec,
                "numCandidates": 200,
                "limit": k,
            }
        },
        {
            "$project": {
                "_id": 0,
                "score": {"$meta": "vectorSearchScore"},
                "name": 1,
                "leadId": 1,
                "telecallerName": 1,
                "telecaller": 1,
                "notes": 1,
                "remarks": 1,
                "content": 1,
            }
        },
    ]
    return list(coll.aggregate(pipeline))

# =======================
# Query processing
# =======================
def run_structured_query(coll: Collection, spec: Dict[str, Any]) -> pd.DataFrame:
    mode = spec.get("mode")
    filt = spec.get("filter") or {}
    proj = spec.get("projection")
    srt = spec.get("sort")
    lim = spec.get("limit") or 200

    if mode == "distinct" and spec.get("distinctField"):
        field = spec["distinctField"]
        vals = coll.distinct(field, filter=filt)
        df = pd.DataFrame({field: vals})
        return df

    cursor = coll.find(filt, projection=proj)
    if srt:
        cursor = cursor.sort(srt["field"], srt["direction"])
    cursor = cursor.limit(lim)
    rows = list(cursor)

    # Flatten nested keys for readability
    def flatten(d: Dict[str, Any], parent: str = "", sep: str = ".") -> Dict[str, Any]:
        items = []
        for k, v in d.items():
            new_key = f"{parent}{sep}{k}" if parent else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    flat_rows = [flatten({k: v for k, v in r.items() if k != "_id"}) for r in rows]
    df = pd.DataFrame(flat_rows)
    return df

# =======================
# Streamlit setup
# =======================
st.set_page_config(page_title="Mongo RAG Chatbot", page_icon="📚", layout="wide")

st.title("📚 MongoDB RAG Chatbot")
st.caption("Ask questions or request structured lists/filters. Example: **list out the telecaller name**")

client = get_mongo()
coll = get_collection(client, DEFAULT_DB, DEFAULT_COLL)

user_msg = st.chat_input("Type your question… e.g., list out the telecaller name")

if user_msg:
    st.session_state.history.append(("user", user_msg))
    # Run vector search if the query is structured
    query_vec = get_embedder().embed_query(user_msg)  # Update with your embedding logic
    matches = atlas_vector_search(coll, query_vec, k=5)

    # Output the result
    st.write(matches)  # Show matched documents in the UI as needed
