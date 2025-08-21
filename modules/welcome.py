import streamlit as st
from utils import navigate_to

def show():
    st.subheader("🧭 Welcome to EBI")
    st.markdown("""
    This console helps you:
    - Browse and explore databases  
    - Preview and audit tables  
    - Clean data for analysis  
    - Run advanced SQL queries  
    - Reset session anytime  

    Built for analysts and admins.  
    Visit [EXES Analytics](https://deric-exes-analytics.netlify.app) to learn more.
    """)

   # if st.button("Home"):
     #   navigate_to("Welcome")
    if st.button("Start →"):
        navigate_to("Navigator")
    #if st.button("Reset →"):
     #   navigate_to("Reset")
