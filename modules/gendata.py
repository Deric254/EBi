import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
from utils import navigate_to

fake = Faker()

def show(conn):
    st.subheader("🧬 Generate & Insert Synthetic Dataset")

    cursor = conn.cursor()

    st.markdown("#### 1. Table & Columns")
    table_name = st.text_input("Table name", value="synthetic_data")
    num_rows = st.number_input("Number of rows", min_value=10, max_value=100000, value=100)

    st.markdown("Define columns and patterns:")
    col_defs = []
    col_types = ["Name", "Email", "Phone", "Address", "Date", "Integer", "Float", "Category", "Boolean", "Text"]
    n_cols = st.number_input("Number of columns", min_value=1, max_value=20, value=5)
    for i in range(n_cols):
        col1, col2 = st.columns([2,2])
        with col1:
            col_name = st.text_input(f"Column {i+1} name", value=f"col_{i+1}", key=f"colname_{i}")
        with col2:
            col_type = st.selectbox(f"Type for {col_name}", col_types, key=f"coltype_{i}")
        col_defs.append((col_name, col_type))

    if st.button("Generate & Insert"):
        # Generate data
        data = {}
        for col_name, col_type in col_defs:
            if col_type == "Name":
                data[col_name] = [fake.name() for _ in range(num_rows)]
            elif col_type == "Email":
                data[col_name] = [fake.email() for _ in range(num_rows)]
            elif col_type == "Phone":
                data[col_name] = [fake.phone_number() for _ in range(num_rows)]
            elif col_type == "Address":
                data[col_name] = [fake.address().replace('\n', ', ') for _ in range(num_rows)]
            elif col_type == "Date":
                data[col_name] = [fake.date_between('-5y', 'today') for _ in range(num_rows)]
            elif col_type == "Integer":
                data[col_name] = np.random.randint(0, 1000, num_rows)
            elif col_type == "Float":
                data[col_name] = np.round(np.random.normal(50, 15, num_rows), 2)
            elif col_type == "Category":
                cats = ["A", "B", "C", "D"]
                data[col_name] = np.random.choice(cats, num_rows)
            elif col_type == "Boolean":
                data[col_name] = np.random.choice([0, 1], num_rows)
            elif col_type == "Text":
                data[col_name] = [fake.sentence(nb_words=8) for _ in range(num_rows)]
            else:
                data[col_name] = [None]*num_rows

        df = pd.DataFrame(data)
        st.write("Preview of generated data:", df.head())

        # Create table SQL
        sql_types = {
            "Name": "TEXT",
            "Email": "TEXT",
            "Phone": "TEXT",
            "Address": "TEXT",
            "Date": "TEXT",
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
                    elif typ in ["Name", "Email", "Phone", "Address", "Category", "Text", "Date"]:
                        values.append(f"'{str(val).replace('\'','\\\'')}'")
                    elif typ == "Boolean":
                        values.append(str(int(val)))
                    else:
                        values.append(str(val))
                values_sql = ", ".join(values)
                cursor.execute(f"INSERT INTO '{table_name}' VALUES ({values_sql})")
            conn.commit()
            st.success(f"Generated and inserted `{num_rows}` rows into `{table_name}`!")
        except Exception as e:
            st.error(f"Error creating/inserting: {e}")

    if st.button("← Back"):
        navigate_to("Welcome")
