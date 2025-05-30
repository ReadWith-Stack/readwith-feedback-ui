import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# --- Setup ---
st.set_page_config(page_title="Trainer AI UI", layout="wide")

# --- Supabase connection ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Load trainer logs from Supabase ---
@st.cache_data
def load_trainer_logs():
    response = supabase.table("trainer_logs").select("*").order("timestamp", desc=True).execute()  # PATCHED: Now newest first
    return response.data if response.data else []

raw_logs = load_trainer_logs()

# --- Filter: Show only unreviewed entries ---
show_unreviewed_only = st.sidebar.checkbox("🔍 Show only entries needing review", value=True)

if show_unreviewed_only:
    trainer_logs = [log for log in raw_logs if not log.get("trainer_rewrite") and not log.get("decision")]
else:
    trainer_logs = raw_logs

if not trainer_logs:
    st.warning("No entries match the current filter.")
    st.stop()

# --- Session state for navigation ---
if "turn_index" not in st.session_state:
    st.session_state.turn_index = 0
st.session_state.turn_index = max(0, min(st.session_state.turn_index, len(trainer_logs) - 1))

# --- Navigation buttons ---
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if st.button("⬅ Prev", disabled=st.session_state.turn_index == 0):
        st.session_state.turn_index -= 1
with col3:
    if st.button("Next ➡", disabled=st.session_state.turn_index >= len(trainer_logs) - 1):
        st.session_state.turn_index += 1

current = trainer_logs[st.session_state.turn_index]
st.markdown(f"### Turn {st.session_state.turn_index + 1} of {len(trainer_logs)}")

# --- Layout: side-by-side columns ---
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 📘 Prompt")
    st.code(current["prompt"], language="markdown")

    st.markdown("#### 🤖 AI Response")
    st.code(current["ai_response"], language="markdown")

with right_col:
    st.markdown("#### ✍️ User Rewrite (if provided)")
    st.code(current.get("user_rewrite", "—"), language="markdown")

    st.markdown("#### 📝 Your Rewrite")
    trainer_rewrite = st.text_area("Edit or enter your version:", value=current.get("user_rewrite", ""), height=200)

# --- Trainer decision area ---
st.markdown("#### ❤️ Which version is better?")
decision = st.radio("Your judgment", options=["AI Response", "Your Rewrite", "Neither"], key=f"decision_{st.session_state.turn_index}")

notes = st.text_input("Optional notes (context, reasoning, style comments):", key=f"notes_{st.session_state.turn_index}")

# --- Save button ---
if st.button("💾 Save Trainer Decision"):
    log_entry = {
        "session_id": current.get("session_id", "anonymous"),
        "prompt": current["prompt"],
        "ai_response": current["ai_response"],
        "user_rewrite": current.get("user_rewrite", ""),
        "trainer_rewrite": trainer_rewrite,
        "decision": decision,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        supabase.table("trainer_logs").insert(log_entry).execute()
        st.success("✅ Trainer decision saved!")
    except Exception as e:
        st.error(f"❌ Failed to save decision: {e}")

# --- CSV Export of Reviewed Logs ---
st.sidebar.markdown("---")
if st.sidebar.button("📤 Export reviewed trainer logs to CSV"):
    reviewed = [log for log in raw_logs if log.get("trainer_rewrite") or log.get("decision")]
    if reviewed:
        df = pd.DataFrame(reviewed)
        st.sidebar.download_button("Download CSV", df.to_csv(index=False), file_name="reviewed_trainer_logs.csv")
    else:
        st.sidebar.warning("No reviewed logs available to export.")
