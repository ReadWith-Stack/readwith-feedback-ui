import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# --- Load OpenAI key securely from Streamlit secrets ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide")
st.title("ReadWith: Feedback Collector")
st.caption("📖 Focused on: *The Priory of the Orange Tree*")

# --- State for multi-turn chat ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Message Input Area (submit before rendering chat) ---
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
        except Exception as e:
            ai_reply = f"⚠️ Error: {str(e)}"

    # Append to chat history immediately
    st.session_state.chat_history.append({"user": new_input, "ai": ai_reply})

# --- Display Chat Interface with In-line Feedback ---
st.subheader("Conversation and Feedback")

for i, turn in enumerate(st.session_state.chat_history):
    chat_col, feedback_col = st.columns([3, 1])

    with chat_col:
        st.markdown(
            f"""
            <div style="text-align: right; background-color: #e6f7ff; padding: 10px; border-radius: 10px; margin-bottom: 5px;">
                <strong>You:</strong> {turn['user']}
            </div>
            """, unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="text-align: left; background-color: #f9f9f9; padding: 10px; border-radius: 10px; margin-bottom: 5px;">
                <strong>ReadWith:</strong> {turn['ai']}
            </div>
            """, unsafe_allow_html=True)

    with feedback_col:
        st.markdown("**Feedback**")
        good = st.button("👍", key=f"good_{i}")
        bad = st.button("👎", key=f"bad_{i}")
        written_feedback = st.text_area("Comment", key=f"feedback_{i}", label_visibility="collapsed", placeholder="Add a comment...")

        if st.button("Submit Feedback", key=f"submit_feedback_{i}"):
            feedback_type = "Good" if good else "Needs Work" if bad else "Unrated"
            timestamp = datetime.now().isoformat()
            feedback_data = {
                "timestamp": timestamp,
                "turn": i + 1,
                "user_input": turn['user'],
                "ai_response": turn['ai'],
                "rating": feedback_type,
                "comment": written_feedback
            }

            try:
                df = pd.read_csv("feedback_log.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=["timestamp", "turn", "user_input", "ai_response", "rating", "comment"])

            df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
            df.to_csv("feedback_log.csv", index=False)
            st.success(f"✅ Feedback saved for Turn {i+1}")
