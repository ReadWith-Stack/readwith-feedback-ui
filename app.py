import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime
import uuid
import os

# --- Setup ---
st.set_page_config(page_title="ReadWith Chat", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a warm, witty, and insightful book discussion companion."}
            ] + st.session_state.messages
        )
        ai_message = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

# --- Conversation & Feedback, turn-by-turn ---
for i in range(0, len(st.session_state.messages), 2):
    if i + 1 >= len(st.session_state.messages):
        break  # Skip if assistant message not yet present

    user_msg = st.session_state.messages[i]["content"]
    ai_msg = st.session_state.messages[i + 1]["content"]

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown(f"#### You:")
        st.markdown(f"<div style='background-color:#DCEBFF; padding:10px; border-radius:10px;'>{user_msg}</div>", unsafe_allow_html=True)

        st.markdown(f"#### ReadWith:")
        st.markdown(f"<div style='background-color:#F0F0F0; padding:10px; border-radius:10px;'>{ai_msg}</div>", unsafe_allow_html=True)

    with col2:
        turn_id = i + 1
        if turn_id not in st.session_state.feedback:
            st.session_state.feedback[turn_id] = {"rating": "none", "comment": ""}

        st.markdown("##### Feedback")
        feedback_row = st.columns([1, 1], gap="small")
        with feedback_row[0]:
            if st.button("👍", key=f"up_{turn_id}"):
                st.session_state.feedback[turn_id]["rating"] = "up"
        with feedback_row[1]:
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
            df = pd.DataFrame([feedback])
            df.to_csv("feedback_log.csv", mode="a", header=not os.path.exists("feedback_log.csv"), index=False)
            st.success("✅ Feedback submitted.")

# --- Chat input pinned to bottom ---
st.markdown("---")

# --- Download button under input ---
if os.path.exists("feedback_log.csv"):
    with open("feedback_log.csv", "rb") as f:
        st.download_button(
            label="📥 Download Feedback Log",
            data=f,
            file_name="feedback_log.csv",
            mime="text/csv"
        )
