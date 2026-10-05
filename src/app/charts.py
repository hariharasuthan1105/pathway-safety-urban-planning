import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Dark / Command-Center Plotly Template Layout
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(15,23,42,0.6)',
    font=dict(color='#E2E8F0', family='Inter, sans-serif'),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor='#334155', showgrid=True),
    yaxis=dict(gridcolor='#334155', showgrid=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

def render_time_series_chart(data_df: pd.DataFrame, metric_column: str, title: str):
    """Render a modern time series chart for a specific metric"""
    if data_df.empty or metric_column not in data_df.columns:
        st.info(f"No active stream data available for {title}")
        return
    
    chart_df = data_df.copy()
    chart_df['timestamp'] = pd.to_datetime(chart_df['timestamp'])
    chart_df = chart_df.sort_values('timestamp')
    
    fig = px.line(
        chart_df,
        x='timestamp',
        y=metric_column,
        color='source',
        title=title,
        labels={metric_column: title, 'timestamp': 'Time'},
        height=350,
        color_discrete_sequence=['#38BDF8', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']
    )
    
    fig.update_layout(**CHART_LAYOUT)
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, use_container_width=True)

def render_pie_chart(data_df: pd.DataFrame, column: str, title: str):
    """Render a donut pie chart for categorical data"""
    if data_df.empty or column not in data_df.columns:
        st.info(f"No data available for {title}")
        return
    
    pie_df = data_df[column].value_counts().reset_index()
    pie_df.columns = [column, 'count']
    
    fig = px.pie(
        pie_df,
        values='count',
        names=column,
        title=title,
        hole=0.45,
        height=350,
        color_discrete_sequence=['#10B981', '#F59E0B', '#F97316', '#EF4444', '#64748B']
    )
    
    fig.update_layout(**CHART_LAYOUT)
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#0F172A', width=2)))
    st.plotly_chart(fig, use_container_width=True)

def render_bar_chart(data_df: pd.DataFrame, x_column: str, y_column: str, title: str):
    """Render a bar chart"""
    if data_df.empty or x_column not in data_df.columns or y_column not in data_df.columns:
        st.info(f"No data available for {title}")
        return
    
    bar_df = data_df.groupby(x_column)[y_column].count().reset_index() if y_column == 'count' else data_df.groupby(x_column)[y_column].mean().reset_index()
    
    fig = px.bar(
        bar_df,
        x=x_column,
        y=y_column,
        title=title,
        height=350,
        color=x_column,
        color_discrete_sequence=['#38BDF8', '#8B5CF6', '#10B981', '#F59E0B']
    )
    
    fig.update_layout(**CHART_LAYOUT)
    fig.update_traces(marker=dict(line=dict(color='#0F172A', width=1)))
    st.plotly_chart(fig, use_container_width=True)
