import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_time_series_chart(data_df, metric_column, title):
    """Render a time series chart for a specific metric"""
    if data_df.empty or metric_column not in data_df.columns:
        st.info(f"No data available for {title}")
        return
    
    # Prepare data
    chart_df = data_df.copy()
    chart_df['timestamp'] = pd.to_datetime(chart_df['timestamp'])
    chart_df = chart_df.sort_values('timestamp')
    
    # Create chart
    fig = px.line(
        chart_df,
        x='timestamp',
        y=metric_column,
        color='source',
        title=title,
        labels={metric_column: title, 'timestamp': 'Time'},
        height=400
    )
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=title,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_pie_chart(data_df, column, title):
    """Render a pie chart for categorical data"""
    if data_df.empty or column not in data_df.columns:
        st.info(f"No data available for {title}")
        return
    
    # Prepare data
    pie_df = data_df[column].value_counts().reset_index()
    pie_df.columns = [column, 'count']
    
    # Create chart
    fig = px.pie(
        pie_df,
        values='count',
        names=column,
        title=title,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_bar_chart(data_df, x_column, y_column, title):
    """Render a bar chart"""
    if data_df.empty or x_column not in data_df.columns or y_column not in data_df.columns:
        st.info(f"No data available for {title}")
        return
    
    # Prepare data
    bar_df = data_df.groupby(x_column)[y_column].mean().reset_index()
    
    # Create chart
    fig = px.bar(
        bar_df,
        x=x_column,
        y=y_column,
        title=title,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
