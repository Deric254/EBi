import streamlit as st
import pandas as pd
from utils import navigate_to
from modules import visualizer
import os
from datetime import datetime

def show(conn):
    st.subheader("🧠 Analyst Playground")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    st.markdown(f"**Tables in database:**")
    st.write(tables)

    current_table = st.session_state.get("selected_table", tables[0] if tables else None)
    table = current_table

    if table:
        cursor.execute(f"SELECT * FROM '{table}' LIMIT 1000")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)

        result_dfs = {"Full Table": df}

        # --- SELECT columns ---
        with st.expander("🔎 Select Columns", expanded=False):
            col1, col2 = st.columns([2, 2])
            with col1:
                selected_cols = st.multiselect("Columns", cols, default=cols)
            with col2:
                st.markdown("Tip: Hold Ctrl/Cmd to select multiple columns.")
            st.dataframe(df[selected_cols].head(20))
            if st.button("Visualize This Table", key="viz_selected_cols_btn"):
                if not df[selected_cols].empty and any(pd.api.types.is_numeric_dtype(df[col]) for col in selected_cols):
                    visualizer.show(df[selected_cols], title="Visualize: Selected Columns", key="viz_selected_cols")
                else:
                    st.warning("No numeric columns to visualize.")
            result_dfs["Selected Columns"] = df[selected_cols]

        # --- FILTER rows ---
        with st.expander("🔍 Filter Rows (WHERE)", expanded=False):
            col1, col2 = st.columns([2, 2])
            with col1:
                filter_col = st.selectbox("Column to filter", cols, key="filter_col")
            with col2:
                filter_val = st.text_input("Value to filter (contains)", key="filter_val")
            filtered_df = df[df[filter_col].astype(str).str.contains(filter_val)] if filter_val else df
            st.dataframe(filtered_df[selected_cols].head(20))
            if st.button("Visualize This Table", key="viz_filtered_rows_btn"):
                if not filtered_df[selected_cols].empty and any(pd.api.types.is_numeric_dtype(filtered_df[col]) for col in selected_cols):
                    visualizer.show(filtered_df[selected_cols], title="Visualize: Filtered Rows", key="viz_filtered_rows")
                else:
                    st.warning("No numeric columns to visualize.")
            st.markdown("Tip: Type part of a value to match rows.")
            result_dfs["Filtered Rows"] = filtered_df[selected_cols]

        # --- GROUP BY & AGGREGATE ---
        with st.expander("📊 Group & Aggregate", expanded=False):
            st.markdown("""
            <b>Group & Aggregate lets you summarize your data:</b><br>
            - <b>Group by column:</b> Choose a column to group your data (e.g., by category, date, etc.)<br>
            - <b>Aggregate function:</b> Choose how to summarize each group:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>count</b>: Number of rows<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>sum</b>: Total of numeric values<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>mean</b>: Average of numeric values<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>min</b>: Minimum value<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>max</b>: Maximum value<br>
            <span style='color:#d90429;font-weight:bold;'>If you choose a non-numeric column for sum/mean/min/max, you may get an error. Only use these on numeric columns.</span>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([2, 2])
            with col1:
                group_col = st.selectbox("Group by column", cols, key="group_col")
            with col2:
                agg_func = st.selectbox("Aggregate function", ["count", "sum", "mean", "min", "max"], key="agg_func")
            if st.button("Run Group & Aggregate", key="run_group"):
                try:
                    grouped = df.groupby(group_col)[selected_cols].agg(agg_func)
                    st.write(grouped)
                    result_dfs["Group & Aggregate"] = grouped
                except Exception as e:
                    st.markdown(f"<span style='color:#d90429;font-weight:bold;'>Aggregation failed: {e}</span>", unsafe_allow_html=True)
            st.markdown("Tip: Use group and aggregate to summarize your data.")

        # --- JOIN tables ---
        with st.expander("🔗 Join Tables", expanded=False):
            st.markdown("Combine data from two tables using different join types.")
            if len(tables) > 1:
                col1, col2 = st.columns([2, 2])
                with col1:
                    join_table = st.selectbox("Table to join", [t for t in tables if t != table], key="join_table")
                    join_type = st.selectbox("Join type", ["INNER", "LEFT", "RIGHT", "FULL"], key="join_type")
                with col2:
                    join_col_self = st.selectbox("Join column in current table", cols, key="join_col_self")
                    cursor.execute(f"PRAGMA table_info('{join_table}')")
                    join_table_cols = [row[1] for row in cursor.fetchall()]
                    join_col_other = st.selectbox("Join column in other table", join_table_cols, key="join_col_other")
                if st.button("Run JOIN", key="run_join"):
                    # SQLite does not support RIGHT/FULL JOIN natively, so emulate with UNION for FULL and swap for RIGHT
                    if join_type == "INNER":
                        query = f"""
                        SELECT a.*, b.*
                        FROM '{table}' a
                        INNER JOIN '{join_table}' b
                        ON a."{join_col_self}" = b."{join_col_other}"
                        LIMIT 100
                        """
                    elif join_type == "LEFT":
                        query = f"""
                        SELECT a.*, b.*
                        FROM '{table}' a
                        LEFT JOIN '{join_table}' b
                        ON a."{join_col_self}" = b."{join_col_other}"
                        LIMIT 100
                        """
                    elif join_type == "RIGHT":
                        query = f"""
                        SELECT b.*, a.*
                        FROM '{join_table}' b
                        LEFT JOIN '{table}' a
                        ON b."{join_col_other}" = a."{join_col_self}"
                        LIMIT 100
                        """
                    elif join_type == "FULL":
                        query = f"""
                        SELECT a.*, b.*
                        FROM '{table}' a
                        LEFT JOIN '{join_table}' b
                        ON a."{join_col_self}" = b."{join_col_other}"
                        UNION
                        SELECT a.*, b.*
                        FROM '{table}' a
                        RIGHT JOIN '{join_table}' b
                        ON a."{join_col_self}" = b."{join_col_other}"
                        LIMIT 100
                        """
                    try:
                        cursor.execute(query)
                        join_rows = cursor.fetchall()
                        join_cols = [desc[0] for desc in cursor.description]
                        join_df = pd.DataFrame(join_rows, columns=join_cols)
                        st.dataframe(join_df)
                        if st.button("Visualize This Table", key="viz_join_result_btn"):
                            if not join_df.empty and any(pd.api.types.is_numeric_dtype(join_df[col]) for col in join_df.columns):
                                visualizer.show(join_df, title="Visualize: Join Result", key="viz_join_result")
                            else:
                                st.warning("No numeric columns to visualize.")
                        result_dfs["Join Result"] = join_df
                    except Exception as e:
                        st.error(f"Join error: {e}")
            else:
                st.info("You need at least two tables to perform a join.")
            st.markdown("Tip: Use JOIN to combine related data from different tables.")

        # --- CTE Example ---
        with st.expander("🧬 CTE (Common Table Expression)", expanded=False):
            col1, col2 = st.columns([2, 2])
            with col1:
                cte_query = st.text_area("CTE SQL", value=f"WITH temp AS (SELECT * FROM '{table}' LIMIT 10) SELECT * FROM temp", key="cte_query", height=100)
            with col2:
                st.markdown("Tip: Use CTEs for advanced queries and temporary results.")
            if st.button("Run CTE Query", key="run_cte"):
                try:
                    cursor.execute(cte_query)
                    cte_rows = cursor.fetchall()
                    cte_cols = [desc[0] for desc in cursor.description]
                    cte_df = pd.DataFrame(cte_rows, columns=cte_cols)
                    st.dataframe(cte_df)
                    if st.button("Visualize This Table", key="viz_cte_result_btn"):
                        if not cte_df.empty and any(pd.api.types.is_numeric_dtype(cte_df[col]) for col in cte_df.columns):
                            visualizer.show(cte_df, title="Visualize: CTE Result", key="viz_cte_result")
                        else:
                            st.warning("No numeric columns to visualize.")
                    result_dfs["CTE Result"] = cte_df
                except Exception as e:
                    st.error(f"CTE error: {e}")

        # --- Export full table ---
        with st.expander("📤 Export Table", expanded=False):
            st.download_button("📥 Export Full Table CSV", df.to_csv(index=False), f"{table}_full.csv", "text/csv")
            # Save exported CSV to my_projects/files
            files_dir = os.path.join("my_projects", "files")
            os.makedirs(files_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_path = os.path.join(files_dir, f"{table}_full_{timestamp}.csv")
            df.to_csv(full_path, index=False)
            st.success(f"Full table CSV saved to My Projects.")

        # --- Quick Stats ---
        with st.expander("📈 Quick Stats", expanded=False):
            st.write(df.describe(include="all"))

        # --- Visualize Results ---
        with st.expander("📊 Visualize Results", expanded=False):
            st.markdown("Select a result to visualize and gain insights.")
            viz_keys = list(result_dfs.keys())
            selected_viz = st.selectbox("Choose result to visualize", viz_keys, key="viz_results_select")
            viz_df = result_dfs[selected_viz] if selected_viz in result_dfs else df

            st.markdown("**Choose chart type:**")
            chart_type = st.selectbox("Chart type", ["Bar", "Line", "Pie", "Scatter"], key=f"viz_chart_type_{selected_viz}")

            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("X axis", viz_df.columns, key=f"viz_x_col_{selected_viz}")
            with col2:
                y_col = st.selectbox("Y axis", viz_df.columns, key=f"viz_y_col_{selected_viz}")

            if x_col == y_col:
                st.warning("X and Y axis must be different columns for visualization.")
            elif chart_type in ["Bar", "Line", "Scatter"]:
                try:
                    plot_df = viz_df[[x_col, y_col]].dropna()
                    if plot_df.empty or not pd.api.types.is_numeric_dtype(plot_df[y_col]):
                        st.info("No numeric data to plot for selected columns.")
                    else:
                        if chart_type == "Bar":
                            st.bar_chart(plot_df.set_index(x_col)[y_col])
                        elif chart_type == "Line":
                            st.line_chart(plot_df.set_index(x_col)[y_col])
                        elif chart_type == "Scatter":
                            st.write("Scatter Plot")
                            st.scatter_chart(plot_df)
                except Exception as e:
                    st.error(f"Cannot plot: {e}")
            elif chart_type == "Pie":
                try:
                    pie_data = viz_df.groupby(x_col)[y_col].sum().reset_index()
                    if pie_data.empty or pie_data[x_col].ndim != 1 or pie_data[y_col].ndim != 1 or not pd.api.types.is_numeric_dtype(pie_data[y_col]):
                        st.info("Cannot plot pie chart for selected columns.")
                    else:
                        st.write("Pie Chart (use matplotlib/seaborn for more options)")
                        import matplotlib.pyplot as plt
                        fig, ax = plt.subplots()
                        ax.pie(pie_data[y_col], labels=pie_data[x_col], autopct='%1.1f%%')
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Cannot plot pie chart: {e}")

            st.markdown("**Insights:**")
            st.write("Summary statistics for selected data:")
            st.write(viz_df.describe(include="all"))
            st.write("Top values for X axis:")
            st.write(viz_df[x_col].value_counts().head())

        # --- Advanced SQL Query ---
        with st.expander("🧠 Run Advanced SQL Query", expanded=False):
            col1, col2 = st.columns([2, 2])
            with col1:
                query = st.text_area("Enter SQL query", height=100, value="", placeholder="Type your SQL query here...", key="advanced_sql")
            with col2:
                st.markdown("Tip: Write any valid SQL. Use LIMIT for safety.")
            if st.button("Run Query", key="run_advanced_sql"):
                try:
                    cursor.execute(query)
                    if cursor.description:
                        rows = cursor.fetchall()
                        cols = [desc[0] for desc in cursor.description]
                        df = pd.DataFrame(rows, columns=cols)
                        st.dataframe(df)
                        st.download_button("📥 Export Results", df.to_csv(index=False), "query_results.csv", "text/csv")
                        # Save query results to my_projects/files
                        files_dir = os.path.join("my_projects", "files")
                        os.makedirs(files_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        query_path = os.path.join(files_dir, f"query_results_{timestamp}.csv")
                        df.to_csv(query_path, index=False)
                        st.success(f"Query results saved to My Projects.")
                    else:
                        conn.commit()
                        st.success("Query executed successfully.")
                except Exception as e:
                    st.error(f"Query error: {e}")

        # --- Analyst Tips ---
        with st.expander("📘 Analyst Tips", expanded=False):
            st.markdown("""
            - Use **Select Columns** to choose what you see  
            - Use **Filter Rows** to narrow down data  
            - Use **Group & Aggregate** to summarize  
            - Use **Join Tables** to combine datasets  
            - Use **CTE** for advanced queries  
            - Use **Export Table** to download your work  
            - Use **Quick Stats** for instant insights  
            - Use **Advanced SQL** for custom logic  
            - Visit [EXES Analytics](https://deric-exes-analytics.netlify.app) for more tools
            """)

        col_back, col_next = st.columns([1, 1], gap="small")
        with col_back:
            if st.button("← Back"):
                navigate_to("Cleaner & Query")
        with col_next:
            if st.button("Next →"):
                navigate_to("Reset")
