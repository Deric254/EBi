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

def show(df, title="📊 Visualize Data", key=None):
    st.subheader(title)
    if df is None or df.empty:
        st.markdown("<span style='font-weight:bold;color:#49A078;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>No data to visualize.</span>", unsafe_allow_html=True)
        return None

    columns = df.columns.tolist()
    chart_type = st.selectbox("Chart type", ["Bar", "Line", "Pie", "Scatter"], key=f"viz_chart_type_{key}")

    default_x = columns[0]
    default_y = columns[1] if len(columns) > 1 else columns[0]

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("X axis", columns, index=columns.index(default_x), key=f"viz_x_col_{key}")
    with col2:
        y_col = st.selectbox("Y axis", columns, index=columns.index(default_y), key=f"viz_y_col_{key}")

    x_data = intelligent_group(df[x_col])
    y_data = df[y_col]
    colors = plt.cm.tab10.colors if len(x_data.unique()) <= 10 else plt.cm.Set3.colors

    fig = None
    if x_col == y_col:
        st.markdown("<span style='font-weight:bold;color:#49A078;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>X and Y axis must be different columns for visualization.</span>", unsafe_allow_html=True)
    elif chart_type in ["Bar", "Line", "Scatter"]:
        try:
            plot_df = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            if plot_df.empty:
                st.markdown("<span style='font-weight:bold;color:#49A078;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>No data to plot for selected columns.</span>", unsafe_allow_html=True)
            else:
                if chart_type == "Bar":
                    fig, ax = plt.subplots()
                    grouped = plot_df.groupby(x_col)[y_col].sum()
                    bars = ax.bar(grouped.index, grouped.values, color=colors[:len(grouped.index)])
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
            st.markdown(f"<span style='font-weight:bold;color:#d90429;background:#fffbe6;padding:6px 16px;border-radius:8px;display:inline-block;'>Cannot plot: {e}</span>", unsafe_allow_html=True)
    elif chart_type == "Pie":
        try:
            pie_data = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            grouped = pie_data.groupby(x_col)[y_col].sum().reset_index()
            if grouped.empty or grouped[x_col].ndim != 1 or grouped[y_col].ndim != 1:
                st.markdown("<span style='font-weight:bold;color:#49A078;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>Cannot plot pie chart for selected columns.</span>", unsafe_allow_html=True)
            else:
                fig, ax = plt.subplots()
                wedges, texts, autotexts = ax.pie(grouped[y_col], labels=grouped[x_col], autopct='%1.1f%%',
                                                  colors=colors[:len(grouped[x_col])], textprops={'fontsize': 8})
                for text in autotexts:
                    text.set_color('black')
                ax.set_title(f"{y_col} by {x_col}")
                st.pyplot(fig)
        except Exception as e:
            st.markdown(f"<span style='font-weight:bold;color:#d90429;background:#fffbe6;padding:6px 16px;border-radius:8px;display:inline-block;'>Cannot plot pie chart: {e}</span>", unsafe_allow_html=True)

    # Show only simple, direct insights for non-technical users
    st.markdown("**Quick Insights:**")
    # Show top values and basic stats only
    st.write(f"Most frequent {x_col}:")
    st.write(x_data.value_counts().head(3))
    if pd.api.types.is_numeric_dtype(y_data):
        st.write(f"Average {y_col}: {y_data.mean():.2f}")
        st.write(f"Max {y_col}: {y_data.max():.2f}")
        st.write(f"Min {y_col}: {y_data.min():.2f}")
    saved_path = None
    if fig and st.button("Download Visual"):
        visuals_dir = os.path.join("my_projects", "visuals")
        os.makedirs(visuals_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"visual_{timestamp}.png"
        temp_path = os.path.join(os.getcwd(), fname)
        fig.savefig(temp_path, bbox_inches='tight')
        save_path = os.path.join(visuals_dir, fname)
        try:
            os.replace(temp_path, save_path)
        except Exception as e:
            st.markdown(f"<span style='font-weight:bold;color:#d90429;background:#fffbe6;padding:6px 16px;border-radius:8px;display:inline-block;'>Error saving visual: {e}</span>", unsafe_allow_html=True)
            save_path = None
        if save_path:
            st.markdown(f"<span style='font-weight:bold;color:#49A078;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>Visual saved as {fname} in my_projects/visuals</span>", unsafe_allow_html=True)
            saved_path = save_path
    return saved_path
