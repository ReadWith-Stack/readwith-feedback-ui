import streamlit as st
st.set_page_config(page_title="Feedback Review UI", layout="wide")

from supabase import create_client, Client

# --- Supabase setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Admin login ---
st.markdown("### 🔐 Admin Login")
password = st.text_input("Enter admin password:", type="password")
if password != st.secrets.get("ADMIN_PASSWORD"):
    st.warning("Access restricted.")
    st.stop()

st.title("🗃️ Review Feedback Comments")

# --- Load all feedback from Supabase ---
with st.spinner("Loading feedback..."):
    response_all = supabase.table("feedback").select("*").order("timestamp", desc=True).execute()
    feedback_items = response_all.data if response_all.data else []

# --- Show summary counts ---
st.markdown("### 🧮 Feedback Summary")
status_counts = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}
for item in feedback_items:
    status = item.get("status", "pending")
    status_counts["total"] += 1
    if status in status_counts:
        status_counts[status] += 1

st.markdown(f"- **Total:** {status_counts['total']}")
st.markdown(f"- ✅ Approved:** {status_counts['approved']}")
st.markdown(f"- ❌ Rejected:** {status_counts['rejected']}")
st.markdown(f"- ⏳ Pending:** {status_counts['pending']}")

# --- Display feedback, grouped by status ---
if not feedback_items:
    st.success("✅ No feedback available.")
else:
    st.markdown("## ⏳ Pending Approval")
    for item in [i for i in feedback_items if i['status'] == 'pending']:
        with st.expander(f"Turn {item['turn_index']} - {item['timestamp']}", expanded=False):
            st.markdown(f"**Session ID:** {item['session_id']}")
            st.markdown(f"**User Message:** {item['user_message']}")
            st.markdown(f"**AI Response:** {item['ai_response']}")
            st.markdown(f"**Rating:** {item['rating']}")
            st.markdown(f"**Comment:** {item['comment']}")
            st.markdown(f"**Status:** {item['status']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{item['id']}"):
                    supabase.table("feedback").update({"status": "approved"}).eq("id", item["id"]).execute()
                    st.success("Approved!")
            with col2:
                if st.button("❌ Reject", key=f"reject_{item['id']}"):
                    supabase.table("feedback").update({"status": "rejected"}).eq("id", item["id"]).execute()
                    st.warning("Rejected.")

    st.markdown("## ✅ Reviewed Feedback")
    for item in [i for i in feedback_items if i['status'] in ['approved', 'rejected']]:
        with st.expander(f"Turn {item['turn_index']} - {item['timestamp']}", expanded=False):
            st.markdown(f"**Session ID:** {item['session_id']}")
            st.markdown(f"**User Message:** {item['user_message']}")
            st.markdown(f"**AI Response:** {item['ai_response']}")
            st.markdown(f"**Rating:** {item['rating']}")
            st.markdown(f"**Comment:** {item['comment']}")
            st.markdown(f"**Status:** {item['status']}")
