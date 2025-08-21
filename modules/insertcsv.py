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

    # Step 2: Select/Create Database
    cursor.execute("SHOW DATABASES")
    dbs = [db[0] for db in cursor.fetchall()]
    db_mode = st.radio("Database option", ["Use existing", "Create new"])
    if db_mode == "Use existing":
        selected_db = st.selectbox("Select database", dbs)
    else:
        selected_db = st.text_input("Enter new database name")
        if selected_db and st.button("Create Database"):
            try:
                cursor.execute(f"CREATE DATABASE `{selected_db}`")
                conn.commit()
                st.success(f"Database `{selected_db}` created.")
                cursor.execute("SHOW DATABASES")
                dbs = [db[0] for db in cursor.fetchall()]
            except Exception as e:
                st.error(f"Error creating database: {e}")

    if not selected_db:
        st.info("Select or create a database to continue.")
        return

    cursor.execute(f"USE `{selected_db}`")

    # Step 3: Table Name
    default_table = uploaded_file.name.split(".")[0]
    table_name = st.text_input("Table name", value=default_table)

    # Step 4: Datatype Selection
    st.markdown("#### Column Datatypes")
    dtype_map = {
        "int64": "INT",
        "float64": "FLOAT",
        "object": "VARCHAR(255)",
        "bool": "BOOLEAN",
        "datetime64[ns]": "DATETIME"
    }
    col_types = {}
    for col in df.columns:
        inferred = dtype_map.get(str(df[col].dtype), "VARCHAR(255)")
        col_types[col] = st.selectbox(f"{col}", [inferred, "INT", "FLOAT", "VARCHAR(255)", "BOOLEAN", "DATETIME"], index=0)

    # Step 5: Insert
    if st.button("Insert CSV to Database"):
        try:
            # Create table
            cols_sql = ", ".join([f"`{col}` {col_types[col]}" for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` ({cols_sql})")
            conn.commit()

            # Insert rows
            for _, row in df.iterrows():
                values = []
                for col in df.columns:
                    val = row[col]
                    if pd.isnull(val):
                        values.append("NULL")
                    elif col_types[col].startswith("VARCHAR"):
                        values.append(f"'{str(val).replace('\'','\\\'')}'")
                    elif col_types[col] == "DATETIME":
                        values.append(f"'{str(val)}'")
                    elif col_types[col] == "BOOLEAN":
                        values.append(str(int(bool(val))))
                    else:
                        values.append(str(val))
                values_sql = ", ".join(values)
                cursor.execute(f"INSERT INTO `{table_name}` VALUES ({values_sql})")
            conn.commit()
            st.success(f"CSV inserted into `{selected_db}`.`{table_name}` successfully!")
        except Exception as e:
            st.error(f"Error inserting CSV: {e}")

    if st.button("← Back"):
        navigate_to("Navigator")
