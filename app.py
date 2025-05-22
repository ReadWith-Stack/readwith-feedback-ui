import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# --- Load OpenAI key securely from Streamlit secrets ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide")
st.title("ReadWith: Feedback Collector")

# --- State management ---
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

# --- Main Layout with Two Columns ---
left_col, right_col = st.columns([3, 1])

# --- Left Column: Chat Display ---
with left_col:
    if st.session_state.ai_response:
        st.subheader("💬 You asked:")
        st.markdown(f"> {st.session_state.user_input}")

        st.subheader("📘 AI Response")
        st.write(st.session_state.ai_response)

# --- Right Column: Feedback Tools (Aligned to Top) ---
with right_col:
    if st.session_state.ai_response:
        st.subheader("📝 Feedback")
        good = st.button("👍 Good", key="good")
        bad = st.button("👎 Needs Work", key="bad")
        written_feedback = st.text_area("Optional comment", key="feedback")
        if st.button("Submit Feedback", key="submit_feedback"):
            feedback_type = "Good" if good else "Needs Work" if bad else "Unrated"
            timestamp = datetime.now().isoformat()
            feedback_data = {
                "timestamp": timestamp,
                "user_input": st.session_state.user_input,
                "ai_response": st.session_state.ai_response,
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

# --- Message Input (Always at Bottom) ---
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
            st.session_state.user_input = new_input
            st.session_state.ai_response = response.choices[0].message.content
        except Exception as e:
            st.session_state.ai_response = f"⚠️ Error: {str(e)}"
