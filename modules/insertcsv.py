import streamlit as st
import pandas as pd
from utils import navigate_to

def show(conn):
    st.subheader("📤 Insert CSV to Database")

    cursor = conn.cursor()

    # Table switch dropdown
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    if tables:
        current_table = st.session_state.get("selected_table", tables[0])
        selected_table = st.selectbox("Switch to table", tables, index=tables.index(current_table) if current_table in tables else 0)
        if selected_table != current_table:
            st.session_state["selected_table"] = selected_table
            st.experimental_rerun()

    # Step 1: Upload CSV
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file to begin.")
        if st.button("← Back"):
            navigate_to("Navigator")
        return

    df = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded CSV:", df.head())

    # Step 2: Table Name
    default_table = uploaded_file.name.split(".")[0]
    table_name = st.text_input("Table name", value=default_table, placeholder="Enter table name")

    # Step 3: Datatype Selection
    st.markdown("#### Column Datatypes")
    dtype_map = {
        "int64": "INTEGER",
        "float64": "REAL",
        "object": "TEXT",
        "bool": "INTEGER",
        "datetime64[ns]": "TEXT"
    }
    col_types = {}
    for col in df.columns:
        inferred = dtype_map.get(str(df[col].dtype), "TEXT")
        col_types[col] = st.selectbox(f"{col}", [inferred, "INTEGER", "REAL", "TEXT"], index=0)

    # Step 4: Insert
    if st.button("Insert CSV to Database"):
        try:
            # Create table
            cols_sql = ", ".join([f"'{col}' {col_types[col]}" for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS '{table_name}' ({cols_sql})")
            conn.commit()

            # Insert rows
            for _, row in df.iterrows():
                values = []
                for col in df.columns:
                    val = row[col]
                    if pd.isnull(val):
                        values.append("NULL")
                    elif col_types[col] == "TEXT":
                        values.append(f"'{str(val).replace('\'','\\\'')}'")
                    else:
                        values.append(str(val))
                values_sql = ", ".join(values)
                cursor.execute(f"INSERT INTO '{table_name}' VALUES ({values_sql})")
            conn.commit()
            st.success(f"CSV inserted into `{table_name}` successfully!")
            # Save uploaded CSV to my_projects/files
            import os
            from datetime import datetime
            files_dir = os.path.join("my_projects", "files")
            os.makedirs(files_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = os.path.join(files_dir, f"{table_name}_uploaded_{timestamp}.csv")
            df.to_csv(csv_path, index=False)
            st.success(f"Uploaded CSV saved to My Projects.")
        except Exception as e:
            st.error(f"Error inserting CSV: {e}")

    if st.button("← Back"):
        navigate_to("Navigator")
