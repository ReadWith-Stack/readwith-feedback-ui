import streamlit as st
import pandas as pd
from datetime import datetime

st.title("ReadWith: Feedback Collector")

ai_response = "This is a sample response from the ReadWith AI. What do you think?"
st.subheader("📘 AI Response")
st.write(ai_response)

st.subheader("📝 Your Feedback")
col1, col2 = st.columns(2)
with col1:
    good = st.button("👍 Good")
with col2:
    bad = st.button("👎 Needs Work")

written_feedback = st.text_area("Optional: Add any comments or suggestions")

if good or bad:
    feedback_type = "Good" if good else "Needs Work"
    timestamp = datetime.now().isoformat()
    new_feedback = {
        "timestamp": timestamp,
        "response": ai_response,
        "rating": feedback_type,
        "comment": written_feedback
    }

    try:
        df = pd.read_csv("feedback_log.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["timestamp", "response", "rating", "comment"])

    df = pd.concat([df, pd.DataFrame([new_feedback])], ignore_index=True)
    df.to_csv("feedback_log.csv", index=False)
    st.success("✅ Feedback saved!")
