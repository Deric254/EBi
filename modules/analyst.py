import streamlit as st
import pandas as pd
from utils import navigate_to

def show(conn):
    st.subheader("🧠 Analyst Playground")

    cursor = conn.cursor()

    # Show current database and allow switching
    cursor.execute("SHOW DATABASES")
    dbs = [db[0] for db in cursor.fetchall()]
    current_db = st.session_state.get("selected_db", dbs[0] if dbs else None)
    selected_db = st.selectbox("Current Database", dbs, index=dbs.index(current_db) if current_db in dbs else 0)
    if selected_db != current_db:
        st.session_state["selected_db"] = selected_db
        current_db = selected_db
    cursor.execute(f"USE `{current_db}`")

    # Preview tables in current database
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    st.markdown(f"**Tables in `{current_db}`:**")
    st.write(tables)

    # Table selection for analytics
    table = st.selectbox("Select table for analytics", tables) if tables else None

    if table:
        cursor.execute(f"SELECT * FROM `{table}` LIMIT 1000")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)

        st.markdown(f"### 📊 Analytics for `{table}`")
        st.dataframe(df.head(20))

        # GUI analytics: filter, group, aggregate, export
        with st.expander("🔎 Filter & Analyze Data"):
            filter_col = st.selectbox("Filter column", cols)
            filter_val = st.text_input("Filter value")
            filtered_df = df[df[filter_col].astype(str).str.contains(filter_val)] if filter_val else df

            group_col = st.selectbox("Group by column", cols)
            agg_func = st.selectbox("Aggregate function", ["count", "sum", "mean", "min", "max"])
            if st.button("Run Group & Aggregate"):
                grouped = filtered_df.groupby(group_col).agg(agg_func)
                st.write(grouped)

            st.write("Filtered Data Preview", filtered_df.head(20))
            st.download_button("📥 Export Filtered CSV", filtered_df.to_csv(index=False), f"{table}_filtered.csv", "text/csv")

        with st.expander("📈 Quick Stats"):
            st.write(filtered_df.describe(include="all"))

    # Collapsed SQL query area
    with st.expander("🧠 Run Advanced SQL Query"):
        query = st.text_area("Enter SQL query", height=200)
        if st.button("Run Query"):
            try:
                cursor.execute(query)
                if cursor.description:
                    rows = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=cols)
                    st.dataframe(df)
                    st.download_button("📥 Export Results", df.to_csv(index=False), "query_results.csv", "text/csv")
                else:
                    conn.commit()
                    st.success("Query executed successfully.")
            except Exception as e:
                st.error(f"Query error: {e}")

    with st.expander("📘 Analyst Tips"):
        st.markdown("""
        - Use `WITH` for CTEs  
        - Use `JOIN` to combine tables  
        - Use `UPDATE`, `DELETE`, `RENAME` for modifications  
        - Always test with `LIMIT` before running large queries  
        - Visit [EXES Analytics](https://deric-exes-analytics.netlify.app) for more tools
        """)

    # Navigation buttons
    col_back, col_next = st.columns([1, 1], gap="small")
    with col_back:
        if st.button("← Back"):
            navigate_to("Cleaner & Query")
    with col_next:
        if st.button("Next →"):
            navigate_to("Reset")

    # Commented out: Insert CSV and Generate Data buttons
    # if st.button("Insert CSV →"):
    #     navigate_to("Insert CSV")
    # if st.button("Generate Data →"):
    #     navigate_to("Generate Data")
