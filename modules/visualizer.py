import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

def intelligent_group(series, max_categories=6):
    counts = series.value_counts()
    if len(counts) > max_categories:
        top = counts.nlargest(max_categories)
        grouped = series.apply(lambda x: x if x in top.index else "Other")
        return grouped
    return series

def show(df, title="📊 Visualize Data", save_name=None):
    st.subheader(title)
    if df is None or df.empty:
        st.info("No data to visualize.")
        return None

    columns = df.columns.tolist()
    chart_type = st.selectbox("Chart type", ["Bar", "Line", "Pie", "Scatter"], key="viz_chart_type")

    default_x = columns[0]
    default_y = columns[1] if len(columns) > 1 else columns[0]

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("X axis", columns, index=columns.index(default_x), key="viz_x_col")
    with col2:
        y_col = st.selectbox("Y axis", columns, index=columns.index(default_y), key="viz_y_col")

    x_data = intelligent_group(df[x_col])
    y_data = df[y_col]
    colors = plt.cm.tab10.colors if len(x_data.unique()) <= 10 else plt.cm.Set3.colors

    fig = None
    if x_col == y_col:
        st.warning("X and Y axis must be different columns for visualization.")
    elif chart_type in ["Bar", "Line", "Scatter"]:
        try:
            plot_df = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            if plot_df.empty:
                st.info("No data to plot for selected columns.")
            else:
                if chart_type == "Bar":
                    fig, ax = plt.subplots()
                    grouped = plot_df.groupby(x_col)[y_col].sum()
                    bars = ax.bar(grouped.index, grouped.values, color=colors[:len(grouped.index)])
                    # Add data labels
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
                    ax.set_ylabel(y_col)
                    ax.set_xlabel(x_col)
                    plt.xticks(rotation=45)
                elif chart_type == "Line":
                    fig, ax = plt.subplots()
                    grouped = plot_df.groupby(x_col)[y_col].sum()
                    ax.plot(grouped.index, grouped.values, marker='o', color=colors[0])
                    for i, v in enumerate(grouped.values):
                        ax.annotate(f'{v:.2f}', xy=(grouped.index[i], v), xytext=(0, 5), textcoords="offset points", ha='center', fontsize=8)
                    ax.set_ylabel(y_col)
                    ax.set_xlabel(x_col)
                    plt.xticks(rotation=45)
                elif chart_type == "Scatter":
                    fig, ax = plt.subplots()
                    ax.scatter(plot_df[x_col], plot_df[y_col], c=np.arange(len(plot_df)), cmap='tab10')
                    ax.set_ylabel(y_col)
                    ax.set_xlabel(x_col)
                    plt.xticks(rotation=45)
            if fig:
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Cannot plot: {e}")
    elif chart_type == "Pie":
        try:
            pie_data = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            grouped = pie_data.groupby(x_col)[y_col].sum().reset_index()
            if grouped.empty or grouped[x_col].ndim != 1 or grouped[y_col].ndim != 1:
                st.info("Cannot plot pie chart for selected columns.")
            else:
                fig, ax = plt.subplots()
                wedges, texts, autotexts = ax.pie(grouped[y_col], labels=grouped[x_col], autopct='%1.1f%%',
                                                  colors=colors[:len(grouped[x_col])], textprops={'fontsize': 8})
                for text in autotexts:
                    text.set_color('black')
                ax.set_title(f"{y_col} by {x_col}")
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Cannot plot pie chart: {e}")

    st.markdown("**Insights:**")
    st.write("Summary statistics for selected data:")
    st.write(df.describe(include="all"))
    st.write("Top values for X axis:")
    st.write(x_data.value_counts().head())

    # Save visual to my_projects/visuals
    saved_path = None
    if fig and st.button("Download Visual"):
        visuals_dir = os.path.join("my_projects", "visuals")
        os.makedirs(visuals_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = save_name or f"visual_{timestamp}.png"
        save_path = os.path.join(visuals_dir, fname)
        fig.savefig(save_path, bbox_inches='tight')
        st.success(f"Visual saved as {fname} in my_projects/visuals")
        saved_path = save_path
    return saved_path
