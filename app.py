# --- Safe rerun trigger ---
if st.session_state.get("trigger_rerun"):
    st.session_state["trigger_rerun"] = False
    st.experimental_rerun()

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
        st.session_state["trigger_rerun"] = True
