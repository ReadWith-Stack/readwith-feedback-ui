import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime
import uuid

# --- Setup ---
st.set_page_config(page_title="ReadWith Test", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Session Variables ---
if "user_message" not in st.session_state:
    st.session_state.user_message = None
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- UI Title ---
st.title("📘 ReadWith: MVP Test (One-Turn Chat + Feedback)")

# --- Chat Input ---
user_input = st.chat_input("Ask ReadWith something about The Priory of the Orange Tree")

if user_input:
    st.session_state.user_message = user_input
    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a warm, witty, and insightful book discussion companion."},
                {"role": "user", "content": user_input}
            ]
        )
        st.session_state.ai_response = response.choices[0].message.content

# --- Display Messages ---
if st.session_state.user_message:
    st.markdown("#### You:")
    st.markdown(f"<div style='background-color:#DCEBFF; padding:10px; border-radius:10px;'>{st.session_state.user_message}</div>", unsafe_allow_html=True)

if st.session_state.ai_response:
    st.markdown("#### ReadWith:")
    st.markdown(f"<div style='background-color:#F0F0F0; padding:10px; border-radius:10px;'>{st.session_state.ai_response}</div>", unsafe_allow_html=True)

# --- Feedback Section ---
if st.session_state.ai_response:
    st.markdown("---")
    st.subheader("📝 Feedback")

    col1, col2 = st.columns(2)
    with col1:
        upvote = st.button("👍", key="thumbs_up")
    with col2:
        downvote = st.button("👎", key="thumbs_down")

    comment = st.text_area("Comment", height=80)
    submit = st.button("Submit Feedback")

    if submit:
        feedback = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": st.session_state.session_id,
            "user_message": st.session_state.user_message,
            "ai_response": st.session_state.ai_response,
            "rating": "up" if upvote else "down" if downvote else "none",
            "comment": comment,
            "status": "pending"
        }

        df = pd.DataFrame([feedback])
        df.to_csv("feedback_log.csv", mode="a", header=not pd.io.common.file_exists("feedback_log.csv"), index=False)

        st.success("✅ Feedback submitted.")
