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

# --- Turn-by-turn conversation + feedback ---
for i in range(0, len(st.session_state.messages), 2):
    if i + 1 >= len(st.session_state.messages):
        break

    user_msg = st.session_state.messages[i]["content"]
    ai_msg = st.session_state.messages[i + 1]["content"]
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("#### You:")
        st.markdown(f"<div style='background-color:#DCEBFF; padding:10px; border-radius:10px;'>{user_msg}</div>", unsafe_allow_html=True)
        st.markdown("#### ReadWith:")
        st.markdown(f"<div style='background-color:#F0F0F0; padding:10px; border-radius:10px;'>{ai_msg}</div>", unsafe_allow_html=True)

    with col2:
        turn_id = i + 1
        if turn_id not in st.session_state.feedback:
            st.session_state.feedback[turn_id] = {"rating": "none", "comment": ""}

        st.markdown("##### Feedback")
        thumbs = st.columns([1, 1], gap="small")
        with thumbs[0]:
            if st.button("👍", key=f"up_{turn_id}"):
                st.session_state.feedback[turn_id]["rating"] = "up"
        with thumbs[1]:
            if st.button("👎", key=f"down_{turn_id}"):
                st.session_state.feedback[turn_id]["rating"] = "down"

        st.session_state.feedback[turn_id]["comment"] = st.text_area(
            "Comment",
            key=f"comment_{turn_id}",
            value=st.session_state.feedback[turn_id]["comment"],
            height=80
        )

        if st.button("Submit Feedback", key=f"submit_{turn_id}"):
            feedback = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": st.session_state.session_id,
                "turn_index": turn_id,
                "user_message": user_msg,
                "ai_response": ai_msg,
                "rating": st.session_state.feedback[turn_id]["rating"],
                "comment": st.session_state.feedback[turn_id]["comment"],
                "status": "pending"
            }
            supabase.table("feedback").insert(feedback).execute()
            st.success("✅ Feedback submitted.")

st.markdown("---")
