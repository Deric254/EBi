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
    # Make all Streamlit notifications (info/success/warning/error) bold green without changing logic
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

    #st.info("Cleaner & Query module activated. (Core system module)")
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
                # Make inline rename error bold green to match notifications
                st.markdown(f"<span style='color:#198754;font-weight:bold;'>Rename error: {e}</span>", unsafe_allow_html=True)

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
        # New option: drop columns that are entirely NULL/blank (whitespace-aware)
        col1, col2 = st.columns([1, 8])
        with col1:
            drop_empty_columns = st.checkbox("", value=False, key="drop_empty_columns")
        with col2:
            st.markdown("<span style='color:black'>Drop columns that are entirely NULL/blank</span>", unsafe_allow_html=True)

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
        # Robustly drop empty columns (all NULL or blank/whitespace) if selected
        if 'drop_empty_columns' in locals() and drop_empty_columns:
            tmp = cleaned_df.copy()
            obj_cols = tmp.select_dtypes(include='object').columns
            if len(obj_cols) > 0:
                # Treat pure whitespace as empty
                tmp[obj_cols] = tmp[obj_cols].replace(r'^\s*$', np.nan, regex=True)
            empty_cols = [c for c in tmp.columns if tmp[c].isna().all()]
            if empty_cols:
                cleaned_df.drop(columns=empty_cols, inplace=True)
                st.success(f"Dropped empty columns: {', '.join(empty_cols)}")
            else:
                st.info("No empty columns to drop.")
        # --- Column/Row Selection Section ---
        with st.expander("🗑️ Drop Columns or Filter Rows", expanded=False):
            st.markdown("<span style='color:black;font-weight:bold;'>Remove specific columns or rows from dataset</span>", unsafe_allow_html=True)
            
            # Column dropping section
            st.markdown("<span style='color:black;'>Select columns to remove:</span>", unsafe_allow_html=True)
            columns_to_drop = st.multiselect("Columns to drop", cleaned_df.columns, key="cols_to_drop")
            
            if columns_to_drop:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Drop Selected Columns", key="drop_cols_btn"):
                        try:
                            # Keep track of original shape
                            orig_cols = cleaned_df.shape[1]
                            
                            # Create a new DataFrame excluding the selected columns
                            # This ensures we're creating a new DataFrame, not a view
                            remaining_columns = [col for col in cleaned_df.columns if col not in columns_to_drop]
                            cleaned_df = cleaned_df[remaining_columns].copy()
                            
                            dropped_count = orig_cols - cleaned_df.shape[1]
                            st.success(f"Dropped {dropped_count} columns: {', '.join(columns_to_drop)}")
                        except Exception as e:
                            st.error(f"Error dropping columns: {e}")
            
            # Use a Streamlit divider instead of HTML hr tag
            st.markdown("---")
            
            # Row filtering section
            st.markdown("<span style='color:black;font-weight:bold;'>Filter rows by condition:</span>", unsafe_allow_html=True)
            
            filter_col1, filter_col2, filter_col3 = st.columns([1.5, 1, 1.5])
            with filter_col1:
                filter_column = st.selectbox("Select column", cleaned_df.columns, key="filter_column")
            
            with filter_col2:
                operators = ["equals", "not equals", "greater than", "less than", "contains", "starts with", "ends with", "is null", "is not null"]
                filter_operator = st.selectbox("Condition", operators, key="filter_operator")
            
            with filter_col3:
                # Only show value input for operators that need it
                if filter_operator not in ["is null", "is not null"]:
                    # Use the appropriate input type based on column data type
                    col_dtype = str(cleaned_df[filter_column].dtype)
                    if "int" in col_dtype or "float" in col_dtype:
                        try:
                            filter_value = st.number_input("Value", value=0, key="filter_value")
                        except:
                            filter_value = st.text_input("Value", key="filter_value")
                    elif "datetime" in col_dtype:
                        filter_value = st.date_input("Value", key="filter_value")
                    else:
                        filter_value = st.text_input("Value", key="filter_value")
            
            if st.button("Apply Filter", key="apply_filter_btn"):
                try:
                    orig_rows = len(cleaned_df)
                    
                    # Create filter based on selected operator
                    if filter_operator == "equals":
                        mask = cleaned_df[filter_column] == filter_value
                    elif filter_operator == "not equals":
                        mask = cleaned_df[filter_column] != filter_value
                    elif filter_operator == "greater than":
                        mask = cleaned_df[filter_column] > filter_value
                    elif filter_operator == "less than":
                        mask = cleaned_df[filter_column] < filter_value
                    elif filter_operator == "contains":
                        mask = cleaned_df[filter_column].astype(str).str.contains(str(filter_value), na=False)
                    elif filter_operator == "starts with":
                        mask = cleaned_df[filter_column].astype(str).str.startswith(str(filter_value), na=False)
                    elif filter_operator == "ends with":
                        mask = cleaned_df[filter_column].astype(str).str.endswith(str(filter_value), na=False)
                    elif filter_operator == "is null":
                        mask = cleaned_df[filter_column].isna()
                    elif filter_operator == "is not null":
                        mask = ~cleaned_df[filter_column].isna()
                    
                    # Apply the filter
                    cleaned_df = cleaned_df[mask]
                    
                    # Show results
                    filtered_rows = len(cleaned_df)
                    removed_rows = orig_rows - filtered_rows
                    st.success(f"Filter applied: Kept {filtered_rows} rows, removed {removed_rows} rows")
                except Exception as e:
                    st.error(f"Error applying filter: {e}")
            
            # Option to reset all filters
            if st.button("Reset to Original Data", key="reset_filters"):
                cleaned_df = df.copy()
                st.success("Reset to original data. All filters and transformations cleared.")

        # --- Column Rename/Edit Section ---
        with st.expander("✏️ Rename or Edit Columns", expanded=False):
            st.markdown("<span style='color:black'>Rename columns in the cleaned dataset</span>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 2])
            with col1:
                if cleaned_df.columns.size > 0:
                    col_to_rename = st.selectbox("Select column to rename", cleaned_df.columns, key="col_rename_select")
                else:
                    st.warning("No columns available")
                    col_to_rename = None
            
            with col2:
                if col_to_rename:
                    new_col_name = st.text_input("New column name", value=col_to_rename, key="new_col_name")
                    
                    if st.button("Rename Column", key="rename_col_btn"):
                        if new_col_name and new_col_name != col_to_rename:
                            try:
                                # Create a mapping dictionary for column renames
                                col_mapping = {col_to_rename: new_col_name}
                                # Apply rename to the cleaned dataframe
                                cleaned_df = cleaned_df.rename(columns=col_mapping)
                                st.success(f"Column '{col_to_rename}' renamed to '{new_col_name}'")
                            except Exception as e:
                                st.error(f"Error renaming column: {e}")
            
            # Batch column renaming option with black text
            st.markdown("---")
            st.markdown("<span style='color:black; font-weight:bold;'>Simple Column Name Formatting</span>", unsafe_allow_html=True)
            st.markdown("<span style='color:black;'>Format all column names at once (easier than renaming each column)</span>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown("<span style='color:black;'>Make lowercase:</span>", unsafe_allow_html=True)
                make_lowercase = st.checkbox("", value=True, key="make_lowercase")
            with col2:
                st.markdown("<span style='color:black;'>Replace spaces:</span>", unsafe_allow_html=True)
                replace_spaces = st.checkbox("", value=True, key="replace_spaces")
            with col3:
                if replace_spaces:
                    st.markdown("<span style='color:black;'>Replace with:</span>", unsafe_allow_html=True)
                    space_replacement = st.selectbox("", ["_", "-", ""], key="space_replacement")
                else:
                    space_replacement = "_"  # Default
            
            if st.button("Apply Formatting to All Columns", key="batch_rename_btn"):
                old_names = cleaned_df.columns.tolist()
                
                # Create new column names based on selected options
                new_names = old_names.copy()
                if make_lowercase:
                    new_names = [col.lower() for col in new_names]
                if replace_spaces:
                    new_names = [col.replace(" ", space_replacement) for col in new_names]
                
                # Apply the new column names if changes were made
                rename_map = {old: new for old, new in zip(old_names, new_names) if old != new}
                if rename_map:
                    cleaned_df = cleaned_df.rename(columns=rename_map)
                    renamed_cols = list(rename_map.keys())
                    st.success(f"Renamed {len(renamed_cols)} columns")
                else:
                    st.info("No columns needed renaming")

        # Comment out the auto-rename line since we now have user controls for it
        # cleaned_df.columns = [c.strip().lower().replace(' ', '_') for c in cleaned_df.columns]

        # Display cleaned data with formatted numbers
        st.write("✅ Cleaned Preview")
        
        # Show row and column counts to verify changes
        st.markdown(f"<span style='color:black;font-weight:bold;'>Cleaned data has {cleaned_df.shape[1]} columns and {cleaned_df.shape[0]} rows</span>", unsafe_allow_html=True)
        
        # Add a debug option to show column names for verification
        with st.expander("Column details", expanded=False):
            st.markdown("<span style='color:black;'>Current columns in dataset:</span>", unsafe_allow_html=True)
            for i, col in enumerate(cleaned_df.columns):
                st.markdown(f"<span style='color:black;'>{i+1}. {col}</span>", unsafe_allow_html=True)
        
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

        # Store the cleaned DataFrame in session state to make it available to other modules
        st.session_state.cleaned_df = cleaned_df.copy()
        
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
            st.markdown("Delete rows in a column for matching values.")
            col1, col2 = st.columns([2, 2])
            with col1:
                delete_col = st.selectbox("Column to delete from", cleaned_df.columns, key="cleaner_delete_col")
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
                # Ensure the cleaned DataFrame is in session state before navigating
                st.session_state.cleaned_df = cleaned_df.copy()
                navigate_to("Analyst")

    except Exception as e:
        st.error(f"Error loading or cleaning data: {e}")
