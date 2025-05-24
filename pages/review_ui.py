import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime
import uuid
from supabase import create_client, Client

# --- Streamlit + Supabase setup ---
st.set_page_config(page_title="ReadWith Chat", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SUPABASE_URL = "https://nwhsnymzihkqtlufiafu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Session setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Title ---
st.markdown("<h3>ReadWith: AI Testing & Feedback</h3>", unsafe_allow_html=True)
st.markdown("<h5>Book: The Priory of The Orange Tree</h5>", unsafe_allow_html=True)

# --- Chat input ---
user_input = st.chat_input("Your Message")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a warm, witty, and insightful book discussion companion."}
            ] + st.session_state.messages
        )
        ai_message = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

# --- Conversation + Feedback, turn-by-turn ---
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
