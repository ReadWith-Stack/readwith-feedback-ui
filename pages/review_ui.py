import streamlit as st
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

st.set_page_config(page_title="Feedback Review UI", layout="wide")
st.title("🗃️ Review Feedback Comments")

# --- Show summary counts ---
st.markdown("### 🧮 Feedback Summary")
summary = {
    "total": supabase.table("feedback").select("id").execute().count,
    "approved": supabase.table("feedback").select("id").eq("status", "approved").execute().count,
    "rejected": supabase.table("feedback").select("id").eq("status", "rejected").execute().count,
}
st.markdown(f"- **Total:** {summary['total']}")
st.markdown(f"- ✅ Approved:** {summary['approved']}")
st.markdown(f"- ❌ Rejected:** {summary['rejected']}")

# --- Load pending feedback from Supabase ---
with st.spinner("Loading feedback..."):
    response = supabase.table("feedback").select("*").eq("status", "pending").execute()
    feedback_items = response.data if response.data else []

if not feedback_items:
    st.success("✅ No pending feedback.")
else:
    for item in feedback_items:
        with st.expander(f"Turn {item['turn_index']} - {item['timestamp']}", expanded=True):
            st.markdown(f"**User Message:** {item['user_message']}")
            st.markdown(f"**AI Response:** {item['ai_response']}")
            st.markdown(f"**Rating:** {item['rating']}")
            st.markdown(f"**Comment:** {item['comment']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{item['id']}"):
                    supabase.table("feedback").update({"status": "approved"}).eq("id", item["id"]).execute()
                    st.success("Approved!")
            with col2:
                if st.button("❌ Reject", key=f"reject_{item['id']}"):
                    supabase.table("feedback").update({"status": "rejected"}).eq("id", item["id"]).execute()
                    st.warning("Rejected.")
