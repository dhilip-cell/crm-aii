import streamlit as st
from pymongo import MongoClient
from pymongo.collection import Collection
import os
import json

# ==============================
# Configuration (edit to suit)
# ==============================
DEFAULT_DB = os.getenv("DB_NAME", "test")
DEFAULT_COLL = os.getenv("COLLECTION_NAME", "baffle_collection")
USE_ATLAS_VECTOR = os.getenv("USE_ATLAS_VECTOR", "1") == "1"
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "rag_vector_index")

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
# Chatbot Interface
# =======================
st.set_page_config(page_title="CRM Assistant", page_icon="📚", layout="wide")

# Add a header
st.markdown(
    """
    <style>
    #header {
        background: #0D333F;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
    #header h1 {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div id="header"><h1>CRM Assistant</h1></div>', unsafe_allow_html=True)

# Chatbox UI setup
if "history" not in st.session_state:
    st.session_state.history = []  # History for chat messages

# Display previous messages
for message in st.session_state.history:
    sender = message["sender"]
    text = message["message"]
    if sender == "user":
        st.markdown(f'<div style="background-color: #33B04A; color: white; padding: 12px 14px; border-radius: 12px; margin: 6px 0; text-align: right;">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background-color: #dcd9e6; color: black; padding: 12px 14px; border-radius: 12px; margin: 6px 0; text-align: left;">{text}</div>', unsafe_allow_html=True)

# Input box and button
input_text = st.text_input("Ask me anything...")

if st.button("Send"):
    if input_text:
        # User message
        st.session_state.history.append({"sender": "user", "message": input_text})

        # Bot response (this is where your logic for querying MongoDB will go)
        bot_response = get_bot_response(input_text)

        # Adding bot response
        st.session_state.history.append({"sender": "bot", "message": bot_response})

        # Clear the input field
        st.text_input("Ask me anything...", value="", key="new_input")

        # Scroll to the bottom
        st.experimental_rerun()

# =======================
# MongoDB Vector Search Logic (Example Placeholder)
# =======================
def atlas_vector_search(query: str) -> str:
    # Placeholder MongoDB vector search logic
    # Replace with actual logic for your vector search (e.g., Atlas vector search)
    return f"Mock response for: {query}"

# =======================
# Custom Logic for Processing Chat Inputs
# =======================
def get_bot_response(user_query: str) -> str:
    # You can replace this with actual MongoDB search or any other logic.
    return atlas_vector_search(user_query)

# =======================
# Interactivity Enhancements
# =======================
# You can add more interactivity and refine the chatbot further. For example, adding more buttons or customizing the message formats.
