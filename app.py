import streamlit as st
from supabase import create_client
from datetime import datetime
from openai import OpenAI
import uuid
import os

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Load system prompt
with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "rerun" not in st.session_state:
    st.session_state.rerun = False
if "feedback_rating" not in st.session_state:
    st.session_state.feedback_rating = None

# App layout
st.set_page_config(page_title="ReadWith - Book Sage", layout="wide")
col1, col2 = st.columns([3, 1])

# Conversation area
with col1:
    st.title("📚 Book Sage")
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        align = "user" if role == "user" else "assistant"
        with st.chat_message(align):
            st.markdown(content)

    user_input = st.chat_input("Ask about the book…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}] +
                     st.session_state.messages,
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

        st.session_state.rerun = True

# Feedback area
with col2:
    st.header("📬 Feedback")
    if st.session_state.messages:
        last_user_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        last_ai_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "")

        st.write("Was this helpful?")
        feedback_col = st.columns(2)
        with feedback_col[0]:
            if st.button("👍", key="thumbs_up"):
                st.session_state.feedback_rating = "approve"
        with feedback_col[1]:
            if st.button("👎", key="thumbs_down"):
                st.session_state.feedback_rating = "reject"

        comment = st.text_area("Leave a comment (optional)", key="comment_box")
        rewrite = st.text_area("Rewrite the AI response (optional)", key="rewrite_box")

        # If rewrite is provided, override thumb choice
        feedback_decision = (
            "rewrite" if rewrite.strip() else st.session_state.feedback_rating
        )

        if st.button("Submit Feedback"):
            if feedback_decision:
                feedback_data = {
                    "session_id": st.session_state.session_id,
                    "prompt": last_user_msg,
                    "ai_response": last_ai_msg,
                    "rating": feedback_decision,
                    "comment": comment,
                    "rewrite": rewrite,
                    "timestamp": datetime.utcnow().isoformat()
                }
                try:
                    supabase.table("feedback").insert(feedback_data).execute()
                    st.success("✅ Feedback submitted.")
                except Exception as e:
                    st.error(f"❌ Failed to save feedback: {e}")

                trainer_log = {
                    "session_id": st.session_state.session_id,
                    "prompt": last_user_msg,
                    "ai_response": last_ai_msg,
                    "user_rewrite": rewrite if rewrite else None,
                    "decision": feedback_decision,
                    "timestamp": datetime.utcnow().isoformat()
                }
                try:
                    supabase.table("trainer_logs").insert(trainer_log).execute()
                    st.info("🧠 Trainer log recorded.")
                except Exception as e:
                    st.warning(f"⚠️ Trainer log failed: {e}")

                # Reset rating and trigger rerun
                st.session_state.feedback_rating = None
                st.session_state.rerun = True
            else:
                st.warning("Please select a thumbs up/down or provide a rewrite before submitting.")

# Rerun if needed
if st.session_state.get("rerun"):
    st.session_state.rerun = False
    st.rerun()
