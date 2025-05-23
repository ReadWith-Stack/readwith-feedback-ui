import streamlit as st
from datetime import datetime
import pandas as pd
import openai
import uuid

# --- Configuration ---
st.set_page_config(page_title="ReadWith Chat", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Session State Setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Feedback Logging ---
FEEDBACK_LOG = "feedback_log.csv"

def save_feedback(message, response, rating, comment):
    feedback_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": st.session_state.session_id,
        "user_message": message,
        "ai_response": response,
        "rating": rating,
        "comment": comment,
        "status": "pending"
    }
    df = pd.DataFrame([feedback_entry])
    df.to_csv(FEEDBACK_LOG, mode='a', header=not pd.io.common.file_exists(FEEDBACK_LOG), index=False)

# --- Chat Function ---
def get_ai_response(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a thoughtful book discussion companion."}] +
                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages] +
                 [{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return completion.choices[0].message["content"]

# --- Layout ---
left_col, right_col = st.columns([4, 1])

with left_col:
    st.markdown("### 📚 ReadWith: *The Priory of the Orange Tree*")
    for i, message in enumerate(st.session_state.messages):
        role = message["role"]
        align = "right" if role == "user" else "left"
        bg = "#DCEBFF" if role == "user" else "#F0F0F0"
        st.markdown(
            f"<div style='background-color:{bg}; padding:8px; border-radius:10px; margin:4px 0; text-align:{align}; max-width:90%;'>{message['content']}</div>",
            unsafe_allow_html=True
        )

    # --- Chat Input ---
    if prompt := st.chat_input("What would you like to ask ReadWith?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.feedback[len(st.session_state.messages) - 1] = {"rating": None, "comment": ""}

with right_col:
    st.markdown("### Feedback")

    # Feedback only on AI responses
    for i in range(1, len(st.session_state.messages), 2):
        message = st.session_state.messages[i]
        msg_id = i

        st.markdown(f"#### Response {msg_id // 2 + 1}")
        thumbs_col1, thumbs_col2 = st.columns(2)
        with thumbs_col1:
            if st.button("👍", key=f"up_{msg_id}"):
                st.session_state.feedback[msg_id]["rating"] = "up"
        with thumbs_col2:
            if st.button("👎", key=f"down_{msg_id}"):
                st.session_state.feedback[msg_id]["rating"] = "down"

        comment = st.text_area(
            "Comment",
            key=f"comment_{msg_id}",
            height=60,
            value=st.session_state.feedback[msg_id].get("comment", "")
        )
        st.session_state.feedback[msg_id]["comment"] = comment

        if st.button("Submit Feedback", key=f"submit_{msg_id}"):
            data = st.session_state.feedback[msg_id]
            user_msg = st.session_state.messages[msg_id - 1]["content"]
            ai_msg = message["content"]
            save_feedback(user_msg, ai_msg, data["rating"], data["comment"])
            st.success("✅ Feedback submitted")

