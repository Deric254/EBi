import streamlit as st
from utils import navigate_to

def show():
    st.subheader("🔄 Reset Session")
    st.markdown("Use this to restart your workflow from the beginning.")

    col_back, col_reset = st.columns([1, 1], gap="small")
    with col_back:
        if st.button("← Back"):
            navigate_to("Analyst")
    with col_reset:
        if st.button("Reset All"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session reset. Please reload or start from Welcome.")
            navigate_to("Welcome")

    st.markdown("Visit [EXES Analytics](https://deric-exes-analytics.netlify.app) to explore more tools.")
      #  navigate_to("Generate Data")
   # if st.button("Welcome →"):
     #   navigate_to("Welcome")

    st.markdown("Visit [EXES Analytics](https://deric-exes-analytics.netlify.app) to explore more tools.")
