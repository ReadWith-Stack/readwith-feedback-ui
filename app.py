import streamlit as st
from openai import OpenAI
from datetime import datetime
import uuid
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np

# --- Setup ---
st.set_page_config(page_title="ReadWith Chat", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Embedding model ---
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Helper functions ---
def load_system_prompt():
    with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

def embed_text(text):
    return embedding_model.encode(text).tolist()

def retrieve_relevant_chunks(query_text, top_k=5, threshold=0.75):
    embedded_query = embed_text(query_text)
    result = supabase.rpc("match_documents", {
        "query_embedding": embedded_query,
        "match_threshold": threshold,
        "match_count": top_k
    }).execute()
    if result.data:
        return [item["content"] for item in result.data]
    return []

# --- Session Setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Title ---
st.markdown("<h3>ReadWith: AI Testing & Feedback</h3>", unsafe_allow_html=True)
st.markdown("<h5>Book: The Priory of The Orange Tree</h5>", unsafe_allow_html=True)

# --- Chat Input ---
user_input = st.chat_input("Your Message")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Retrieve RAG context
    context_chunks = retrieve_relevant_chunks(user_input, top_k=5, threshold=0.75)
    context_text = "\n\n".join(context_chunks)
    context_system_message = f"You may use the following book context to answer the question:\n\n{context_text}"

    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": load_system_prompt()},
                {"role": "system", "content": context_system_message}
            ] + st.session_state.messages
        )
        ai_message = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

    # --- Debug: Show retrieved context chunks ---
if "context_chunks" in locals():
    st.markdown("### 🔍 Retrieved Context Chunks")
    if context_chunks:
        for chunk in context_chunks:
            st.markdown(f"- {chunk}")
    else:
        st.info("⚠️ No context chunks retrieved for this query. The RAG system returned zero results.")

st.markdown("---")
