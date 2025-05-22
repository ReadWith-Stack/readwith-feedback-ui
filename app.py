import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# Use API key securely stored in Streamlit Cloud's secret manager
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("ReadWith: Feedback Collector & AI Chat")

# --- Conversation prompt input ---
st.subheader("💬 Start a Conversation with ReadWith")
user_input = st.text_input("Your message:", "")

# --- Get AI response when user submits ---
ai_response = ""
if user_input:
    with st.spinner("Thinking..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are ReadWith, a warm, witty and insightful literary conversation partner. Answer like a friend who's read the book, offering reflections and inviting conversation."},
                    {"role": "user", "content": user_input}
                ]
            )
            ai_response = response['choices'][0]['message']['content']
        except Exception as e:
            ai_response = f"⚠️ Error: {str(e)}"

# --- Display AI response ---
if ai_response:
    st.subheader("📘 AI Response")
    st.write(ai_response)

    # --- Feedback section ---
    st.subheader("📝 Your Feedback")
    col1, col2 = st.columns(2)
    with col1:
        good = st.button("👍 Good", key="good")
    with col2:
        bad = st.button("👎 Needs Work", key="bad")

    written_feedback = st.text_area("Optional: Add any comments or suggestions", key="feedback")

    if good or bad:
        feedback_type = "Good" if good else "Needs Work"
        timestamp = datetime.now().isoformat()
        feedback_data = {
            "timestamp": timestamp,
            "user_input": user_input,
            "ai_response": ai_response,
            "rating": feedback_type,
            "comment": written_feedback
        }

        try:
            df = pd.read_csv("feedback_log.csv")
        except FileNotFoundError:
            df = pd.DataFrame(columns=["timestamp", "user_input", "ai_response", "rating", "comment"])

        df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
        df.to_csv("feedback_log.csv", index=False)
        st.success("✅ Feedback saved!")
