import streamlit as st
from utils import navigate_to

def show(conn):
    st.subheader("📂 Data Navigator")

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = sorted([db[0] for db in cursor.fetchall()])

        col1, col2 = st.columns(2)
        with col1:
            search_db = st.text_input("🔎 Search databases")
        with col2:
            filtered_dbs = [db for db in dbs if search_db.lower() in db.lower()] if search_db else dbs
            selected_db = st.selectbox("Select a database", filtered_dbs)
            st.session_state["selected_db"] = selected_db

        cursor.execute(f"USE `{selected_db}`")
        cursor.execute("SHOW FULL TABLES")
        rows = cursor.fetchall()
        tables = sorted([r[0] for r in rows if r[1] == "BASE TABLE"])

        col3, col4 = st.columns(2)
        with col3:
            search_table = st.text_input("🔎 Search tables")
        with col4:
            filtered_tables = [t for t in tables if search_table.lower() in t.lower()] if search_table else tables
            selected_table = st.selectbox("Select a table", filtered_tables)
            st.session_state["selected_table"] = selected_table

        cursor.execute(f"SHOW COLUMNS FROM `{selected_table}`")
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
