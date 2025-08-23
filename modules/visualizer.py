import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
from datetime import datetime

def format_number(n):
    """Format numbers based on their scale, removing .0 for integers"""
    if pd.isnull(n):
        return ""
    n = float(n)
    if abs(n) >= 1_000_000:
        formatted = f"{n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        formatted = f"{n/1_000:.1f}K"
    else:
        formatted = f"{n:.1f}"
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return formatted

def truncate_text(text, max_words=1):
    """Truncate text to a maximum number of words"""
    words = str(text).split()
    if len(words) <= max_words:
        return str(text)
    return " ".join(words[:max_words]) + "..."

def clean_bin_label(x):
    """Clean bin labels and handle invalid cases to create readable ranges"""
    try:
        x_str = str(x).replace('(', '').replace(']', '').replace(', ', '-')
        parts = x_str.split('-')
        # Skip empty or invalid parts
        formatted_parts = [format_number(float(p)) for p in parts if p.strip() and p != 'nan']
        if not formatted_parts:
            return str(x)
        
        # For ranges with multiple parts, ensure a clean range format
        if len(formatted_parts) > 1:
            # Create a clean range format like "0-20", "21-40", etc.
            return f"{formatted_parts[0]}-{formatted_parts[-1]}"
        return '-'.join(formatted_parts)
    except (ValueError, TypeError) as e:
        return str(x)  # Fallback to original string

def intelligent_group(series, y_series, max_categories=10):
    """Group x-axis data by y-axis values into bins if >10 categories and y is numeric"""
    counts = series.value_counts()
    if len(counts) > max_categories and pd.api.types.is_numeric_dtype(y_series):
        try:
            # Filter out NaN values to avoid invalid bins
            valid_data = pd.DataFrame({'x': series, 'y': y_series}).dropna()
            if valid_data.empty:
                st.markdown("<span style='color:#d90429;font-size:14px;'>Cannot group: No valid numeric data in Y-axis.</span>", unsafe_allow_html=True)
                return series
            num_bins = min(5, len(valid_data['y'].unique()))
            if num_bins < 2:
                st.markdown("<span style='color:#d90429;font-size:14px;'>Cannot group: Insufficient unique Y-axis values.</span>", unsafe_allow_html=True)
                return series
            bins = pd.qcut(valid_data['y'], q=num_bins, duplicates='drop')
            df_temp = pd.DataFrame({'x': valid_data['x'], 'y': valid_data['y'], 'bin': bins})
            grouped_data = df_temp.groupby('bin', observed=True)['x'].agg(lambda x: ', '.join(x)).reset_index()
            
            # Create cleaner bin labels that look like "0-20", "21-40", etc.
            grouped_data['bin'] = grouped_data['bin'].apply(clean_bin_label)
            
            # Ensure bins are sorted properly
            grouped_data['sort_key'] = grouped_data['bin'].apply(
                lambda x: float(x.split('-')[0].replace('K', '000').replace('M', '000000'))
                if '-' in x else float(x.replace('K', '000').replace('M', '000000'))
            )
            grouped_data = grouped_data.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
            
            # Map the original values to their bins
            bin_dict = dict(zip(df_temp['x'], df_temp['bin']))
            
            # Calculate how many unique values were grouped
            original_count = len(series.unique())
            new_count = len(grouped_data)
            
            # Store this info for display
            st.session_state[f'grouping_info_{series.name}'] = {
                'original': original_count,
                'grouped': new_count
            }
            
            return series.map(lambda x: bin_dict.get(x, x))
        except Exception as e:
            st.markdown(f"<span style='color:#d90429;font-size:14px;'>Grouping failed: {str(e)}. Using raw data.</span>", unsafe_allow_html=True)
            return series
    return series

def intelligent_group_y(series, x_series, max_categories=10):
    """Group y-axis data by x-axis values into up to 10 groups if >10 categories"""
    counts = series.value_counts()
    if len(counts) > max_categories:
        try:
            x_counts = x_series.value_counts()
            top_x = x_counts.head(max_categories).index
            df_temp = pd.DataFrame({'x': x_series, 'y': series}).dropna()
            grouped_data = df_temp.groupby('x')['y'].agg(lambda x: ', '.join(x)).reset_index()
            grouped_data = grouped_data[grouped_data['x'].isin(top_x)]
            y_to_x = dict(zip(df_temp['y'], df_temp['x']))
            return series.map(lambda y: y_to_x.get(y, y) if y_to_x.get(y) in top_x else y)
        except Exception as e:
            st.markdown(f"<span style='color:#d90429;font-size:14px;'>Y-axis grouping failed: {str(e)}. Using raw data.</span>", unsafe_allow_html=True)
            return series
    return series

def show(df, title="📊 Visualize Data", key=None):
    st.markdown(
        """
        <style>
        div.stAlert p {
            color: #198754 !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.subheader(title)
    if df is None or df.empty:
        st.markdown("<span style='font-weight:bold;color:#198754;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>No data to visualize.</span>", unsafe_allow_html=True)
        return None

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    if not numeric_cols and not categorical_cols:
        st.markdown("<span style='font-weight:bold;color:#198754;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>At least one valid column is required for visualization.</span>", unsafe_allow_html=True)
        return None

    chart_container = st.container()
    chart_col1, chart_col2 = st.columns([1, 1])
    
    with chart_col1:
        columns = df.columns.tolist()
        chart_type = st.selectbox("Chart type", 
                               ["Bar", "Line", "Pie", "Scatter", "Area", "Heatmap", "Pareto"], 
                               key=f"viz_chart_type_{key}")

    with chart_col2:
        chart_size = st.select_slider("Chart size", 
                                    options=["Small", "Medium", "Large"],
                                    value="Small",
                                    key=f"viz_chart_size_{key}")
        sizes = {"Small": (3.5, 2.5), "Medium": (5, 3.5), "Large": (7, 4.5)}
        fig_size = sizes[chart_size]

    col1, col2 = st.columns(2)
    default_x = categorical_cols[0] if categorical_cols else columns[0]
    default_y = numeric_cols[0] if numeric_cols else columns[1] if len(columns) > 1 else columns[0]
    
    with col1:
        x_col = st.selectbox("X axis", columns, index=columns.index(default_x), key=f"viz_x_col_{key}")
    with col2:
        # Allow any column for Y-axis, with preference for numeric when available
        y_col = st.selectbox("Y axis", columns, 
                          index=columns.index(default_y) if default_y in columns else 0, 
                          key=f"viz_y_col_{key}")

    custom_labels = st.expander("Customize Chart Labels", expanded=False)
    with custom_labels:
        col1, col2, col3 = st.columns(3)
        with col1:
            chart_title = st.text_input("Chart Title", value=f"{y_col} by {x_col}", key=f"viz_title_{key}")
        with col2:
            x_axis_label = st.text_input("X-Axis Label", value="Category" if len(df[x_col].unique()) > 10 and pd.api.types.is_numeric_dtype(df[y_col]) else x_col, key=f"viz_xlabel_{key}")
        with col3:
            y_axis_label = st.text_input("Y-Axis Label", value=y_col, key=f"viz_ylabel_{key}")

    agg_method = 'mean'
    if pd.api.types.is_numeric_dtype(df[y_col]) and (len(df[x_col].unique()) > 10 or (pd.api.types.is_numeric_dtype(df[x_col]) and len(df[x_col].unique()) > 10)):
        agg_options = st.expander("📊 Aggregation Options", expanded=True)
        with agg_options:
            st.markdown("<span style='color:black;font-weight:bold;'>Select aggregation for numeric Y-axis</span>", unsafe_allow_html=True)
            agg_method = st.selectbox("Aggregation Method", ["Mean", "Sum"], key=f"agg_method_{key}").lower()

    enable_binning = False
    num_bins = 5
    if pd.api.types.is_numeric_dtype(df[x_col]) and len(df[x_col].unique()) > 10:
        binning_options = st.expander("📊 X-Axis Binning Options", expanded=True)
        with binning_options:
            st.markdown("<span style='color:black;font-weight:bold;'>Group numeric X-axis data into bins</span>", unsafe_allow_html=True)
            enable_binning = st.checkbox("Enable binning for large numeric data", value=True, key=f"enable_binning_{key}")
            if enable_binning:
                col1, col2 = st.columns([1, 1])
                with col1:
                    num_bins = st.number_input("Number of bins", min_value=2, max_value=20, value=5, key=f"num_bins_{key}")
                with col2:
                    bin_method = st.selectbox("Binning method", 
                                           ["Equal width", "Equal frequency", "Custom range"], 
                                           key=f"bin_method_{key}")
                if bin_method == "Custom range":
                    min_val = float(df[x_col].min()) if not df[x_col].isna().all() else 0
                    max_val = float(df[x_col].max()) if not df[x_col].isna().all() else 1
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        bin_start = st.number_input("Start value", value=min_val, key=f"bin_start_{key}")
                    with col2:
                        bin_end = st.number_input("End value", value=max_val, key=f"bin_end_{key}")

    x_data = df[x_col]
    y_data = df[y_col]
    
    # Track original counts for consistent messaging
    original_x_count = len(df[x_col].unique())
    original_y_count = len(df[y_col].unique())
    
    if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
        try:
            if bin_method == "Equal width":
                bins = pd.cut(df[x_col], bins=num_bins)
                df_binned = df.copy()
                df_binned[x_col] = bins
                grouped_data = df_binned.groupby(x_col, observed=True)[y_col].agg([agg_method, 'count']).reset_index()
                grouped_data[x_col] = grouped_data[x_col].apply(clean_bin_label)
                grouped_data['sort_key'] = grouped_data[x_col].apply(
                    lambda x: float(x.split('-')[0].replace('K', '000').replace('M', '000000'))
                    if '-' in x else float(x.replace('K', '000').replace('M', '000000'))
                )
                grouped_data = grouped_data.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
                x_data = grouped_data[x_col]
                y_data = grouped_data[agg_method]
                counts = grouped_data['count']
                st.markdown(f"<span style='color:black;font-style:italic;'>Binned {original_x_count} unique {x_col} values into {len(grouped_data)} groups</span>", unsafe_allow_html=True)
            elif bin_method == "Equal frequency":
                bins = pd.qcut(df[x_col], q=num_bins, duplicates='drop')
                df_binned = df.copy()
                df_binned[x_col] = bins
                grouped_data = df_binned.groupby(x_col, observed=True)[y_col].agg([agg_method, 'count']).reset_index()
                grouped_data[x_col] = grouped_data[x_col].apply(clean_bin_label)
                grouped_data['sort_key'] = grouped_data[x_col].apply(
                    lambda x: float(x.split('-')[0].replace('K', '000').replace('M', '000000'))
                    if '-' in x else float(x.replace('K', '000').replace('M', '000000'))
                )
                grouped_data = grouped_data.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
                x_data = grouped_data[x_col]
                y_data = grouped_data[agg_method]
                counts = grouped_data['count']
                st.markdown(f"<span style='color:black;font-style:italic;'>Binned {original_x_count} unique {x_col} values into {len(grouped_data)} groups with ~{len(df)//num_bins} points per bin</span>", unsafe_allow_html=True)
            else:  # Custom range
                custom_bins = np.linspace(bin_start, bin_end, num_bins + 1)
                bins = pd.cut(df[x_col], bins=custom_bins)
                df_binned = df.copy()
                df_binned[x_col] = bins
                grouped_data = df_binned.groupby(x_col, observed=True)[y_col].agg([agg_method, 'count']).reset_index()
                grouped_data[x_col] = grouped_data[x_col].apply(clean_bin_label)
                grouped_data['sort_key'] = grouped_data[x_col].apply(
                    lambda x: float(x.split('-')[0].replace('K', '000').replace('M', '000000'))
                    if '-' in x else float(x.replace('K', '000').replace('M', '000000'))
                )
                grouped_data = grouped_data.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
                x_data = grouped_data[x_col]
                y_data = grouped_data[agg_method]
                counts = grouped_data['count']
                st.markdown(f"<span style='color:black;font-style:italic;'>Binned {original_x_count} unique {x_col} values using custom range into {len(grouped_data)} groups</span>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<span style='color:#d90429;font-size:14px;'>Binning failed: {str(e)}. Using raw data.</span>", unsafe_allow_html=True)
    else:
        x_data = intelligent_group(df[x_col], df[y_col], max_categories=10)
        if len(df[x_col].unique()) > 10 and pd.api.types.is_numeric_dtype(df[y_col]):
            grouped_count = len(x_data.unique())
            st.markdown(f"<span style='color:black;font-style:italic;'>Grouped {original_x_count} unique {x_col} values into {grouped_count} categories</span>", unsafe_allow_html=True)
    
    if not pd.api.types.is_numeric_dtype(df[y_col]) and len(df[y_col].unique()) > 10:
        y_data = intelligent_group_y(df[y_col], df[x_col], max_categories=10)
        grouped_count = len(y_data.unique())
        st.markdown(f"<span style='color:black;font-style:italic;'>Grouped {original_y_count} unique {y_col} values into {grouped_count} categories</span>", unsafe_allow_html=True)
    
    unique_x = x_data.unique()
    if len(unique_x) <= 10:
        colors = plt.cm.tab10.colors 
    else:
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(unique_x)))

    x_label = x_axis_label if 'x_axis_label' in locals() else "Category" if len(df[x_col].unique()) > 10 and pd.api.types.is_numeric_dtype(df[y_col]) else truncate_text(x_col, 1)
    y_label = y_axis_label if 'y_axis_label' in locals() else truncate_text(y_col, 1)
    
    fig = None
    if x_col == y_col and chart_type != "Pie":
        st.markdown("<span style='color:#198754;font-size:14px;font-weight:bold;'>X and Y axis should be different columns for most chart types.</span>", unsafe_allow_html=True)
    else:
        try:
            if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
                plot_df = pd.DataFrame({x_col: x_data, y_col: y_data})
                if 'counts' in locals():
                    plot_df['count'] = counts
            else:
                plot_df = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            
            if plot_df.empty:
                st.markdown("<span style='color:#198754;font-size:14px;font-weight:bold;'>No data to plot for selected columns.</span>", unsafe_allow_html=True)
            else:
                if chart_type == "Bar":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
                            grouped = plot_df.set_index(x_col)[y_col]
                        else:
                            grouped = plot_df.groupby(x_col)[y_col].agg(agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count')
                        
                        x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                        if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]) and 'count' in plot_df.columns:
                            x_labels = [f"{label} (n={int(plot_df.loc[plot_df[x_col] == idx, 'count'].iloc[0])})" 
                                     for idx, label in zip(grouped.index, x_labels)]
                        
                        # Adjust spacing for better readability if many labels
                        fig_width_per_bar = fig_size[0] / len(grouped)
                        rotation = 45
                        fontsize = 8
                        
                        # Adjust rotation and font size based on number of bars
                        if len(grouped) > 8:
                            rotation = 90
                            fontsize = 7 if len(grouped) <= 15 else 6
                        
                        bars = ax.bar(x_labels, grouped.values, color=colors[:len(grouped.index)])
                        
                        for bar in bars:
                            height = bar.get_height()
                            ax.annotate(format_number(height), 
                                      xy=(bar.get_x() + bar.get_width() / 2, height),
                                      xytext=(0, 3), textcoords="offset points", 
                                      ha='center', va='bottom', fontsize=6, color='black')
                        
                        if len(grouped) > 2 and pd.api.types.is_numeric_dtype(df[y_col]):
                            z = np.polyfit(range(len(grouped)), grouped.values, 1)
                            p = np.poly1d(z)
                            ax.plot(range(len(grouped)), p(range(len(grouped))), 
                                  "r--", alpha=0.7, linewidth=1)
                        
                        ax.set_ylabel(y_label, fontsize=9)
                        ax.set_xlabel(x_label, fontsize=9)
                        
                        # Improve label spacing to avoid overlap
                        plt.xticks(rotation=rotation, ha='right' if rotation < 90 else 'center', fontsize=fontsize)
                        plt.yticks(fontsize=8)
                        
                        # Add spacing at the bottom for rotated labels
                        plt.subplots_adjust(bottom=0.2 if rotation > 0 else 0.15)
                        
                        if pd.api.types.is_numeric_dtype(df[y_col]):
                            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Bar chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Line":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        grouped = plot_df.groupby(x_col)[y_col].agg(agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count')
                        x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                        
                        # Adjust spacing for better readability
                        rotation = 45
                        fontsize = 8
                        if len(grouped) > 8:
                            rotation = 90
                            fontsize = 7 if len(grouped) <= 15 else 6
                            
                        ax.plot(x_labels, grouped.values, marker='o', color=colors[0], 
                              linewidth=2, markersize=5)
                        for i, v in enumerate(grouped.values):
                            ax.annotate(format_number(v), 
                                      xy=(i, v), xytext=(0, 5), 
                                      textcoords="offset points", 
                                      ha='center', fontsize=6, color='black')
                        if len(grouped) > 3 and pd.api.types.is_numeric_dtype(df[y_col]):
                            window = min(3, len(grouped)-1)
                            rolling_mean = grouped.rolling(window=window, center=True).mean()
                            ax.plot(x_labels, rolling_mean, 'r--', linewidth=1.5, alpha=0.7, 
                                  label='Trend')
                            ax.legend(fontsize=8, loc='best')
                        ax.set_ylabel(y_label, fontsize=9)
                        ax.set_xlabel(x_label, fontsize=9)
                        
                        # Improve label spacing
                        plt.xticks(rotation=rotation, ha='right' if rotation < 90 else 'center', fontsize=fontsize)
                        plt.yticks(fontsize=8)
                        
                        # Add spacing at the bottom for rotated labels
                        plt.subplots_adjust(bottom=0.2 if rotation > 0 else 0.15)
                        
                        if pd.api.types.is_numeric_dtype(df[y_col]):
                            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        plt.grid(True, linestyle='--', alpha=0.3)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Line chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Scatter":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        if len(plot_df) > 100:
                            plot_df = plot_df.sample(100)
                        if len(plot_df) > 2 and pd.api.types.is_numeric_dtype(plot_df[x_col]) and pd.api.types.is_numeric_dtype(plot_df[y_col]):
                            z = np.polyfit(plot_df[x_col], plot_df[y_col], 1)
                            p = np.poly1d(z)
                            x_range = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 100)
                            ax.plot(x_range, p(x_range), "r--", alpha=0.7, linewidth=1.5, label='Trend')
                        ax.scatter(plot_df[x_col], plot_df[y_col], 
                                 c=colors[0], alpha=0.6, s=30)
                        ax.set_ylabel(y_label, fontsize=9)
                        ax.set_xlabel(x_label, fontsize=9)
                        plt.xticks(fontsize=8, rotation=45, ha='right')
                        plt.yticks(fontsize=8)
                        if pd.api.types.is_numeric_dtype(plot_df[y_col]):
                            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        if pd.api.types.is_numeric_dtype(plot_df[x_col]):
                            ax.xaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        plt.grid(True, linestyle='--', alpha=0.3)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Scatter chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Pie":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        pie_data = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
                        grouped = pie_data.groupby(x_col)[y_col].agg(agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count')
                        labels = [truncate_text(l, 1) for l in grouped.index]
                        autopct_func = lambda pct: f"{pct:.1f}%"
                        wedges, texts, autotexts = ax.pie(
                            grouped.values, 
                            labels=labels, 
                            autopct=autopct_func if grouped.values.sum() > 0 else None,
                            colors=colors[:len(grouped)], 
                            textprops={'fontsize': 6, 'color': 'black'},
                            wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
                        )
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Pie chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Area":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        grouped = plot_df.groupby(x_col)[y_col].agg(agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count')
                        x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                        ax.fill_between(x_labels, grouped.values, alpha=0.4, color=colors[0])
                        ax.plot(x_labels, grouped.values, color=colors[0], linewidth=2)
                        for i, v in enumerate(grouped.values):
                            ax.annotate(format_number(v), 
                                      xy=(i, v), xytext=(0, 5), 
                                      textcoords="offset points", 
                                      ha='center', fontsize=6, color='black')
                        if len(grouped) > 2 and pd.api.types.is_numeric_dtype(df[y_col]):
                            z = np.polyfit(range(len(grouped)), grouped.values, 1)
                            p = np.poly1d(z)
                            ax.plot(range(len(grouped)), p(range(len(grouped))), 
                                  "r--", alpha=0.7, linewidth=1.5, label='Trend')
                            ax.legend(fontsize=8, loc='upper left')
                        ax.set_ylabel(y_label, fontsize=9)
                        ax.set_xlabel(x_label, fontsize=9)
                        plt.xticks(rotation=45, ha='right', fontsize=8)
                        plt.yticks(fontsize=8)
                        if pd.api.types.is_numeric_dtype(df[y_col]):
                            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Area chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Heatmap":
                    try:
                        cat_cols = [c for c in df.columns if c != x_col and c != y_col 
                                   and len(df[c].unique()) <= 20]
                        if not cat_cols:
                            st.markdown("<span style='color:#d90429;font-size:14px;'>Heatmap requires at least one more categorical column.</span>", unsafe_allow_html=True)
                        else:
                            heatmap_col = st.selectbox("Heatmap category column", 
                                                     cat_cols, key=f"viz_heatmap_col_{key}")
                            fig, ax = plt.subplots(figsize=fig_size)
                            heatmap_data = df.pivot_table(
                                index=heatmap_col, 
                                columns=x_col, 
                                values=y_col, 
                                aggfunc=agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count'
                            )
                            row_labels = [truncate_text(r, 1) for r in heatmap_data.index]
                            col_labels = [truncate_text(c, 1) for c in heatmap_data.columns]
                            im = ax.imshow(heatmap_data, cmap='viridis')
                            ax.set_xticks(np.arange(len(col_labels)))
                            ax.set_yticks(np.arange(len(row_labels)))
                            ax.set_xticklabels(col_labels, fontsize=8)
                            ax.set_yticklabels(row_labels, fontsize=8)
                            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
                            cbar.ax.tick_params(labelsize=8)
                            for i in range(len(row_labels)):
                                for j in range(len(col_labels)):
                                    value = heatmap_data.iloc[i, j]
                                    if not pd.isna(value):
                                        ax.text(j, i, format_number(value),
                                              ha="center", va="center", 
                                              color="white" if value > heatmap_data.mean().mean() else "black",
                                              fontsize=6)
                            ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                            plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Heatmap failed: {str(e)}</span>", unsafe_allow_html=True)
                
                elif chart_type == "Pareto":
                    try:
                        fig, ax1 = plt.subplots(figsize=fig_size)
                        pareto_data = plot_df.groupby(x_col)[y_col].agg(agg_method if pd.api.types.is_numeric_dtype(df[y_col]) else 'count')
                        pareto_data = pareto_data.sort_values(ascending=False)
                        cumpercentage = pareto_data.cumsum() / pareto_data.sum() * 100
                        x_labels = [truncate_text(idx, 1) for idx in pareto_data.index]
                        
                        # Adjust label rotation and spacing for better readability
                        rotation = 45
                        fontsize = 8
                        if len(pareto_data) > 8:
                            rotation = 90
                            fontsize = 7 if len(pareto_data) <= 15 else 6
                        
                        bars = ax1.bar(x_labels, pareto_data, color=colors[0])
                        ax2 = ax1.twinx()
                        ax2.plot(x_labels, cumpercentage, 'bo-', linewidth=2, markersize=4, color='red')
                        ax2.set_ylim([0, 105])
                        ax2.set_ylabel('Cumulative %', fontsize=9)
                        ax2.tick_params(axis='y', labelsize=8)
                        
                        # Only annotate values if there's reasonable space
                        if len(pareto_data) <= 10:
                            for i, bar in enumerate(bars):
                                height = bar.get_height()
                                ax1.annotate(format_number(height), 
                                          xy=(bar.get_x() + bar.get_width() / 2, height),
                                          xytext=(0, 3), textcoords="offset points", 
                                          ha='center', va='bottom', fontsize=6, color='black')
                                
                                # Only annotate percentage points if not too crowded
                                if i % max(1, len(pareto_data) // 5) == 0:
                                    ax2.annotate(f"{cumpercentage.iloc[i]:.1f}%", 
                                              xy=(i, cumpercentage.iloc[i]),
                                              xytext=(0, 5), textcoords="offset points", 
                                              ha='center', fontsize=6, color='red')
                        
                        ax1.set_ylabel(y_label, fontsize=9)
                        ax1.set_xlabel(x_label, fontsize=9)
                        
                        # Improve label spacing
                        plt.xticks(rotation=rotation, ha='right' if rotation < 90 else 'center', fontsize=fontsize)
                        
                        # Add bottom padding for rotated labels
                        plt.subplots_adjust(bottom=0.2 if rotation > 0 else 0.15)
                        
                        ax1.tick_params(axis='y', labelsize=8)
                        if pd.api.types.is_numeric_dtype(df[y_col]):
                            ax1.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
                                lambda x, p: format_number(x)))
                        ax1.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        ax1.spines['top'].set_visible(False)
                        ax1.spines['right'].set_visible(False)
                        plt.tight_layout()
                    except Exception as e:
                        st.markdown(f"<span style='color:#d90429;font-size:14px;'>Pareto chart failed: {str(e)}</span>", unsafe_allow_html=True)
                
                if fig:
                    st.pyplot(fig)
                    
                if len(numeric_cols) > 1 and len(columns) > 2:
                    with st.expander("Generate Multiple Visualizations", expanded=False):
                        st.markdown("<span style='color:black;font-weight:bold;'>Automatically visualize all numeric columns against categorical columns</span>", unsafe_allow_html=True)
                        if st.button("Generate Multiple Charts", key=f"multi_charts_{key}"):
                            cat_cols = [c for c in columns if c not in numeric_cols]
                            if not cat_cols:
                                st.info("No categorical columns found for additional visualizations.")
                            else:
                                max_charts = min(5, len(numeric_cols) * len(cat_cols))
                                chart_pairs = []
                                for num_col in numeric_cols[:3]:
                                    for cat_col in cat_cols[:2]:
                                        if num_col != cat_col:
                                            chart_pairs.append((cat_col, num_col))
                                
                                for i, (x, y) in enumerate(chart_pairs[:max_charts]):
                                    default_title = f"Distribution of {y} by {x}"
                                    chart_title = st.text_input(
                                        f"Chart Title {i+1}", 
                                        value=default_title, 
                                        key=f"multi_chart_title_{i}_{key}"
                                    )
                                    st.markdown(f"##### {chart_title}")
                                    x_data = intelligent_group(df[x], df[y], max_categories=10)
                                    y_data = df[y]
                                    if not pd.api.types.is_numeric_dtype(df[y]) and len(df[y].unique()) > 10:
                                        y_data = intelligent_group_y(df[y], df[x], max_categories=10)
                                    try:
                                        plot_df = pd.DataFrame({x: x_data, y: y_data}).dropna()
                                        if not plot_df.empty:
                                            fig, ax = plt.subplots(figsize=sizes["Small"])
                                            grouped = plot_df.groupby(x)[y].agg(agg_method if pd.api.types.is_numeric_dtype(df[y]) else 'count')
                                            x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                                            
                                            if len(grouped) <= 5:
                                                autopct_func = lambda pct: f"{pct:.1f}%"
                                                wedges, texts, autotexts = ax.pie(
                                                    grouped.values,
                                                    labels=x_labels,
                                                    autopct=autopct_func,
                                                    colors=colors[:len(grouped)],
                                                    textprops={'fontsize': 6, 'color': 'black'},
                                                    wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
                                                )
                                                ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                                            elif pd.api.types.is_numeric_dtype(df[x]) and pd.api.types.is_numeric_dtype(df[y]):
                                                ax.scatter(plot_df[x], plot_df[y], 
                                                         c=colors[0], alpha=0.6, s=30)
                                                if len(plot_df) > 2:
                                                    z = np.polyfit(plot_df[x], plot_df[y], 1)
                                                    p = np.poly1d(z)
                                                    x_range = np.linspace(plot_df[x].min(), plot_df[x].max(), 100)
                                                    ax.plot(x_range, p(x_range), "r--", alpha=0.7, linewidth=1.5)
                                                ax.set_ylabel(truncate_text(y, 1), fontsize=9)
                                                ax.set_xlabel(truncate_text(x, 1), fontsize=9)
                                                ax.xaxis.set_major_formatter(mticker.FuncFormatter(
                                                    lambda x, p: format_number(x)))
                                                ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                                                ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                                    lambda x, p: format_number(x)))
                                                ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                                                plt.grid(True, linestyle='--', alpha=0.3)
                                            else:
                                                bars = ax.bar(x_labels, grouped.values, color=colors[:len(grouped.index)])
                                                for bar in bars:
                                                    height = bar.get_height()
                                                    ax.annotate(format_number(height), 
                                                              xy=(bar.get_x() + bar.get_width() / 2, height),
                                                              xytext=(0, 3), textcoords="offset points", 
                                                              ha='center', va='bottom', fontsize=6, color='black')
                                                ax.set_ylabel(truncate_text(y, 1), fontsize=9)
                                                ax.set_xlabel(truncate_text(x, 1), fontsize=9)
                                                plt.xticks(rotation=45, ha='right', fontsize=8)
                                                plt.yticks(fontsize=8)
                                                if pd.api.types.is_numeric_dtype(df[y]):
                                                    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))
                                                    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                                        lambda x, p: format_number(x)))
                                                ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                                                ax.spines['top'].set_visible(False)
                                                ax.spines['right'].set_visible(False)
                                            plt.tight_layout()
                                            st.pyplot(fig)
                                            
                                            insights_col1, insights_col2 = st.columns([1, 1])
                                            with insights_col1:
                                                st.markdown("<span style='color:black;font-weight:bold;padding:4px 8px;border-radius:4px;'>Quick Insights:</span>", unsafe_allow_html=True)
                                                if pd.api.types.is_numeric_dtype(y_data):
                                                    metrics = {
                                                        "Average": format_number(y_data.mean()),
                                                        "Max": format_number(y_data.max()),
                                                        "Min": format_number(y_data.min())
                                                    }
                                                    metrics_cols = st.columns(3)
                                                    for j, (label, value) in enumerate(metrics.items()):
                                                        with metrics_cols[j]:
                                                            st.markdown(f"<span style='color:black;font-size:12px;'>{label}: {value}</span>", unsafe_allow_html=True)
                                            with insights_col2:
                                                st.markdown(f"<span style='color:black;font-weight:bold;padding:4px 8px;border-radius:4px;'>Top {x} values:</span>", unsafe_allow_html=True)
                                                top_values = x_data.value_counts().head(3)
                                                for val, count in top_values.items():
                                                    st.markdown(f"<span style='color:black;font-size:12px;'><b>{truncate_text(val)}:</b> {format_number(count)}</span>", unsafe_allow_html=True)
                                    except Exception as e:
                                        st.markdown(f"<span style='color:#d90429;font-size:12px;font-weight:bold;'>Could not generate chart for {y} by {x}: {str(e)}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<span style='color:#d90429;font-size:14px;font-weight:bold;'>Cannot plot: {str(e)}</span>", unsafe_allow_html=True)

    insights_col1, insights_col2 = st.columns([1, 1])
    
    with insights_col1:
        st.markdown("<span style='color:black;font-weight:bold;padding:4px 8px;border-radius:4px;'>Quick Insights:</span>", unsafe_allow_html=True)
        if pd.api.types.is_numeric_dtype(y_data):
            try:
                metrics = {
                    "Average": format_number(y_data.mean()),
                    "Max": format_number(y_data.max()),
                    "Min": format_number(y_data.min())
                }
                metrics_cols = st.columns(3)
                for i, (label, value) in enumerate(metrics.items()):
                    with metrics_cols[i]:
                        st.markdown(f"<span style='color:black;font-size:12px;'>{label}: {value}</span>", unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"<span style='color:#d90429;font-size:12px;'>Quick Insights failed: {str(e)}</span>", unsafe_allow_html=True)
    
    with insights_col2:
        st.markdown(f"<span style='color:black;font-weight:bold;padding:4px 8px;border-radius:4px;'>Top {x_label} values:</span>", unsafe_allow_html=True)
        try:
            top_values = x_data.value_counts().head(3)
            for i, (val, count) in enumerate(top_values.items()):
                st.markdown(f"<span style='color:black;font-size:12px;'><b>{truncate_text(val)}:</b> {format_number(count)}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<span style='color:#d90429;font-size:12px;'>Top values failed: {str(e)}</span>", unsafe_allow_html=True)
    
    saved_path = None
    if fig and st.button("Download Visual"):
        visuals_dir = os.path.join("my_projects", "visuals")
        os.makedirs(visuals_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{chart_type.lower()}_{timestamp}.png"
        temp_path = os.path.join(os.getcwd(), fname)
        fig.savefig(temp_path, bbox_inches='tight', dpi=150)
        save_path = os.path.join(visuals_dir, fname)
        try:
            os.replace(temp_path, save_path)
            st.success(f"Visual saved to My Projects")
            saved_path = save_path
        except Exception as e:
            st.error(f"Error saving: {e}")
            save_path = None
    
    return saved_path