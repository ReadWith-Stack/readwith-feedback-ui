import streamlit as st
import pandas as pd
from datetime import datetime
import openai

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .feedback-buttons-row button {
        margin-right: 10px;
    }
    .thumb-selected {
        border: 2px solid;
        font-weight: bold;
    }
    .thumb-up-selected {
        border-color: green;
    }
    .thumb-down-selected {
        border-color: red;
    }
    .submit-message-btn button:hover {
        font-weight: bold !important;
        color: black !important;
    }
    textarea {
        height: 60px !important;
    }
    .chat-bubble {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        width: fit-content;
        max-width: 100%;
    }
    .chat-bubble-left {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 30px;
        width: fit-content;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("ReadWith: Feedback Collector")
st.caption("📖 Focused on: *The Priory of the Orange Tree*")

# --- Initialize state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "feedback_state" not in st.session_state:
    st.session_state.feedback_state = []

# --- Message Input FIRST to ensure immediate update after submit ---
st.markdown("---")
st.subheader("💬 Start a New Message")
with st.form("message_form", clear_on_submit=True):
    new_input = st.text_input("Type your message here:", key="message_input")
    submitted = st.form_submit_button("Submit Message", help="Click or press Enter", type="primary")

if submitted and new_input:
    with st.spinner("Thinking..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are ReadWith, a warm, witty and insightful literary conversation partner. Speak conversationally, referencing the book if needed."
                    },
                    {
                        "role": "user",
                        "content": new_input
                    }
                ]
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            ai_reply = f"⚠️ Error: {str(e)}"

    # Add both turn and empty feedback record
    st.session_state.chat_history.append({"user": new_input, "ai": ai_reply})
    st.session_state.feedback_state.append({"thumb": None, "comment": ""})

# --- Chat + Feedback Display ---
for i, turn in enumerate(st.session_state.chat_history):
    cols = st.columns([3, 1])

    with cols[0]:
        st.markdown(
            f"""<div class="chat-bubble" style="text-align: right;"><strong>You:</strong> {turn['user']}</div>""",
            unsafe_allow_html=True
        )
        st.markdown(
            f"""<div class="chat-bubble-left" style="text-align: left;"><strong>ReadWith:</strong> {turn['ai']}</div>""",
            unsafe_allow_html=True
        )

    with cols[1]:
        feedback = st.session_state.feedback_state[i]
        thumb = feedback["thumb"]

        thumb_col1, thumb_col2 = st.columns(2)
        with thumb_col1:
            if st.button("👍", key=f"thumb_up_{i}"):
                feedback["thumb"] = "up"
        with thumb_col2:
            if st.button("👎", key=f"thumb_down_{i}"):
                feedback["thumb"] = "down"

        thumb_up_class = "thumb-selected thumb-up-selected" if feedback["thumb"] == "up" else ""
        thumb_down_class = "thumb-selected thumb-down-selected" if feedback["thumb"] == "down" else ""

        st.markdown(
            f"""
            <div class="feedback-buttons-row">
                <button class="{thumb_up_class}">👍</button>
                <button class="{thumb_down_class}">👎</button>
            </div>
            """,
            unsafe_allow_html=True
        )

        comment = st.text_area("Comment", value=feedback["comment"], key=f"comment_{i}", max_chars=500)
        feedback["comment"] = comment

        if st.button("Submit Feedback", key=f"submit_feedback_{i}"):
            feedback_data = {
                "timestamp": datetime.now().isoformat(),
                "turn": i + 1,
                "user_input": turn["user"],
                "ai_response": turn["ai"],
                "rating": feedback["thumb"] or "Unrated",
                "comment": comment
            }
            try:
                df = pd.read_csv("feedback_log.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=["timestamp", "turn", "user_input", "ai_response", "rating", "comment"])
            df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
            df.to_csv("feedback_log.csv", index=False)
            st.success(f"✅ Feedback for Turn {i+1} saved!")
