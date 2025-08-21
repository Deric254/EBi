import streamlit as st
import pandas as pd
from utils import navigate_to

def show(conn):
    db = st.session_state.get("selected_db")
    table = st.session_state.get("selected_table")
    if not db or not table:
        st.warning("Please select a database and table first.")
        return

    st.subheader(f"🔍 Preview & Audit `{table}`")
    cursor = conn.cursor()
    cursor.execute(f"USE `{db}`")

    try:
        cursor.execute(f"SELECT * FROM `{table}` LIMIT 50")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)

        st.download_button("📥 Export CSV", df.to_csv(index=False), f"{table}.csv", "text/csv")
        st.download_button("📥 Export JSON", df.to_json(orient="records"), f"{table}.json", "application/json")

        cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        schema = cursor.fetchall()
        with st.expander("📌 Columns"):
            st.write(pd.DataFrame(schema, columns=["Field", "Type", "Null", "Key", "Default", "Extra"]))

        cursor.execute(f"SHOW INDEX FROM `{table}`")
        indexes = cursor.fetchall()
        with st.expander("📍 Indexes"):
            st.write(pd.DataFrame(indexes))

        col_back, col_next = st.columns([1, 1], gap="small")
        with col_back:
            if st.button("← Back"):
                navigate_to("Navigator")
        with col_next:
            if st.button("Next →"):
                navigate_to("Cleaner & Query")

    except Exception as e:
        st.error(f"Error previewing/auditing: {e}")
