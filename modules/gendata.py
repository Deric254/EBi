import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
from utils import navigate_to

fake = Faker()

def infer_type_from_name(col_name):
    name = col_name.lower()
    if "name" in name:
        return "Name"
    elif "email" in name:
        return "Email"
    elif "phone" in name or "mobile" in name or "contact" in name:
        return "Phone"
    elif "address" in name or "location" in name:
        return "Address"
    elif "date" in name or "dob" in name or "birth" in name:
        return "Date"
    elif "id" in name:
        return "ID"
    elif "subject" in name:
        return "Subject"
    elif "price" in name or "amount" in name or "score" in name or "value" in name:
        return "Float"
    elif "category" in name or "type" in name or "group" in name:
        return "Category"
    elif "flag" in name or "is_" in name or "active" in name or "status" in name:
        return "Boolean"
    elif "desc" in name or "note" in name or "comment" in name or "text" in name:
        return "Text"
    else:
        return None

def show(conn):
    st.subheader("🧬 Generate & Insert Synthetic Dataset")

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

    # Table management section
    st.markdown("#### Table Management")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    if tables:
        selected_table = st.selectbox("Select table to delete or rename", tables)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Table"):
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS '{selected_table}'")
                    conn.commit()
                    st.success(f"Table '{selected_table}' deleted.")
                except Exception as e:
                    st.error(f"Error deleting table: {e}")
        with col2:
            new_name = st.text_input("Rename table to:", value=selected_table, key="rename_table", placeholder="Enter new table name")
            if st.button("Rename Table"):
                try:
                    cursor.execute(f"ALTER TABLE '{selected_table}' RENAME TO '{new_name}'")
                    conn.commit()
                    st.success(f"Table '{selected_table}' renamed to '{new_name}'.")
                except Exception as e:
                    st.error(f"Error renaming table: {e}")

    st.markdown("#### 1. Table & Columns")
    table_name = st.text_input("Table name", value="synthetic_data", placeholder="Enter table name")
    num_rows = st.number_input("Number of rows", min_value=10, max_value=100000, value=100)

    st.markdown("Define columns and patterns:")
    col_defs = []
    col_types = ["ID", "Name", "Email", "Phone", "Address", "Date", "Subject", "Integer", "Float", "Category", "Boolean", "Text"]
    subjects_list = ["Math", "English", "Science", "History", "Art", "Music", "Geography", "Physics", "Chemistry", "Biology"]
    n_cols = st.number_input("Number of columns", min_value=1, max_value=20, value=5)
    for i in range(n_cols):
        col1, col2 = st.columns([2,2])
        with col1:
            col_name = st.text_input(f"Column {i+1} name", value=f"col_{i+1}", key=f"colname_{i}", placeholder="Enter column name")
        with col2:
            inferred_type = infer_type_from_name(col_name)
            default_index = col_types.index(inferred_type) if inferred_type in col_types else 0
            col_type = st.selectbox(f"Type for {col_name}", col_types, index=default_index, key=f"coltype_{i}")
        col_defs.append((col_name, col_type))

    if st.button("Generate & Insert"):
        # Generate data
        data = {}
        for col_name, col_type in col_defs:
            inferred_type = infer_type_from_name(col_name)
            use_type = inferred_type if inferred_type else col_type
            if use_type == "ID":
                data[col_name] = list(range(1, num_rows+1))
            elif use_type == "Name":
                data[col_name] = [fake.name() for _ in range(num_rows)]
            elif use_type == "Email":
                data[col_name] = [fake.email() for _ in range(num_rows)]
            elif use_type == "Phone":
                data[col_name] = [fake.phone_number() for _ in range(num_rows)]
            elif use_type == "Address":
                data[col_name] = [fake.address().replace('\n', ', ') for _ in range(num_rows)]
            elif use_type == "Date":
                data[col_name] = [fake.date_between('-5y', 'today').strftime("%Y-%m-%d") for _ in range(num_rows)]
            elif use_type == "Subject":
                data[col_name] = np.random.choice(subjects_list, num_rows)
            elif use_type == "Integer":
                data[col_name] = np.random.randint(0, 100, num_rows)
            elif use_type == "Float":
                data[col_name] = np.round(np.random.uniform(0, 100, num_rows), 2)
            elif use_type == "Category":
                cats = ["A", "B", "C", "D"]
                data[col_name] = np.random.choice(cats, num_rows)
            elif use_type == "Boolean":
                data[col_name] = np.random.choice([0, 1], num_rows)
            elif use_type == "Text":
                data[col_name] = [fake.sentence(nb_words=8) for _ in range(num_rows)]
            else:
                data[col_name] = [None]*num_rows

        df = pd.DataFrame(data)
        st.write("Preview of generated data:", df.head())

        # Create table SQL
        sql_types = {
            "ID": "INTEGER",
            "Name": "TEXT",
            "Email": "TEXT",
            "Phone": "TEXT",
            "Address": "TEXT",
            "Date": "TEXT",
            "Subject": "TEXT",
            "Integer": "INTEGER",
            "Float": "REAL",
            "Category": "TEXT",
            "Boolean": "INTEGER",
            "Text": "TEXT"
        }
        cols_sql = ", ".join([f"'{col}' {sql_types[typ]}" for col, typ in col_defs])
        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS '{table_name}' ({cols_sql})")
            conn.commit()
            # Insert data
            for _, row in df.iterrows():
                values = []
                for col, typ in col_defs:
                    val = row[col]
                    if pd.isnull(val):
                        values.append("NULL")
                    elif typ in ["ID", "Integer", "Boolean"]:
                        values.append(str(val))
                    else:
                        values.append(f"'{str(val).replace('\'','\\\'')}'")
                values_sql = ", ".join(values)
                cursor.execute(f"INSERT INTO '{table_name}' VALUES ({values_sql})")
            conn.commit()
            st.success(f"Generated and inserted `{num_rows}` rows into `{table_name}`!")
        except Exception as e:
            st.error(f"Error creating/inserting: {e}")

    if st.button("← Back"):
        navigate_to("Welcome")
