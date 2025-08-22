import streamlit as st
from utils import navigate_to

def show(conn):
    st.subheader("📂 Data Navigator")

    try:
        cursor = conn.cursor()
        # List tables in SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        col1, col2 = st.columns(2)
        with col1:
            search_table = st.text_input("🔎 Search tables", placeholder="Type table name...")
        with col2:
            filtered_tables = [t for t in tables if search_table.lower() in t.lower()] if search_table else tables
            selected_table = st.selectbox("Select a table", filtered_tables)
            st.session_state["selected_table"] = selected_table

        # Table switch dropdown (redundant with selectbox above, but for consistency)
        # If you want a separate dropdown, uncomment below:
        # switch_table = st.selectbox("Switch table", tables, index=tables.index(st.session_state["selected_table"]) if st.session_state.get("selected_table") in tables else 0)
        # if switch_table != st.session_state.get("selected_table"):
        #     st.session_state["selected_table"] = switch_table
        #     st.experimental_rerun()

        # Show columns for selected table
        cursor.execute(f"PRAGMA table_info('{selected_table}')")
        columns = cursor.fetchall()
        with st.expander("📌 Table Columns"):
            st.write(columns)

        col_next, col_back = st.columns([1, 1])
        with col_next:
            if st.button("Next →"):
                navigate_to("Preview & Audit")
        with col_back:
            if st.button("← Back"):
                navigate_to("Welcome")

    except Exception as e:
        st.error(f"Error navigating: {e}")
