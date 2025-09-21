import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathway import Table
import time
import json
from datetime import datetime
import pytz

class Dashboard:
    def __init__(self, processed_table: Table, anomalies_table: Table, rag_system, config):
        self.processed_table = processed_table
        self.anomalies_table = anomalies_table
        self.rag_system = rag_system
        self.config = config
        self.mode = config['mode']
        self.map_center = config.get('output', {}).get('map_center', [40.7128, -74.0060])
        
        # Initialize session state
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 5
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
    
    def run(self):
        # Page configuration
        st.set_page_config(
            page_title="Public Safety & Urban Planning Dashboard",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/pathwaycom/pathway',
                'Report a bug': "https://github.com/pathwaycom/pathway/issues",
                'About': "Real-time monitoring system using Pathway"
            }
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            padding: 1rem 0;
        }
        .section-header {
            font-size: 1.8rem;
            color: #0D47A1;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .anomaly-alert {
            background-color: #FFEBEE;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #F44336;
            margin-bottom: 1rem;
        }
        .query-response {
            background-color: #E3F2FD;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #F5F5F5;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #757575;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown('<div class="main-header">Public Safety & Urban Planning Dashboard</div>', unsafe_allow_html=True)
        
        # Sidebar
        self._render_sidebar()
        
        # Main content
        self._render_main_content()
        
        # Auto-refresh
        if time.time() - st.session_state.last_refresh > st.session_state.refresh_interval:
            st.experimental_rerun()
    
    def _render_sidebar(self):
        with st.sidebar:
            st.header("System Controls")
            
            # Mode selection
            mode = st.selectbox(
                "Select Mode",
                ["Public Safety", "Urban Planning"],
                index=0 if self.mode == "public_safety" else 1
            )
            
            # Refresh controls
            st.subheader("Refresh Settings")
            auto_refresh = st.checkbox("Auto Refresh", value=True)
            if auto_refresh:
                st.session_state.refresh_interval = st.slider(
                    "Refresh Interval (seconds)", 
                    min_value=1, 
                    max_value=30, 
                    value=st.session_state.refresh_interval
                )
            
            # Manual refresh
            if st.button("Refresh Now"):
                st.experimental_rerun()
            
            # System info
            st.subheader("System Information")
            st.write(f"Mode: {self.mode}")
            st.write(f"LLM: {self.config['llm']['model']}")
            st.write(f"Data Sources: {len(self.config['data_sources'])}")
            
            # Last update time
            if hasattr(self, 'last_update_time'):
                st.write(f"Last Update: {self.last_update_time}")
    
    def _render_main_content(self):
        # Get data
        data, anomalies = self._get_data()
        self.last_update_time = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Key metrics
        self._render_metrics(data, anomalies)
        
        # Two-column layout for data feed and anomalies
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_data_feed(data)
        
        with col2:
            self._render_anomalies(anomalies)
        
        # Map visualization
        self._render_map(data, anomalies)
        
        # Query assistant
        self._render_query_interface()
    
    def _get_data(self):
        # Get latest data from Pathway tables
        data = self.processed_table.collect()
        anomalies = self.anomalies_table.collect()
        
        # Convert to DataFrames
        data_df = pd.DataFrame(data)
        anomalies_df = pd.DataFrame(anomalies)
        
        return data_df, anomalies_df
    
    def _render_metrics(self, data_df, anomalies_df):
        st.subheader("System Metrics")
        
        # Calculate metrics
        total_data_points = len(data_df)
        total_anomalies = len(anomalies_df)
        anomaly_rate = (total_anomalies / total_data_points * 100) if total_data_points > 0 else 0
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Total Data Points</div>
            </div>
            """.format(total_data_points), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Active Anomalies</div>
            </div>
            """.format(total_anomalies), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}%</div>
                <div class="metric-label">Anomaly Rate</div>
            </div>
            """.format(anomaly_rate), unsafe_allow_html=True)
        
        with col4:
            # Get unique sources
            unique_sources = data_df['source'].nunique() if not data_df.empty else 0
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Data Sources</div>
            </div>
            """.format(unique_sources), unsafe_allow_html=True)
    
    def _render_data_feed(self, data_df):
        st.markdown('<div class="section-header">Live Data Feed</div>', unsafe_allow_html=True)
        
        if not data_df.empty:
            # Format data for display
            display_df = data_df.copy()
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
            display_df = display_df.sort_values('timestamp', ascending=False).head(10)
            
            # Format data column for better readability
            display_df['data'] = display_df['data'].apply(lambda x: json.dumps(x, indent=2))
            
            # Display data
            st.dataframe(
                display_df[['timestamp', 'source', 'data']],
                use_container_width=True,
                height=400
            )
        else:
            st.info("No data available yet")
    
    def _render_anomalies(self, anomalies_df):
        st.markdown('<div class="section-header">Anomaly Alerts</div>', unsafe_allow_html=True)
        
        if not anomalies_df.empty:
            # Format anomalies for display
            display_df = anomalies_df.copy()
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
            display_df = display_df.sort_values('timestamp', ascending=False)
            
            # Create expandable cards for each anomaly
            for _, row in display_df.iterrows():
                with st.expander(f"{row['data']['anomaly_type']} - {row['timestamp']}"):
                    st.markdown(f"""
                    <div class="anomaly-alert">
                        <strong>Anomaly Type:</strong> {row['data']['anomaly_type']}<br>
                        <strong>Description:</strong> {row['data']['anomaly_description']}<br>
                        <strong>Source:</strong> {row['source']}<br>
                        <strong>Location:</strong> {row['location']['lat']:.4f}, {row['location']['lon']:.4f}<br>
                        <strong>Time:</strong> {row['timestamp']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ No anomalies detected")
    
    def _render_map(self, data_df, anomalies_df):
        st.markdown('<div class="section-header">Geospatial Visualization</div>', unsafe_allow_html=True)
        
        if not data_df.empty:
            # Prepare data for mapping
            map_df = data_df.copy()
            map_df['lat'] = map_df['location'].apply(lambda x: x['lat'])
            map_df['lon'] = map_df['location'].apply(lambda x: x['lon'])
            
            # Create map
            fig = px.scatter_mapbox(
                map_df,
                lat="lat",
                lon="lon",
                color="source",
                hover_name="source",
                hover_data=["timestamp"],
                zoom=12,
                height=500,
                mapbox_style="open-street-map",
                center=dict(lat=self.map_center[0], lon=self.map_center[1])
            )
            
            # Add anomaly markers
            if not anomalies_df.empty:
                anomaly_df = anomalies_df.copy()
                anomaly_df['lat'] = anomaly_df['location'].apply(lambda x: x['lat'])
                anomaly_df['lon'] = anomaly_df['location'].apply(lambda x: x['lon'])
                
                fig.add_trace(go.Scattermapbox(
                    lat=anomaly_df['lat'],
                    lon=anomaly_df['lon'],
                    mode='markers',
                    marker=dict(
                        size=15,
                        color='red',
                        opacity=0.8
                    ),
                    text=anomaly_df['data'].apply(lambda x: f"Anomaly: {x['anomaly_type']}"),
                    hoverinfo='text',
                    name='Anomalies'
                ))
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data available")
    
    def _render_query_interface(self):
        st.markdown('<div class="section-header">Query Assistant</div>', unsafe_allow_html=True)
        
        # Query input
        query = st.text_input("Ask a question about the current situation:", 
                             placeholder="e.g., What is the situation at Central Park?")
        
        # Submit button
        if st.button("Submit Query"):
            if query:
                with st.spinner("Processing your query..."):
                    response = self.rag_system.query(query)
                    
                    # Add to query history
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": query,
                        "response": response
                    })
                    
                    # Display response
                    st.markdown(f"""
                    <div class="query-response">
                        <strong>Query:</strong> {query}<br><br>
                        <strong>Response:</strong><br>
                        {response}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Query history
        if st.session_state.query_history:
            st.subheader("Query History")
            for i, item in enumerate(reversed(st.session_state.query_history[-5:])):  # Show last 5 queries
                with st.expander(f"{item['timestamp']} - {item['query'][:50]}..."):
                    st.markdown(f"""
                    <div class="query-response">
                        <strong>Query:</strong> {item['query']}<br><br>
                        <strong>Response:</strong><br>
                        {item['response']}
                    </div>
                    """, unsafe_allow_html=True)
