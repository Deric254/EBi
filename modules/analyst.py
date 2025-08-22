import streamlit as st
import pandas as pd
from utils import navigate_to
from modules import visualizer

def show(conn):
    st.subheader("🧠 Analyst Visualization")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    st.markdown("**Tables in database:**")
    st.write(tables)

    current_table = st.session_state.get("selected_table", tables[0] if tables else None)
    table = current_table

    if table:
        cursor.execute(f"SELECT * FROM '{table}' LIMIT 1000")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)

        st.markdown("### Select Columns to Visualize")
        selected_cols = st.multiselect("Columns", cols, default=cols)
        if not selected_cols:
            st.warning("Please select at least one column.")
            return

        df_selected = df[selected_cols]
        st.markdown("### Visualization & Insights")
        visualizer.show(df_selected, title="📊 Analyst Visualization", key="analyst")
        st.markdown("#### Insights")
        st.write(df_selected.describe(include="all"))

    else:
        st.info("No table selected.")

    col_back, col_next = st.columns([1, 1], gap="small")
    with col_back:
        if st.button("← Back"):
            navigate_to("Cleaner & Query")
    with col_next:
        if st.button("Next →"):
            navigate_to("Reset")
