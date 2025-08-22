"""
Core Module: Data Cleaner & Query
This module is the heart of the system for cleaning, querying, and managing tables.
"""
__all__ = ["show"]

import streamlit as st
import pandas as pd
import numpy as np
from utils import navigate_to

def show(conn):
    st.info("Cleaner & Query module activated. (Core system module)")
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

        # Function to format large numbers with K/M notation
        def format_large_numbers(val):
            if isinstance(val, (int, float)):
                if pd.isna(val):
                    return ""
                if abs(val) >= 1_000_000:
                    return f"{val/1_000_000:.1f}M"
                if abs(val) >= 1_000:
                    return f"{val/1_000:.1f}K"
            return val

        # Display a formatted preview of data
        st.write("🔍 Raw Data Snapshot")
        st.dataframe(df.head().applymap(lambda x: format_large_numbers(x) if isinstance(x, (int, float)) else x))

        nulls = df.isnull().sum()
        blanks = (df == '').sum()
        duplicates = df.duplicated().sum()

        with st.expander("🧼 Cleaning Summary"):
            st.markdown("<span style='color:black'>NULLs per column</span>", unsafe_allow_html=True)
            st.write(nulls)
            st.markdown("<span style='color:black'>Blank strings per column</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:black'>Duplicate rows: {duplicates}</span>", unsafe_allow_html=True)

        # --- Intelligent Data Type Detection ---
        st.markdown("#### Data Type Detection")
        detected_types = {}
        for col in df.columns:
            # Check for numeric type
            numeric_percent = pd.to_numeric(df[col], errors='coerce').notna().mean() * 100
            
            # Check for datetime type
            datetime_percent = pd.to_datetime(df[col], errors='coerce').notna().mean() * 100
            
            # Check for boolean type
            bool_values = {'true', 'false', 'yes', 'no', 't', 'f', 'y', 'n', '1', '0', 'True', 'False'}
            bool_percent = df[col].astype(str).str.lower().isin(bool_values).mean() * 100
            
            # Determine most likely type
            if numeric_percent > 80:
                detected_types[col] = "Numeric"
            elif datetime_percent > 80:
                detected_types[col] = "Datetime" 
            elif bool_percent > 80:
                detected_types[col] = "Boolean"
            else:
                detected_types[col] = "Text"
                
        # Display detected types in a nice format
        st.markdown("<span style='color:black'>Detected column types:</span>", unsafe_allow_html=True)
        type_cols = st.columns(3)
        for i, (col, dtype) in enumerate(detected_types.items()):
            with type_cols[i % 3]:
                icon = {
                    "Numeric": "🔢", 
                    "Datetime": "📅",
                    "Boolean": "✓✗",
                    "Text": "📝"
                }.get(dtype, "📄")
                st.markdown(f"<span style='color:black'>{icon} {col}: <b>{dtype}</b></span>", unsafe_allow_html=True)
        
        # --- Cleaning Options ---
        st.markdown("#### Clean Your Data")
        col1, col2 = st.columns([1, 8])
        with col1:
            drop_nulls = st.checkbox("", value=True, key="drop_nulls")
        with col2:
            st.markdown("<span style='color:black'>Drop rows with NULLs</span>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 8])
        with col1:
            drop_blanks = st.checkbox("", value=True, key="drop_blanks")
        with col2:
            st.markdown("<span style='color:black'>Drop rows with blank strings</span>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 8])
        with col1:
            drop_duplicates = st.checkbox("", value=True, key="drop_duplicates")
        with col2:
            st.markdown("<span style='color:black'>Drop duplicate rows</span>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 8])
        with col1:
            normalize_case = st.checkbox("", value=True, key="normalize_case")
        with col2:
            st.markdown("<span style='color:black'>Normalize text columns to Title Case</span>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 8])
        with col1:
            auto_convert_types = st.checkbox("", value=True, key="auto_convert_types")
        with col2:
            st.markdown("<span style='color:black'>Apply detected data types automatically</span>", unsafe_allow_html=True)

        # --- Change Column Datatypes ---
        with st.expander("🔧 Change Column Datatypes", expanded=False):
            st.markdown("<span style='color:black'>Change the datatype of columns if needed (e.g., to numeric, string, datetime)</span>", unsafe_allow_html=True)
            dtype_map = {
                "String": "object",
                "Numeric": "float",
                "Integer": "int",
                "Datetime": "datetime64[ns]",
                "Boolean": "bool"
            }
            col1, col2 = st.columns([2, 2])
            with col1:
                dtype_col = st.selectbox("Column", df.columns, key="dtype_col")
            with col2:
                dtype_type = st.selectbox("New datatype", list(dtype_map.keys()), key="dtype_type", 
                                        index=list(dtype_map.keys()).index("String" if detected_types.get(dtype_col, "Text") == "Text" else "Numeric"))
            if st.button("Apply Datatype Change", key="apply_dtype_change"):
                try:
                    if dtype_map[dtype_type] == "datetime64[ns]":
                        df[dtype_col] = pd.to_datetime(df[dtype_col], errors="coerce")
                    elif dtype_map[dtype_type] == "bool":
                        df[dtype_col] = df[dtype_col].astype(str).str.lower().map({"true": True, "false": False, 
                                                                                "yes": True, "no": False, 
                                                                                "y": True, "n": False, 
                                                                                "1": True, "0": False})
                    else:
                        df[dtype_col] = df[dtype_col].astype(dtype_map[dtype_type], errors="ignore")
                    st.success(f"Changed `{dtype_col}` to {dtype_type}")
                except Exception as e:
                    st.error(f"Datatype change error: {e}")

        cleaned_df = df.copy()
        if drop_duplicates:
            cleaned_df = cleaned_df.drop_duplicates()
        if drop_blanks:
            cleaned_df.replace('', np.nan, inplace=True)
        if drop_nulls:
            cleaned_df.dropna(inplace=True)
        if normalize_case:
            for col in cleaned_df.select_dtypes(include='object').columns:
                cleaned_df[col] = cleaned_df[col].astype(str).str.title()
        if auto_convert_types:
            for col, dtype in detected_types.items():
                try:
                    if dtype == "Numeric":
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    elif dtype == "Datetime":
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                    elif dtype == "Boolean":
                        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().map({"true": True, "false": False, 
                                                                                     "yes": True, "no": False, 
                                                                                     "y": True, "n": False, 
                                                                                     "1": True, "0": False})
                except:
                    # If conversion fails, keep as is
                    pass

        cleaned_df.columns = [c.strip().lower().replace(' ', '_') for c in cleaned_df.columns]

        # Display cleaned data with formatted numbers
        st.write("✅ Cleaned Preview")
        st.dataframe(cleaned_df.head().applymap(lambda x: format_large_numbers(x) if isinstance(x, (int, float)) else x))
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
        with st.expander("Update Values", expanded=False):
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

        with st.expander("Delete Rows", expanded=False):
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

        # Navigation buttons (side panel logic remains)
        col_back, col_next = st.columns([1, 1], gap="small")
        with col_back:
            if st.button("← Back"):
                navigate_to("Preview & Audit")
        with col_next:
            if st.button("Next →"):
                navigate_to("Analyst")

    except Exception as e:
        st.error(f"Error loading or cleaning data: {e}")
