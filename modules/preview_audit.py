import streamlit as st
import pandas as pd
from utils import navigate_to

def show(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    current_table = st.session_state.get("selected_table", tables[0] if tables else None)
    table = current_table

    if not table:
        st.warning("Please select a table first.")
        return

    st.subheader(f"🔍 Preview & Audit `{table}`")
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM '{table}' LIMIT 50")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)

        st.download_button("📥 Export CSV", df.to_csv(index=False), f"{table}.csv", "text/csv")
        st.download_button("📥 Export JSON", df.to_json(orient="records"), f"{table}.json", "application/json")

        cursor.execute(f"PRAGMA table_info('{table}')")
        schema = cursor.fetchall()
        with st.expander("📌 Columns"):
            st.write(pd.DataFrame(schema, columns=["cid", "name", "type", "notnull", "default_value", "pk"]))

        cursor.execute(f"PRAGMA index_list('{table}')")
        indexes = cursor.fetchall()
        with st.expander("📍 Indexes"):
            st.write(pd.DataFrame(indexes, columns=["seq", "name", "unique", "origin", "partial"]))

        col_back, col_next = st.columns([1, 1], gap="small")
        with col_back:
            if st.button("← Back"):
                navigate_to("Navigator")
        with col_next:
            if st.button("Next →"):
                navigate_to("Cleaner & Query")

    except Exception as e:
        st.error(f"Error previewing/auditing: {e}")
        st.error(f"Error previewing/auditing: {e}")
        st.error(f"Error previewing/auditing: {e}")
