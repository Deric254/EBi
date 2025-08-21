import streamlit as st

def navigate_to(target: str):
    st.session_state["page"] = target
