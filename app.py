import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# --- Set API key from Streamlit Secrets ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("ReadWith: Feedback Collector & AI Chat")

# --- User prompt input ---
st.subheader("💬 Start a Conversation with ReadWith")
user_input = st.text_input("Your message:", "")

ai_response = ""

# --- Submit and fetch AI reply ---
if user_input:
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
                        "content": user_input
                    }
                ]
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            ai_response = f"⚠️ Error: {str(e)}"

# --- Display AI response and feedback interface ---
if ai_response:
    st.subheader("📘 AI Response")
    st.write(ai_response)

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
            "



