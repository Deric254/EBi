import streamlit as st
import pandas as pd
import numpy as np
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

    st.subheader(f"🧹 Cleaner & Query for `{table}`")
    cursor = conn.cursor()

    # --- Table Management Section ---
    st.markdown("#### Table Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Table"):
            try:
                cursor.execute(f"DROP TABLE IF EXISTS '{table}'")
                conn.commit()
                st.success(f"Table '{table}' deleted.")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                if tables:
                    st.session_state["selected_table"] = tables[0]
                else:
                    st.session_state.pop("selected_table", None)
                st.rerun()  # Use st.rerun() for immediate rerun, not st.experimental_rerun()
            except Exception as e:
                st.error(f"Error deleting table: {e}")
    with col2:
        new_name = st.text_input("Rename table to:", value=table, key="rename_table", placeholder="Enter new table name")
        if st.button("Rename Table"):
            try:
                cursor.execute(f"ALTER TABLE '{table}' RENAME TO '{new_name}'")
                conn.commit()
                st.success(f"Table '{table}' renamed to '{new_name}'.")
                st.session_state["selected_table"] = new_name
                # Refresh table list after rename
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                st.markdown(f"<span style='color:#d90429;font-weight:bold;'>Rename error: {e}</span>", unsafe_allow_html=True)

    try:
        cursor.execute(f"SELECT * FROM '{table}' LIMIT 1000")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)

        st.write("🔍 Raw Data Snapshot", df.head())

        nulls = df.isnull().sum()
        blanks = (df == '').sum()
        duplicates = df.duplicated().sum()

        with st.expander("🧼 Cleaning Summary"):
            st.markdown("<span style='color:black'>NULLs per column</span>", unsafe_allow_html=True)
            st.write(nulls)
            st.markdown("<span style='color:black'>Blank strings per column</span>", unsafe_allow_html=True)
            st.write(blanks)
            st.markdown(f"<span style='color:black'>Duplicate rows: {duplicates}</span>", unsafe_allow_html=True)

        # Cleaning checkboxes and logic
        checkbox_states = {}
        for label, key in [
            ("Drop rows with NULLs", "drop_nulls"),
            ("Drop rows with blank strings", "drop_blanks"),
            ("Drop duplicate rows", "drop_duplicates"),
            ("Normalize text columns to Title Case", "normalize_case"),
            ("Suggest column types", "suggest_types"),
            ("Detect numeric outliers", "detect_outliers")
        ]:
            col1, col2 = st.columns([1, 8])
            with col1:
                checked = st.checkbox("", value=True, key=key)
            with col2:
                st.markdown(f"<span style='color:black'>{label}</span>", unsafe_allow_html=True)
            checkbox_states[key] = checked

        cleaned_df = df.copy()

        if checkbox_states["drop_duplicates"]:
            cleaned_df = cleaned_df.drop_duplicates()

        if checkbox_states["drop_blanks"]:
            cleaned_df.replace('', np.nan, inplace=True)

        if checkbox_states["drop_nulls"]:
            cleaned_df.dropna(inplace=True)

        if checkbox_states["normalize_case"]:
            for col in cleaned_df.select_dtypes(include='object').columns:
                cleaned_df[col] = cleaned_df[col].astype(str).str.title()

        if checkbox_states["suggest_types"]:
            with st.expander("📊 Suggested Column Types"):
                st.write(cleaned_df.dtypes)

        if checkbox_states["detect_outliers"]:
            with st.expander("📈 Outlier Detection"):
                for col in cleaned_df.select_dtypes(include=np.number).columns:
                    q1 = cleaned_df[col].quantile(0.25)
                    q3 = cleaned_df[col].quantile(0.75)
                    iqr = q3 - q1
                    outliers = cleaned_df[(cleaned_df[col] < q1 - 1.5 * iqr) | (cleaned_df[col] > q3 + 1.5 * iqr)]
                    st.write(f"Outliers in `{col}`:", outliers[[col]])

        cleaned_df.columns = [c.strip().lower().replace(' ', '_') for c in cleaned_df.columns]

        st.write("✅ Cleaned Preview", cleaned_df.head())
        st.download_button("📥 Export Cleaned CSV", cleaned_df.to_csv(index=False), f"{table}_cleaned.csv", "text/csv")
        # Save cleaned CSV to my_projects/files
        import os
        from datetime import datetime
        files_dir = os.path.join("my_projects", "files")
        os.makedirs(files_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_path = os.path.join(files_dir, f"{table}_cleaned_{timestamp}.csv")
        cleaned_df.to_csv(cleaned_path, index=False)
        st.success(f"Cleaned CSV saved to My Projects.")

        # --- Data Modification Section ---
        with st.expander("✏️ Update Values", expanded=False):
            st.markdown("Update values in a column for matching rows.")
            col1, col2 = st.columns([2, 2])
            with col1:
                update_col = st.selectbox("Column to update", cleaned_df.columns, key="cleaner_update_col")
            with col2:
                update_old = st.text_input("Old value (exact match)", key="cleaner_update_old")
                update_new = st.text_input("New value", key="cleaner_update_new")
            if st.button("Run UPDATE", key="cleaner_run_update"):
                try:
                    cursor.execute(f"UPDATE '{table}' SET \"{update_col}\"=? WHERE \"{update_col}\"=?", (update_new, update_old))
                    conn.commit()
                    st.success(f"Updated `{update_col}` from '{update_old}' to '{update_new}'")
                except Exception as e:
                    st.error(f"Update error: {e}")

        with st.expander("🗑️ Delete Rows", expanded=False):
            st.markdown("Delete rows where a column matches a value.")
            col1, col2 = st.columns([2, 2])
            with col1:
                delete_col = st.selectbox("Column to match for delete", cleaned_df.columns, key="cleaner_delete_col")
            with col2:
                delete_val = st.text_input("Value to delete (exact match)", key="cleaner_delete_val")
            if st.button("Run DELETE", key="cleaner_run_delete"):
                try:
                    cursor.execute(f"DELETE FROM '{table}' WHERE \"{delete_col}\"=?", (delete_val,))
                    conn.commit()
                    st.success(f"Deleted rows where `{delete_col}` = '{delete_val}'")
                except Exception as e:
                    st.error(f"Delete error: {e}")

        with st.expander("🔤 Rename Table", expanded=False):
            st.markdown("Rename your table to a new name.")
            col1, col2 = st.columns([2, 2])
            with col1:
                new_table_name = st.text_input("New table name", value=table, key="cleaner_rename_table")
            with col2:
                st.markdown("Tip: Use a descriptive name for your table.")
            if st.button("Run RENAME", key="cleaner_run_rename"):
                try:
                    cursor.execute(f"ALTER TABLE '{table}' RENAME TO '{new_table_name}'")
                    conn.commit()
                    st.success(f"Table renamed to '{new_table_name}'")
                    st.session_state["selected_table"] = new_table_name
                except Exception as e:
                    st.error(f"Rename error: {e}")

        # Collapsed manual SQL query area
        with st.expander("🧠 Run Manual SQL Query"):
            query = st.text_area("Enter SQL query", value="", placeholder="Type your SQL query here...")
            if st.button("Run Query"):
                try:
                    cursor.execute(query)
                    if cursor.description:
                        result = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        st.dataframe(pd.DataFrame(result, columns=columns))
                    else:
                        conn.commit()
                        st.success("Query executed successfully.")
                except Exception as e:
                    st.error(f"Query error: {e}")

        col_back, col_next = st.columns([1, 1], gap="small")
        with col_back:
            if st.button("← Back"):
                navigate_to("Preview & Audit")
        with col_next:
            if st.button("Next →"):
                navigate_to("Analyst")

    except Exception as e:
        st.error(f"Error loading or cleaning data: {e}")
