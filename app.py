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
if "feedback_ratings" not in st.session_state:
    st.session_state.feedback_ratings = {}

# App layout
st.set_page_config(page_title="ReadWith - Book Sage", layout="wide")

st.title("📚 Book Sage")

# Capture turns: user followed by assistant
turns = []
for i in range(0, len(st.session_state.messages) - 1):
    if st.session_state.messages[i]["role"] == "user" and st.session_state.messages[i + 1]["role"] == "assistant":
        turns.append((i, st.session_state.messages[i], st.session_state.messages[i + 1]))

# Render each turn as its own visual block
for turn_index, user_msg, ai_msg in turns:
    key_base = f"turn_{turn_index}"
    with st.container():
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1], gap="large")

        with col1:
            with st.chat_message("user"):
                st.markdown(user_msg["content"])
            with st.chat_message("assistant"):
                st.markdown(ai_msg["content"])

        with col2:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("👍", key=f"thumbs_up_{key_base}"):
                    st.session_state.feedback_ratings[key_base] = "approve"
            with col_b:
                if st.button("👎", key=f"thumbs_down_{key_base}"):
                    st.session_state.feedback_ratings[key_base] = "reject"

            comment = st.text_area("Leave a comment (optional)", key=f"comment_{key_base}")
            rewrite = st.text_area("Rewrite the AI response (optional)", key=f"rewrite_{key_base}")

            feedback_decision = (
                "rewrite" if rewrite.strip() else st.session_state.feedback_ratings.get(key_base)
            )

            if st.button("Submit Feedback", key=f"submit_{key_base}"):
                if feedback_decision:
                    feedback_data = {
    "session_id": st.session_state.get("session_id", "anonymous"),
    "prompt": user_msg["content"],
    "ai_response": ai_msg["content"],
    "rating": feedback_decision,
    "comment": comment,
    "rewrite": rewrite,
    "timestamp": datetime.utcnow().isoformat(),
    "status": "pending",
    "turn_index": turn_index
}

                    }
                    try:
                        supabase.table("feedback").insert(feedback_data).execute()
                        st.success("✅ Feedback submitted.")
                    except Exception as e:
                        st.error(f"❌ Failed to save feedback: {e}")

                    trainer_log = {
                        "session_id": st.session_state.session_id,
                        "prompt": user_msg["content"],
                        "ai_response": ai_msg["content"],
                        "user_rewrite": rewrite if rewrite else None,
                        "decision": feedback_decision,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    try:
                        supabase.table("trainer_logs").insert(trainer_log).execute()
                        st.info("🧠 Trainer log recorded.")
                    except Exception as e:
                        st.warning(f"⚠️ Trainer log failed: {e}")

                    st.session_state.rerun = True
                else:
                    st.warning("Please select a thumbs up/down or provide a rewrite before submitting.")

# New user input
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

# Rerun if needed
if st.session_state.get("rerun"):
    st.session_state.rerun = False
    st.rerun()
