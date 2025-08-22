import streamlit as st
import pandas as pd
import numpy as np
from utils import navigate_to

def show(conn):
    table = st.session_state.get("selected_table")
    if not table:
        st.warning("Please select a table first.")
        return

    st.subheader(f"🧹 Cleaner & Query for `{table}`")
    cursor = conn.cursor()

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

        # Checkboxes and labels in the same line
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
            suggest_types = st.checkbox("", value=True, key="suggest_types")
        with col2:
            st.markdown("<span style='color:black'>Suggest column types</span>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 8])
        with col1:
            detect_outliers = st.checkbox("", value=True, key="detect_outliers")
        with col2:
            st.markdown("<span style='color:black'>Detect numeric outliers</span>", unsafe_allow_html=True)

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

        if suggest_types:
            with st.expander("📊 Suggested Column Types"):
                st.write(cleaned_df.dtypes)

        if detect_outliers:
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

        # Collapsed manual SQL query area
        with st.expander("🧠 Run Manual SQL Query"):
            query = st.text_area("Enter SQL query")
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
        st.error(f"Error loading or cleaning data: {e}")
