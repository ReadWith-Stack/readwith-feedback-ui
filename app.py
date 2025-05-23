import streamlit as st
import openai
import pandas as pd
from datetime import datetime

# --- Setup ---
st.set_page_config(page_title="ReadWith AI", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Session State Init ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}

# --- CSS Styling ---
st.markdown("""
    <style>
        .user-bubble {
            background-color: #D0E8FF;
            padding: 12px;
            border-radius: 15px;
            max-width: 90%;
            margin-left: auto;
            text-align: right;
        }
        .ai-bubble {
            background-color: #F0F0F0;
            padding: 12px;
            border-radius: 15px;
            max-width: 90%;
            margin-right: auto;
            text-align: left;
        }
        .thumb-button {
            border: 2px solid #DDD;
            border-radius: 8px;
            padding: 6px 12px;
            margin-right: 8px;
            font-size: 18px;
            cursor: pointer;
        }
        .thumb-selected-up {
            border-color: green;
            transform: scale(1.1);
        }
        .thumb-selected-down {
            border-color: red;
            transform: scale(1.1);
        }
        .feedback-box textarea {
            height: 60px !important;
        }
        .submit-button:hover {
            font-weight: bold;
            color: black !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Layout ---
left_col, right_col = st.columns([3, 1], gap="large")

# --- Chat History ---
with left_col:
    st.markdown("### 📖 ReadWith Chat — *The Priory of the Orange Tree*")
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# --- Feedback for latest AI message ---
if any(m["role"] == "assistant" for m in st.session_state.messages):
    latest_ai_msg = [m for m in reversed(st.session_state.messages) if m["role"] == "assistant"][0]
    index = st.session_state.messages.index(latest_ai_msg)

    with right_col:
        st.markdown("### Feedback")
        fb = st.session_state.feedback.get(index, {"rating": None, "comment": ""})

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("👍", key="thumb_up"):
                fb["rating"] = "up"
        with col2:
            if st.button("👎", key="thumb_down"):
                fb["rating"] = "down"

        up_class = "thumb-button thumb-selected-up" if fb["rating"] == "up" else "thumb-button"
        down_class = "thumb-button thumb-selected-down" if fb["rating"] == "down" else "thumb-button"
        st.markdown(f'<div style="display:flex;"><div class="{up_class}">👍</div><div class="{down_class}">👎</div></div>', unsafe_allow_html=True)

        fb["comment"] = st.text_area("Comment", value=fb.get("comment", ""), key="comment_box", help="What did you think of the response?", label_visibility="collapsed")
        if st.button("Submit Feedback", key="submit_feedback"):
            fb["timestamp"] = datetime.now().isoformat()
            fb["message"] = latest_ai_msg["content"]
            with open("feedback_log.csv", "a", encoding="utf-8") as f:
                f.write(f'"{fb["timestamp"]}","{fb["rating"]}","{fb["comment"]}","{fb["message"].replace(chr(10), " ")}"\n')
            st.success("Feedback submitted.")
        st.session_state.feedback[index] = fb

# --- Input ---
st.markdown("---")
user_input = st.text_input("Your message", key="input", label_visibility="collapsed")
if st.button("Submit Message"):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("ReadWith is replying..."):
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ai_msg = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": ai_msg})
        st.experimental_rerun()
