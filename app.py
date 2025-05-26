import streamlit as st
from supabase import create_client
from datetime import datetime
from openai import OpenAI
import uuid
import os

# Environment variables (ensure these are set in Streamlit Cloud or locally)
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

        # Call OpenAI with system prompt + history
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}] +
                     st.session_state.messages,
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

        st.experimental_rerun()

# Feedback area
with col2:
    st.header("📬 Feedback")
    if st.session_state.messages:
        last_user_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        last_ai_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "")

        # Thumbs selection
        st.write("Was this helpful?")
        feedback_col = st.columns(2)
        with feedback_col[0]:
            thumbs_up = st.button("👍", key="thumbs_up")
        with feedback_col[1]:
            thumbs_down = st.button("👎", key="thumbs_down")

        # Comment box
        comment = st.text_area("Leave a comment (optional)", key="comment_box")

        # Rewrite field
        rewrite = st.text_area("Rewrite the AI response (optional)", key="rewrite_box")

        # Determine feedback decision
        feedback_decision = None
        if thumbs_up:
            feedback_decision = "approve"
        elif thumbs_down:
            feedback_decision = "reject"
        elif rewrite.strip():
            feedback_decision = "rewrite"

        if feedback_decision:
            # Store in feedback table
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

            # Also store in trainer_logs table
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

            st.experimental_rerun()
