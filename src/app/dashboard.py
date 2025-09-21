import streamlit as st
import pandas as pd
import plotly.express as px
from pathway import Table
import time

class Dashboard:
    def __init__(self, processed_table: Table, anomalies_table: Table, rag_system, config):
        self.processed_table = processed_table
        self.anomalies_table = anomalies_table
        self.rag_system = rag_system
        self.config = config
        self.mode = config['mode']
    
    def run(self):
        st.set_page_config(
            page_title="Public Safety & Urban Planning",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("Real-time Monitoring Dashboard")
        
        # Sidebar
        with st.sidebar:
            st.header("Configuration")
            st.write(f"Mode: {self.mode}")
            st.write(f"LLM: {self.config['llm']['model']}")
            
            refresh_rate = st.slider("Refresh Rate (sec)", 1, 10, 2)
            
            if st.button("Refresh Data"):
                st.experimental_rerun()
        
        # Main content
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Live Data Feed")
            self._show_data_feed()
        
        with col2:
            st.header("Anomaly Alerts")
            self._show_anomalies()
        
        st.header("Map Visualization")
        self._show_map()
        
        st.header("Query Assistant")
        self._show_query_interface()
        
        # Auto refresh
        time.sleep(refresh_rate)
        st.experimental_rerun()
    
    def _show_data_feed(self):
        # Get latest data
        data = self.processed_table.collect()
        df = pd.DataFrame(data)
        
        if not df.empty:
            st.dataframe(df.tail(10), use_container_width=True)
        else:
            st.info("No data available yet")
    
    def _show_anomalies(self):
        # Get anomalies
        anomalies = self.anomalies_table.collect()
        df = pd.DataFrame(anomalies)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.success("No anomalies detected")
    
    def _show_map(self):
        # Get location data
        data = self.processed_table.collect()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Create map
            fig = px.scatter_mapbox(
                df,
                lat="location__lat",
                lon="location__lon",
                color="source",
                hover_name="source",
                hover_data=["data"],
                zoom=12,
                height=500
            )
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data available")
    
    def _show_query_interface(self):
        query = st.text_input("Ask a question about the current situation:")
        
        if query:
            with st.spinner("Processing your query..."):
                response = self.rag_system.query(query)
                st.success(response)
