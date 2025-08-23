import streamlit as st
import pandas as pd
from utils import navigate_to
from modules import visualizer

def show(conn):
    # Make all Streamlit notifications bold green
    st.markdown(
        """
        <style>
        div.stAlert p {
            color: #198754 !important; /* bootstrap success green */
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🧠 Analyst Visualization")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    st.markdown("**Tables in database:**")
    st.write(tables)

    current_table = st.session_state.get("selected_table", tables[0] if tables else None)
    table = current_table

    if table:
        # Check if we have a cleaned DataFrame in session state
        if "cleaned_df" in st.session_state:
            df = st.session_state.cleaned_df
            st.success(f"Using cleaned dataset with {df.shape[1]} columns and {df.shape[0]} rows")
        else:
            # Fall back to loading from database if no cleaned DataFrame is available
            cursor.execute(f"SELECT * FROM '{table}' LIMIT 1000")
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=cols)
            st.info("Using original dataset (no cleaned version found)")

        st.markdown("### Select Columns to Visualize")
        selected_cols = st.multiselect("Columns", df.columns.tolist(), default=df.columns.tolist())
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
