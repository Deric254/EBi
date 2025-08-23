import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.ticker as mticker

def format_number(n):
    """Format large numbers with K/M suffix"""
    if pd.isnull(n):
        return ""
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return f"{n:.1f}"

def truncate_text(text, max_words=1):
    """Truncate text to a maximum number of words"""
    words = str(text).split()
    if len(words) <= max_words:
        return str(text)
    return " ".join(words[:max_words]) + "..."

def intelligent_group(series, max_categories=6):
    counts = series.value_counts()
    if len(counts) > max_categories:
        top = counts.nlargest(max_categories)
        grouped = series.apply(lambda x: x if x in top.index else "Other")
        return grouped
    return series

def show(df, title="📊 Visualize Data", key=None):
    # Make all Streamlit notifications bold green
    st.markdown(
        """
        <style>
        div.stAlert p {
            color: #198754 !important; /* bootstrap success green */
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

    # Identify numeric columns for visualization
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_cols:
        st.markdown("<span style='font-weight:bold;color:#198754;background:#e8f6ed;padding:6px 16px;border-radius:8px;display:inline-block;'>At least one numeric column is required for visualization.</span>", unsafe_allow_html=True)
        return None

    # Chart selection using compact layout
    chart_container = st.container()
    chart_col1, chart_col2 = st.columns([1, 1])
    
    with chart_col1:
        columns = df.columns.tolist()
        chart_type = st.selectbox("Chart type", 
                               ["Bar", "Line", "Pie", "Scatter", "Area", "Heatmap", "Pareto"], 
                               key=f"viz_chart_type_{key}")

    with chart_col2:
        # Chart size control
        chart_size = st.select_slider("Chart size", 
                                    options=["Small", "Medium", "Large"],
                                    value="Small",
                                    key=f"viz_chart_size_{key}")
        
        sizes = {"Small": (3.5, 2.5), "Medium": (5, 3.5), "Large": (7, 4.5)}
        fig_size = sizes[chart_size]

    # Column selection - ensure at least one is numeric
    col1, col2 = st.columns(2)
    
    # Default to first categorical column for X and first numeric for Y
    categorical_cols = [c for c in columns if c not in numeric_cols]
    default_x = categorical_cols[0] if categorical_cols else columns[0]
    default_y = numeric_cols[0] if numeric_cols else columns[1] if len(columns) > 1 else columns[0]
    
    with col1:
        x_col = st.selectbox("X axis", columns, index=columns.index(default_x), key=f"viz_x_col_{key}")
    with col2:
        y_options = numeric_cols if chart_type in ["Bar", "Line", "Scatter", "Area", "Pareto"] else columns
        y_col = st.selectbox("Y axis", y_options, 
                          index=y_options.index(default_y) if default_y in y_options else 0, 
                          key=f"viz_y_col_{key}")

    # Custom title and axis labels
    custom_labels = st.expander("Customize Chart Labels", expanded=False)
    with custom_labels:
        col1, col2, col3 = st.columns(3)
        with col1:
            chart_title = st.text_input("Chart Title", value=f"{y_col} by {x_col}", key=f"viz_title_{key}")
        with col2:
            x_axis_label = st.text_input("X-Axis Label", value=x_col, key=f"viz_xlabel_{key}")
        with col3:
            y_axis_label = st.text_input("Y-Axis Label", value=y_col, key=f"viz_ylabel_{key}")

    # Add binning options for large numeric data on x-axis
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
                
                # Show custom range inputs if selected
                if bin_method == "Custom range":
                    min_val = float(df[x_col].min())
                    max_val = float(df[x_col].max())
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        bin_start = st.number_input("Start value", value=min_val, key=f"bin_start_{key}")
                    with col2:
                        bin_end = st.number_input("End value", value=max_val, key=f"bin_end_{key}")
    else:
        enable_binning = False

    # Prepare the data
    if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
        # Create the bins based on selected method
        if bin_method == "Equal width":
            # Create equal-width bins across the data range
            bins = pd.cut(df[x_col], bins=num_bins)
            df_binned = df.copy()
            df_binned[x_col] = bins
            # Group and aggregate data
            grouped_data = df_binned.groupby(x_col)[y_col].agg(['mean', 'count']).reset_index()
            # Format bin labels nicely
            grouped_data[x_col] = grouped_data[x_col].astype(str).apply(
                lambda x: x.replace('(', '').replace(']', '').replace(', ', '-')
            )
            # Use the binned data for plotting
            x_data = grouped_data[x_col]
            y_data = grouped_data['mean']
            # Store counts for optional display
            counts = grouped_data['count']
            st.markdown(f"<span style='color:black;font-style:italic;'>Binned {len(df[x_col])} values into {len(grouped_data)} groups</span>", unsafe_allow_html=True)
        elif bin_method == "Equal frequency":
            # Create bins with approximately equal number of points
            bins = pd.qcut(df[x_col], q=num_bins, duplicates='drop')
            df_binned = df.copy()
            df_binned[x_col] = bins
            # Group and aggregate data
            grouped_data = df_binned.groupby(x_col)[y_col].agg(['mean', 'count']).reset_index()
            # Format bin labels nicely
            grouped_data[x_col] = grouped_data[x_col].astype(str).apply(
                lambda x: x.replace('(', '').replace(']', '').replace(', ', '-')
            )
            # Use the binned data for plotting
            x_data = grouped_data[x_col]
            y_data = grouped_data['mean']
            # Store counts for optional display
            counts = grouped_data['count']
            st.markdown(f"<span style='color:black;font-style:italic;'>Binned {len(df[x_col])} values into {len(grouped_data)} groups with ~{len(df)//num_bins} points per bin</span>", unsafe_allow_html=True)
        else:  # Custom range
            # Create custom bins
            custom_bins = np.linspace(bin_start, bin_end, num_bins + 1)
            bins = pd.cut(df[x_col], bins=custom_bins)
            df_binned = df.copy()
            df_binned[x_col] = bins
            # Group and aggregate data
            grouped_data = df_binned.groupby(x_col)[y_col].agg(['mean', 'count']).reset_index()
            # Format bin labels nicely
            grouped_data[x_col] = grouped_data[x_col].astype(str).apply(
                lambda x: x.replace('(', '').replace(']', '').replace(', ', '-')
            )
            # Use the binned data for plotting
            x_data = grouped_data[x_col]
            y_data = grouped_data['mean']
            # Store counts for optional display
            counts = grouped_data['count']
            st.markdown(f"<span style='color:black;font-style:italic;'>Binned {len(df[x_col])} values using custom range into {len(grouped_data)} groups</span>", unsafe_allow_html=True)
    else:
        # Use original data grouping for non-numeric x or when binning is disabled
        x_data = intelligent_group(df[x_col])
        y_data = df[y_col]
    
    # Set consistent color scheme
    if len(x_data.unique()) <= 10:
        colors = plt.cm.tab10.colors 
    else:
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(x_data.unique())))

    # Format axis labels - truncate to one word
    x_label = x_axis_label if 'x_axis_label' in locals() else truncate_text(x_col, 1)
    y_label = y_axis_label if 'y_axis_label' in locals() else truncate_text(y_col, 1)
    
    fig = None
    if x_col == y_col and chart_type != "Pie":
        st.markdown("<span style='color:#198754;font-size:14px;font-weight:bold;'>X and Y axis should be different columns for most chart types.</span>", unsafe_allow_html=True)
    else:
        try:
            # Create the plot dataframe - if we're using binned data, this is already prepared above
            if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
                plot_df = pd.DataFrame({x_col: x_data, y_col: y_data})
                if 'counts' in locals():
                    plot_df['count'] = counts
            else:
                plot_df = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
            
            if plot_df.empty:
                st.markdown("<span style='color:#198754;font-size:14px;font-weight:bold;'>No data to plot for selected columns.</span>", unsafe_allow_html=True)
            else:
                # --- BAR CHART ---
                if chart_type == "Bar":
                    try:
                        fig, ax = plt.subplots(figsize=fig_size)
                        
                        # If using binned data, the grouping is already done
                        if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]):
                            grouped = plot_df.set_index(x_col)[y_col]
                        else:
                            grouped = plot_df.groupby(x_col)[y_col].sum()
                        
                        # Limit to top categories for better readability if not binned
                        if not (enable_binning and pd.api.types.is_numeric_dtype(df[x_col])) and len(grouped) > 8:
                            grouped = grouped.nlargest(8)
                        
                        # Create abbreviated labels for x-axis - one word only
                        x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                        
                        # Add count labels if using binned data
                        if enable_binning and pd.api.types.is_numeric_dtype(df[x_col]) and 'count' in plot_df.columns:
                            # For binned data, show count in parentheses on x-axis labels
                            x_labels = [f"{label} (n={int(plot_df.loc[plot_df[x_col] == idx, 'count'].iloc[0])})" 
                                     for idx, label in zip(grouped.index, x_labels)]
                        
                        bars = ax.bar(x_labels, grouped.values, color=colors[:len(grouped.index)])
                        
                        # Add data labels with formatted numbers
                        for bar in bars:
                            height = bar.get_height()
                            ax.annotate(format_number(height), 
                                      xy=(bar.get_x() + bar.get_width() / 2, height),
                                      xytext=(0, 3), textcoords="offset points", 
                                      ha='center', va='bottom', fontsize=8)
                        
                        # Add trendline
                        if len(grouped) > 2:
                            z = np.polyfit(range(len(grouped)), grouped.values, 1)
                            p = np.poly1d(z)
                            ax.plot(range(len(grouped)), p(range(len(grouped))), 
                                  "r--", alpha=0.7, linewidth=1)
                        
                        # Format axes
                        ax.set_ylabel(y_label, fontsize=9)
                        ax.set_xlabel(x_label, fontsize=9)
                        # Always rotate x-axis labels to prevent overlap
                        plt.xticks(rotation=45, ha='right', fontsize=8)
                        plt.yticks(fontsize=8)
                        
                        # Format y-axis to use K/M notation
                        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                            lambda x, p: format_number(x)))
                        
                        # Add title (bold) with more padding to avoid overlapping with data labels
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        
                        # Clean up the look
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        plt.tight_layout()
                    except Exception as e:
                        st.error(f"An error occurred while plotting: {e}")
                
                # --- LINE CHART ---
                elif chart_type == "Line":
                    fig, ax = plt.subplots(figsize=fig_size)
                    grouped = plot_df.groupby(x_col)[y_col].sum()
                    
                    # Limit to top values for better readability
                    if len(grouped) > 10:
                        grouped = grouped.nlargest(10)
                        
                    # Create abbreviated labels for x-axis - one word only
                    x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                    
                    ax.plot(x_labels, grouped.values, marker='o', color=colors[0], 
                          linewidth=2, markersize=5)
                    
                    # Add data labels with formatted numbers
                    for i, v in enumerate(grouped.values):
                        ax.annotate(format_number(v), 
                                  xy=(i, v), xytext=(0, 5), 
                                  textcoords="offset points", 
                                  ha='center', fontsize=8)
                    
                    # Add moving average trendline
                    if len(grouped) > 3:
                        window = min(3, len(grouped)-1)
                        rolling_mean = grouped.rolling(window=window, center=True).mean()
                        ax.plot(x_labels, rolling_mean, 'r--', linewidth=1.5, alpha=0.7, 
                              label='Trend')
                        ax.legend(fontsize=8, loc='best')
                    
                    # Format axes
                    ax.set_ylabel(y_label, fontsize=9)
                    ax.set_xlabel(x_label, fontsize=9)
                    # Always rotate x-axis labels to prevent overlap
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                    plt.yticks(fontsize=8)
                    
                    # Format y-axis to use K/M notation
                    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                        lambda x, p: format_number(x)))
                    
                    # Add title (bold) with more padding
                    ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                    
                    # Clean up the look
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.grid(True, linestyle='--', alpha=0.3)
                    plt.tight_layout()
                
                # --- SCATTER PLOT ---
                elif chart_type == "Scatter":
                    fig, ax = plt.subplots(figsize=fig_size)
                    
                    # Limit points for better visibility
                    if len(plot_df) > 100:
                        plot_df = plot_df.sample(100)
                    
                    # Add regression line
                    if len(plot_df) > 2 and pd.api.types.is_numeric_dtype(plot_df[x_col]) and pd.api.types.is_numeric_dtype(plot_df[y_col]):
                        z = np.polyfit(plot_df[x_col], plot_df[y_col], 1)
                        p = np.poly1d(z)
                        x_range = np.linspace(plot_df[x_col].min(), plot_df[x_col].max(), 100)
                        ax.plot(x_range, p(x_range), "r--", alpha=0.7, linewidth=1.5, label='Trend')
                        
                    # Create scatter plot
                    ax.scatter(plot_df[x_col], plot_df[y_col], 
                             c=colors[0], alpha=0.6, s=30)
                    
                    # Format axes
                    ax.set_ylabel(y_label, fontsize=9)
                    ax.set_xlabel(x_label, fontsize=9)
                    plt.xticks(fontsize=8, rotation=45, ha='right')
                    plt.yticks(fontsize=8)
                    
                    # Add title (bold) with more padding
                    ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                    
                    # Format axes to use K/M notation for large numbers
                    if pd.api.types.is_numeric_dtype(plot_df[y_col]):
                        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                            lambda x, p: format_number(x)))
                    if pd.api.types.is_numeric_dtype(plot_df[x_col]):
                        ax.xaxis.set_major_formatter(mticker.FuncFormatter(
                            lambda x, p: format_number(x)))
                    
                    # Clean up the look
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.grid(True, linestyle='--', alpha=0.3)
                    plt.tight_layout()
                
                # --- PIE CHART ---
                elif chart_type == "Pie":
                    fig, ax = plt.subplots(figsize=fig_size)
                    pie_data = pd.DataFrame({x_col: x_data, y_col: y_data}).dropna()
                    grouped = pie_data.groupby(x_col)[y_col].sum().reset_index()
                    
                    # Limit to top values for better readability
                    if len(grouped) > 6:
                        top = grouped.nlargest(5, y_col)
                        other_sum = grouped[~grouped[x_col].isin(top[x_col])][y_col].sum()
                        other_row = pd.DataFrame({x_col: ['Other'], y_col: [other_sum]})
                        grouped = pd.concat([top, other_row])
                    
                    # Create abbreviated labels for pie slices - one word only
                    labels = [truncate_text(l, 1) for l in grouped[x_col]]
                    
                    # Format values to appear with K/M notation
                    autopct_func = lambda pct: format_number(pct * grouped[y_col].sum() / 100)
                    
                    wedges, texts, autotexts = ax.pie(
                        grouped[y_col], 
                        labels=labels, 
                        autopct=autopct_func if grouped[y_col].sum() > 0 else None,
                        colors=colors[:len(grouped)], 
                        textprops={'fontsize': 8},
                        wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
                    )
                    
                    # Improve text visibility
                    for text in autotexts:
                        text.set_color('white')
                        text.set_fontweight('bold')
                    
                    # Set title with custom title and padding
                    ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                    plt.tight_layout()
                
                # --- AREA CHART ---
                elif chart_type == "Area":
                    fig, ax = plt.subplots(figsize=fig_size)
                    grouped = plot_df.groupby(x_col)[y_col].sum()
                    
                    # Limit to top values for better readability
                    if len(grouped) > 10:
                        grouped = grouped.nlargest(10)
                    
                    # Create abbreviated labels for x-axis - one word only
                    x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                    
                    # Create area chart
                    ax.fill_between(x_labels, grouped.values, alpha=0.4, color=colors[0])
                    ax.plot(x_labels, grouped.values, color=colors[0], linewidth=2)
                    
                    # Add data labels with formatted numbers
                    for i, v in enumerate(grouped.values):
                        ax.annotate(format_number(v), 
                                  xy=(i, v), xytext=(0, 5), 
                                  textcoords="offset points", 
                                  ha='center', fontsize=8)
                    
                    # Add trendline
                    if len(grouped) > 2:
                        z = np.polyfit(range(len(grouped)), grouped.values, 1)
                        p = np.poly1d(z)
                        ax.plot(range(len(grouped)), p(range(len(grouped))), 
                              "r--", alpha=0.7, linewidth=1.5, label='Trend')
                        ax.legend(fontsize=8, loc='upper left')
                    
                    # Format axes
                    ax.set_ylabel(y_label, fontsize=9)
                    ax.set_xlabel(x_label, fontsize=9)
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                    plt.yticks(fontsize=8)
                    
                    # Format y-axis to use K/M notation
                    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                        lambda x, p: format_number(x)))
                    
                    # Add title (bold) with more padding
                    ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                    
                    # Clean up the look
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.tight_layout()
                
                # --- HEATMAP ---
                elif chart_type == "Heatmap":
                    # For heatmap, we need at least one more categorical column
                    cat_cols = [c for c in df.columns if c != x_col and c != y_col 
                               and len(df[c].unique()) <= 20]
                    
                    if not cat_cols:
                        st.markdown("<span style='color:#d90429;font-size:14px;'>Heatmap requires at least one more categorical column.</span>", unsafe_allow_html=True)
                    else:
                        heatmap_col = st.selectbox("Heatmap category column", 
                                                 cat_cols, key=f"viz_heatmap_col_{key}")
                        
                        fig, ax = plt.subplots(figsize=fig_size)
                        
                        # Prepare heatmap data
                        heatmap_data = df.pivot_table(
                            index=heatmap_col, 
                            columns=x_col, 
                            values=y_col, 
                            aggfunc='mean'
                        )
                        
                        # Limit size for readability
                        if heatmap_data.shape[0] > 10 or heatmap_data.shape[1] > 10:
                            # Get top rows and columns
                            top_rows = heatmap_data.mean(axis=1).nlargest(10).index
                            top_cols = heatmap_data.mean(axis=0).nlargest(10).index
                            heatmap_data = heatmap_data.loc[
                                heatmap_data.index.isin(top_rows), 
                                heatmap_data.columns.isin(top_cols)
                            ]
                        
                        # Create abbreviated labels - one word only
                        row_labels = [truncate_text(r, 1) for r in heatmap_data.index]
                        col_labels = [truncate_text(c, 1) for c in heatmap_data.columns]
                        
                        # Create the heatmap
                        im = ax.imshow(heatmap_data, cmap='viridis')
                        
                        # Set labels
                        ax.set_xticks(np.arange(len(col_labels)))
                        ax.set_yticks(np.arange(len(row_labels)))
                        ax.set_xticklabels(col_labels, fontsize=8)
                        ax.set_yticklabels(row_labels, fontsize=8)
                        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                        
                        # Add colorbar
                        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
                        cbar.ax.tick_params(labelsize=8)
                        
                        # Add value annotations
                        for i in range(len(row_labels)):
                            for j in range(len(col_labels)):
                                value = heatmap_data.iloc[i, j]
                                if not pd.isna(value):
                                    ax.text(j, i, format_number(value),
                                          ha="center", va="center", 
                                          color="white" if value > heatmap_data.mean().mean() else "black",
                                          fontsize=7)
                        
                        # Use custom title (bold) with more padding
                        ax.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                        plt.tight_layout()
                
                # --- PARETO CHART ---
                elif chart_type == "Pareto":
                    fig, ax1 = plt.subplots(figsize=fig_size)
                    
                    # Prepare data
                    pareto_data = plot_df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
                    
                    # Limit to top categories for better readability
                    if len(pareto_data) > 10:
                        pareto_data = pareto_data.head(10)
                    
                    # Calculate cumulative percentage
                    cumpercentage = pareto_data.cumsum() / pareto_data.sum() * 100
                    
                    # Create abbreviated labels for x-axis - one word only
                    x_labels = [truncate_text(idx, 1) for idx in pareto_data.index]
                    
                    # Create Pareto chart
                    bars = ax1.bar(x_labels, pareto_data, color=colors[0])
                    
                    # Add percentage axis
                    ax2 = ax1.twinx()
                    ax2.plot(x_labels, cumpercentage, 'bo-', linewidth=2, markersize=4, color='red')
                    ax2.set_ylim([0, 105])
                    ax2.set_ylabel('Cumulative %', fontsize=9)
                    ax2.tick_params(axis='y', labelsize=8)
                    
                    # Add data labels with formatted numbers
                    for i, bar in enumerate(bars):
                        height = bar.get_height()
                        ax1.annotate(format_number(height), 
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3), textcoords="offset points", 
                                   ha='center', va='bottom', fontsize=7)
                        
                        # Add percentage on the line
                        ax2.annotate(f"{cumpercentage.iloc[i]:.1f}%", 
                                   xy=(i, cumpercentage.iloc[i]),
                                   xytext=(0, 5), textcoords="offset points", 
                                   ha='center', fontsize=7, color='red')
                    
                    # Format axes
                    ax1.set_ylabel(y_label, fontsize=9)
                    ax1.set_xlabel(x_label, fontsize=9)
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                    ax1.tick_params(axis='y', labelsize=8)
                    
                    # Format y-axis to use K/M notation
                    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
                        lambda x, p: format_number(x)))
                    
                    # Add title (bold) with more padding
                    ax1.set_title(chart_title, fontweight='bold', fontsize=10, pad=15)
                    
                    # Clean up the look
                    ax1.spines['top'].set_visible(False)
                    ax1.spines['right'].set_visible(False)
                    plt.tight_layout()
                
                # Display the chart
                if fig:
                    st.pyplot(fig)
                    
                # Generate more visualizations option
                if len(numeric_cols) > 1 and len(columns) > 2:
                    with st.expander("Generate Multiple Visualizations", expanded=False):
                        st.markdown("<span style='color:black;font-weight:bold;'>Automatically visualize all numeric columns against categorical columns</span>", unsafe_allow_html=True)
                        if st.button("Generate Multiple Charts", key=f"multi_charts_{key}"):
                            # Get categorical columns (non-numeric)
                            cat_cols = [c for c in columns if c not in numeric_cols]
                            if not cat_cols:
                                st.info("No categorical columns found for additional visualizations.")
                            else:
                                # Generate a reasonable number of visualizations
                                max_charts = min(5, len(numeric_cols) * len(cat_cols))
                                chart_pairs = []
                                
                                # Prioritize pairs
                                for num_col in numeric_cols[:3]:  # Limit to first 3 numeric cols
                                    for cat_col in cat_cols[:2]:  # Limit to first 2 categorical cols
                                        if num_col != cat_col:
                                            chart_pairs.append((cat_col, num_col))
                                
                                for i, (x, y) in enumerate(chart_pairs[:max_charts]):
                                    st.markdown(f"##### {y} by {x}")
                                    x_data = intelligent_group(df[x])
                                    y_data = df[y]
                                    
                                    try:
                                        plot_df = pd.DataFrame({x: x_data, y: y_data}).dropna()
                                        if not plot_df.empty:
                                            fig, ax = plt.subplots(figsize=sizes["Small"])
                                            grouped = plot_df.groupby(x)[y].sum()
                                            
                                            # Limit for readability
                                            if len(grouped) > 8:
                                                grouped = grouped.nlargest(8)
                                            
                                            # One-word labels
                                            x_labels = [truncate_text(idx, 1) for idx in grouped.index]
                                            
                                            # Choose chart type based on data
                                            if len(grouped) <= 5:
                                                # Pie for few categories
                                                wedges, texts, autotexts = ax.pie(
                                                    grouped.values,
                                                    labels=x_labels,
                                                    autopct='%1.1f%%',
                                                    colors=colors[:len(grouped)],
                                                    textprops={'fontsize': 8},
                                                    wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
                                                )
                                                
                                                # Improve text visibility for pie chart values
                                                for text in autotexts:
                                                    text.set_color('white')
                                                    text.set_fontweight('bold')
                                                
                                                # Add value labels in addition to percentages
                                                for i, p in enumerate(wedges):
                                                    ang = (p.theta2 - p.theta1)/2. + p.theta1
                                                    y = np.sin(np.deg2rad(ang))
                                                    x = np.cos(np.deg2rad(ang))
                                                    if y > 0:  # Only add for pieces big enough
                                                        ax.annotate(format_number(grouped.values[i]), 
                                                                  xy=(x*0.7, y*0.7),
                                                                  ha='center', va='center',
                                                                  fontsize=7, color='white',
                                                                  fontweight='bold')
                                                
                                                ax.set_title(f"{y} by {x}", fontweight='bold', fontsize=10, pad=15)
                                            else:
                                                # Bar for more categories
                                                bars = ax.bar(x_labels, grouped.values, color=colors[:len(grouped.index)])
                                                
                                                # Add data labels for bars
                                                for bar in bars:
                                                    height = bar.get_height()
                                                    ax.annotate(format_number(height), 
                                                              xy=(bar.get_x() + bar.get_width() / 2, height),
                                                              xytext=(0, 3), textcoords="offset points", 
                                                              ha='center', va='bottom', fontsize=7)
                                                
                                                ax.set_ylabel(truncate_text(y, 1), fontsize=9)
                                                ax.set_xlabel(truncate_text(x, 1), fontsize=9)
                                                plt.xticks(rotation=45, ha='right', fontsize=8)
                                                plt.yticks(fontsize=8)
                                                ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                                                    lambda x, p: format_number(x)))
                                                ax.set_title(f"{y} by {x}", fontweight='bold', fontsize=10, pad=15)
                                                ax.spines['top'].set_visible(False)
                                                ax.spines['right'].set_visible(False)
                                                plt.tight_layout()
                                            st.pyplot(fig)
                                    except Exception as e:
                                        st.markdown(f"<span style='color:#198754;font-size:12px;font-weight:bold;'>Could not generate chart for {y} by {x}: {str(e)}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<span style='color:#198754;font-size:14px;font-weight:bold;'>Cannot plot: {str(e)}</span>", unsafe_allow_html=True)

    # Show quick insights in a compact form
    insights_col1, insights_col2 = st.columns([1, 1])
    
    with insights_col1:
        st.markdown("**Quick Insights:**")
        if pd.api.types.is_numeric_dtype(y_data):
            metrics = {
                "Average": format_number(y_data.mean()),
                "Max": format_number(y_data.max()),
                "Min": format_number(y_data.min())
            }
            # Show metrics in a compact format
            metrics_cols = st.columns(3)
            for i, (label, value) in enumerate(metrics.items()):
                with metrics_cols[i]:
                    st.metric(f"{label}", value)
    
    with insights_col2:
        st.markdown(f"**Top {x_col} values:**")
        top_values = x_data.value_counts().head(3)
        for i, (val, count) in enumerate(top_values.items()):
            st.markdown(f"**{truncate_text(val)}:** {format_number(count)}")
    
    # Download option
    saved_path = None
    if fig and st.button("Download Visual"):
        visuals_dir = os.path.join("my_projects", "visuals")
        os.makedirs(visuals_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{chart_type.lower()}_{timestamp}.png"
        temp_path = os.path.join(os.getcwd(), fname)
        # Save with higher DPI for better quality
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
