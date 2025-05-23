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
    st.session_state.messages = []  # List of {"role": "user"/"assistant", "content": ...}
if "feedback" not in st.session_state:
    st.session_state.feedback = {}  # Dict with turn index as key
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- UI Title ---
st.title("📘 ReadWith: Multi-Turn Chat + Feedback")

# --- Chat Input ---
user_input = st.chat_input("Ask ReadWith something about The Priory of the Orange Tree")

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

# --- Display Conversation ---
for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    is_user = role == "user"
    bg = "#DCEBFF" if is_user else "#F0F0F0"
    align = "right" if is_user else "left"

    st.markdown(
        f"<div style='background-color:{bg}; padding:10px; border-radius:10px; margin:4px 0; text-align:{align}; max-width:90%;'>{msg['content']}</div>",
        unsafe_allow_html=True
    )

    # --- Feedback for AI Responses Only ---
    if role == "assistant":
        if idx not in st.session_state.feedback:
            st.session_state.feedback[idx] = {"rating": "none", "comment": ""}

        with st.container():
            st.markdown("##### 📝 Feedback")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍", key=f"thumbs_up_{idx}"):
                    st.session_state.feedback[idx]["rating"] = "up"
            with col2:
                if st.button("👎", key=f"thumbs_down_{idx}"):
                    st.session_state.feedback[idx]["rating"] = "down"

            st.session_state.feedback[idx]["comment"] = st.text_area(
                "Comment",
                value=st.session_state.feedback[idx]["comment"],
                height=80,
                key=f"comment_{idx}"
            )

            if st.button("Submit Feedback", key=f"submit_{idx}"):
                user_msg = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
                ai_msg = msg["content"]
                feedback = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": st.session_state.session_id,
                    "turn_index": idx,
                    "user_message": user_msg,
                    "ai_response": ai_msg,
                    "rating": st.session_state.feedback[idx]["rating"],
                    "comment": st.session_state.feedback[idx]["comment"],
                    "status": "pending"
                }
                df = pd.DataFrame([feedback])
                df.to_csv("feedback_log.csv", mode="a", header=not os.path.exists("feedback_log.csv"), index=False)
                st.success("✅ Feedback submitted.")

# --- CSV Preview ---
if os.path.exists("feedback_log.csv"):
    st.markdown("---")
    st.subheader("📄 Feedback Log Preview")
    df_log = pd.read_csv("feedback_log.csv")
    st.dataframe(df_log)
else:
    st.info("No feedback submitted yet. Provide feedback to start building the log.")
