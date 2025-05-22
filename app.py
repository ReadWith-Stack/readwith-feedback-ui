import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# --- Load OpenAI key securely from Streamlit secrets ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide")
st.title("ReadWith: Feedback Collector")

# --- State management for multi-turn chat ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Layout: Left (chat), Right (feedback) ---
left_col, right_col = st.columns([3, 1])

# --- Left Column: Chat Bubbles ---
with left_col:
    st.subheader("💬 Conversation")
    for i, turn in enumerate(st.session_state.chat_history):
        with st.container():
            # User message (right-aligned)
            st.markdown(
                f"""
                <div style="text-align: right; background-color: #e6f7ff; padding: 10px; border-radius: 10px; margin-bottom: 5px;">
                    <strong>You:</strong> {turn['user']}
                </div>
                """, unsafe_allow_html=True)

            # AI response (left-aligned)
            st.markdown(
                f"""
                <div style="text-align: left; background-color: #f9f9f9; padding: 10px; border-radius: 10px; margin-bottom: 20px;">
                    <strong>ReadWith:</strong> {turn['ai']}
                </div>
                """, unsafe_allow_html=True)

# --- Right Column: Feedback on latest AI message ---
with right_col:
    if st.session_state.chat_history:
        st.subheader("📝 Feedback")
        good = st.button("👍 Good", key="good")
        bad = st.button("👎 Needs Work", key="bad")
        written_feedback = st.text_area("Optional comment", key="feedback")

        if st.button("Submit Feedback", key="submit_feedback"):
            latest = st.session_state.chat_history[-1]
            feedback_type = "Good" if good else "Needs Work" if bad else "Unrated"
            timestamp = datetime.now().isoformat()
            feedback_data = {
                "timestamp": timestamp,
                "user_input": latest['user'],
                "ai_response": latest['ai'],
                "rating": feedback_type,
                "comment": written_feedback
            }
            try:
                df = pd.read_csv("feedback_log.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=["timestamp", "user_input", "ai_response", "rating", "comment"])
            df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
            df.to_csv("feedback_log.csv", index=False)
            st.success("✅ Feedback submitted!")

# --- Message input area ---
st.markdown("---")
st.subheader("💬 Start a New Message")
with st.form("message_form", clear_on_submit=True):
    new_input = st.text_input("Type your message here:", key="message_input")
    submitted = st.form_submit_button("Submit Message")

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
            st.session_state.chat_history.append({"user": new_input, "ai": ai_reply})
        except Exception as e:
            st.session_state.chat_history.append({"user": new_input, "ai": f"⚠️ Error: {str(e)}"})
