import streamlit as st
from supabase import create_client, Client
import os

# --- Supabase setup ---
SUPABASE_URL = "https://nwhsnymzihkqtlufiafu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53aHNueW16aWhrcXRsdWZpYWZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4NDE2MzEsImV4cCI6MjA2MzQxNzYzMX0.7ShjmnX6_cY2H-Aj3eHF_23BP4D0tUS5wgoDBq9_3oE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
st.markdown(f"- ✅ **Approved:** {summary['approved']}")
st.markdown(f"- ❌ **Rejected:** {summary['rejected']}")

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
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{item['id']}"):
                    supabase.table("feedback").update({"status": "rejected"}).eq("id", item["id"]).execute()
                    st.warning("Rejected.")
                    st.experimental_rerun()
