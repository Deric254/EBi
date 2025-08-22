import streamlit as st
import pandas as pd
from utils import navigate_to

def show(conn):
    st.subheader("📤 Insert CSV to Database")

    cursor = conn.cursor()

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
    table_name = st.text_input("Table name", value=default_table)

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
        except Exception as e:
            st.error(f"Error inserting CSV: {e}")

    if st.button("← Back"):
        navigate_to("Navigator")
