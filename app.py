import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# --- Load OpenAI key securely from Streamlit secrets ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("ReadWith: Feedback Collector")

# --- User prompt input ---
st.subheader("💬 Start a Conversation with ReadWith")
user_input = st.text_input("Your message:")

ai_response = ""

# --- Get AI response if message submitted ---
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

# --- Display response and feedback tools ---
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

    # --- New: Submit Feedback Button ---
    if st.button("Submit Feedback"):
        feedback_type = "Good" if good else "Needs Work" if bad else "Unrated"
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
        st.success("✅ Feedback submitted!")

elif not user_input:
    st.write("👆 Type a message to begin a conversation.")
