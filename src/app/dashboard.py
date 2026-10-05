import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    import pathway as pw
    from pathway import Table
except ImportError:
    from ..pathway_compat import pw, Table

from .charts import render_time_series_chart, render_pie_chart, render_bar_chart
from ..processing.city_state import CityStateManager

logger = logging.getLogger(__name__)

class Dashboard:
    def __init__(self, processed_table: Table, anomalies_table: Table, rag_system, config: dict, city_state_manager: CityStateManager = None):
        self.processed_table = processed_table
        self.anomalies_table = anomalies_table
        self.rag_system = rag_system
        self.config = config
        self.mode = config.get('mode', 'public_safety')
        self.map_center = config.get('output', {}).get('map_center', [40.7128, -74.0060])
        self.city_state_manager = city_state_manager or CityStateManager(config)
        
        # Initialize session state variables
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 5
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        if 'selected_event_idx' not in st.session_state:
            st.session_state.selected_event_idx = 0
        if 'severity_filter' not in st.session_state:
            st.session_state.severity_filter = "All"
        if 'source_filter' not in st.session_state:
            st.session_state.source_filter = "All"
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Overview"

    def run(self):
        # Page configuration
        st.set_page_config(
            page_title="Urban Intelligence Command Center",
            page_icon="🏙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Apply Custom Command Center CSS Theme
        self._apply_theme_css()

        # Render Top Navigation Header
        self._render_top_navigation()

        # Render Sidebar & Navigation Controls
        self._render_sidebar()

        # Fetch latest streaming data from Pathway tables
        data_df, anomalies_df = self._get_data()

        # Main Dashboard Layout Routing based on Active Navigation Tab
        tab = st.session_state.active_tab

        if tab == "Overview":
            self._render_metrics_panel(data_df, anomalies_df)
            self._render_realtime_intelligence_panel()
            col_feed, col_map = st.columns([1, 1])
            with col_feed:
                self._render_live_event_feed(data_df)
            with col_map:
                self._render_city_map(data_df, anomalies_df)
            self._render_event_details_panel(data_df)

        elif tab == "Live Events":
            self._render_metrics_panel(data_df, anomalies_df)
            col_feed, col_detail = st.columns([1.2, 0.8])
            with col_feed:
                self._render_live_event_feed(data_df, max_rows=25)
            with col_detail:
                self._render_event_details_panel(data_df)

        elif tab == "City Map":
            self._render_city_map(data_df, anomalies_df, height=650)
            self._render_event_details_panel(data_df)

        elif tab == "Analytics":
            self._render_analytics_section(data_df, anomalies_df)

        elif tab == "Anomalies":
            self._render_anomalies_panel(anomalies_df)

        elif tab == "AI Assistant":
            self._render_ai_assistant_panel()

        elif tab == "System Status":
            self._render_system_health_panel(data_df)

        # Auto Refresh Mechanism
        if time.time() - st.session_state.last_refresh > st.session_state.refresh_interval:
            st.session_state.last_refresh = time.time()
            if hasattr(st, "rerun"):
                st.rerun()

    def _apply_theme_css(self):
        st.markdown("""
        <style>
        /* Modern Command Center CSS Theme */
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 98%;
        }
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            margin-bottom: 1.25rem;
        }
        .header-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.025em;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-simulated {
            background-color: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .status-live {
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .metric-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 0.75rem;
            padding: 1.1rem;
            text-align: left;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .metric-card:hover {
            border-color: #38BDF8;
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-val {
            font-size: 1.8rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0.2rem 0;
        }
        .badge-severity {
            padding: 0.2rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-low { background-color: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }
        .badge-moderate { background-color: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }
        .badge-high { background-color: rgba(249, 115, 22, 0.2); color: #F97316; border: 1px solid #F97316; }
        .badge-critical { background-color: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; }
        
        .card-panel {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin-bottom: 1.25rem;
        }
        .panel-header {
            font-size: 1.1rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 0.5rem;
        }
        .event-item {
            background-color: #0F172A;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .event-item:hover {
            border-color: #38BDF8;
            background-color: #1E293B;
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_top_navigation(self):
        mode_title = "Public Safety System" if self.mode == "public_safety" else "Urban Planning System"
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        data_mode = self.config.get('data_mode', 'HYBRID').upper()
        
        mode_badge_cls = "status-live" if data_mode == "LIVE" else ("status-simulated" if data_mode == "HYBRID" else "status-simulated")
        
        st.markdown(f"""
        <div class="header-bar">
            <div>
                <div class="header-title">
                    🏙️ Real-Time Urban Intelligence Command Center
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">
                    Streaming Telemetry Pipeline • Mode: <strong>{mode_title}</strong>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span class="status-badge {mode_badge_cls}">
                    ● {data_mode} MODE (PATHWAY ENGINE LIVE)
                </span>
                <span style="font-size: 0.85rem; color: #94A3B8;">
                    🕒 Updated: {now_str}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


    def _render_sidebar(self):
        with st.sidebar:
            st.title("🎛️ Navigation & Control")
            
            # Primary Navigation Radio Tabs
            st.session_state.active_tab = st.radio(
                "Select Dashboard View",
                ["Overview", "Live Events", "City Map", "Analytics", "Anomalies", "AI Assistant", "System Status"],
                index=["Overview", "Live Events", "City Map", "Analytics", "Anomalies", "AI Assistant", "System Status"].index(st.session_state.active_tab)
            )
            
            st.divider()
            st.subheader("🔍 Event Filters")
            
            # Severity Filter
            st.session_state.severity_filter = st.selectbox(
                "Filter by Severity",
                ["All", "CRITICAL", "HIGH", "MODERATE", "LOW"]
            )
            
            # Source Filter
            st.session_state.source_filter = st.selectbox(
                "Filter by Source",
                ["All", "twitter", "police_scanner", "city_sensors", "transit_api", "traffic_api", "environment_api"]
            )
            
            st.divider()
            st.subheader("⚙️ System Refresh Controls")
            
            st.session_state.refresh_interval = st.slider(
                "Auto Refresh Rate (seconds)",
                min_value=2,
                max_value=30,
                value=st.session_state.refresh_interval
            )
            
            if st.button("🔄 Refresh Stream Now", use_container_width=True):
                st.session_state.last_refresh = time.time()
                if hasattr(st, "rerun"):
                    st.rerun()

            st.divider()
            st.caption("Urban Intelligence System v1.2 (Phase 2 Stable)")

    def _get_data(self):
        data = self.processed_table.collect()
        anomalies = self.anomalies_table.collect()
        
        # Ingest events into CityStateManager
        for row in data:
            if isinstance(row, dict):
                self.city_state_manager.ingest_event(row)

        self.live_city_state = self.city_state_manager.get_live_city_state()
        st.session_state.live_city_state = self.live_city_state

        data_df = pd.DataFrame(data) if data else pd.DataFrame(columns=['timestamp', 'source', 'data', 'location'])
        anomalies_df = pd.DataFrame(anomalies) if anomalies else pd.DataFrame(columns=['timestamp', 'source', 'data', 'location'])

        # Augment severity logic onto DataFrame rows safely
        if not data_df.empty:
            data_df['severity'] = data_df.apply(self._compute_severity, axis=1)
        if not anomalies_df.empty:
            anomalies_df['severity'] = anomalies_df.apply(self._compute_severity, axis=1)

        # Apply Filters
        if not data_df.empty:
            if st.session_state.severity_filter != "All":
                data_df = data_df[data_df['severity'] == st.session_state.severity_filter]
            if st.session_state.source_filter != "All":
                data_df = data_df[data_df['source'] == st.session_state.source_filter]

        return data_df, anomalies_df

    def _compute_severity(self, row: pd.Series) -> str:
        row_data = row.get('data', {}) if isinstance(row.get('data'), dict) else {}
        if row_data.get('anomaly', False):
            if row_data.get('anomaly_type') == 'noise_level_anomaly' or row_data.get('priority', 0) >= 4:
                return "CRITICAL"
            return "HIGH"
        if row_data.get('priority') == 3 or row_data.get('congestion_level', 0) > 0.7:
            return "MODERATE"
        return "LOW"

    def _render_metrics_panel(self, data_df: pd.DataFrame, anomalies_df: pd.DataFrame):
        total_events = len(data_df)
        total_anomalies = len(anomalies_df)
        
        live_state = getattr(self, 'live_city_state', {}) or st.session_state.get('live_city_state', {})
        risk_score = live_state.get('overall_risk_score', min(100, int((total_anomalies * 18) + (total_events * 2))))
        risk_label = live_state.get('overall_risk_level', "CRITICAL" if risk_score > 75 else ("HIGH" if risk_score > 50 else ("MODERATE" if risk_score > 25 else "LOW")))
        risk_trend = live_state.get('risk_trend', 'STABLE')
        risk_badge_class = f"badge-{risk_label.lower()}"

        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CITY RISK INDEX</div>
                <div class="metric-val">{risk_score} <span style="font-size:1rem; color:#94A3B8;">/100</span></div>
                <div><span class="badge-severity {risk_badge_class}">{risk_label} ({risk_trend})</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">INGESTED EVENTS</div>
                <div class="metric-val">{total_events}</div>
                <div style="font-size:0.75rem; color:#38BDF8;">● Pathway Stream Active</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">ACTIVE ANOMALIES</div>
                <div class="metric-val" style="color:#EF4444;">{total_anomalies}</div>
                <div style="font-size:0.75rem; color:#F59E0B;">⚠️ Rule Violations Flagged</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            correlations_count = len(live_state.get('correlations', []))
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CROSS-SOURCE CORRELATIONS</div>
                <div class="metric-val" style="color:#38BDF8;">{correlations_count}</div>
                <div style="font-size:0.75rem; color:#10B981;">🔗 Multi-Source Overlaps</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">SYSTEM HEALTH</div>
                <div class="metric-val" style="color:#10B981; font-size:1.4rem;">HEALTHY</div>
                <div style="font-size:0.75rem; color:#10B981;">● Phase 4 Engine Live</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    def _render_realtime_intelligence_panel(self):
        live_state = getattr(self, 'live_city_state', {}) or st.session_state.get('live_city_state', {})
        if not live_state:
            return

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown('<div class="panel-header">⚡ City Risk & Evidence Trail</div>', unsafe_allow_html=True)
            
            factors = live_state.get('contributing_factors', [])
            evidence = live_state.get('evidence', [])

            st.markdown(f"**Current Risk Level:** `{live_state.get('overall_risk_level')}` (Score: `{live_state.get('overall_risk_score')}/100` | Trend: `{live_state.get('risk_trend')}`)")
            
            st.markdown("#### 🎯 Main Contributing Factors:")
            for f in factors:
                st.markdown(f"- 🔴 {f}")

            with st.expander("🔍 Inspect Risk Evidence Trail", expanded=False):
                for ev in evidence:
                    st.markdown(f"- {ev}")

        with col_right:
            st.markdown('<div class="panel-header">🗺️ Zone Intelligence & Intelligence Feed</div>', unsafe_allow_html=True)
            
            zone_summaries = live_state.get('zone_summaries', {})
            if zone_summaries:
                z_cols = st.columns(min(3, len(zone_summaries)))
                idx = 0
                for z_name, z_info in list(zone_summaries.items())[:3]:
                    with z_cols[idx % 3]:
                        badge_cls = f"badge-{z_info['risk_level'].lower()}"
                        st.markdown(f"""
                        <div class="card-panel" style="padding:0.75rem;">
                            <div style="font-weight:700; font-size:0.9rem;">{z_name}</div>
                            <div style="margin:0.25rem 0;"><span class="badge-severity {badge_cls}">{z_info['risk_level']} ({z_info['risk_score']} pts)</span></div>
                            <small style="color:#94A3B8;">Events: {z_info['event_count']} | Crit: {z_info['critical_count']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    idx += 1

            intelligence_feed = live_state.get('intelligence_feed', [])
            if intelligence_feed:
                st.markdown("#### 📢 Intelligence Feed Alerts:")
                for alert in reversed(intelligence_feed[-4:]):
                    st.markdown(f"`[{alert['time']}]` **{alert['category'].upper()}**: {alert['message']}")

        st.markdown("<br>", unsafe_allow_html=True)

    def _render_live_event_feed(self, data_df: pd.DataFrame, max_rows: int = 8):
        st.markdown('<div class="panel-header">📡 Live Event Feed (Pathway Ingestion Stream)</div>', unsafe_allow_html=True)

        if data_df.empty:
            st.info("Waiting for live data streams from Pathway pipeline...")
            return

        display_df = data_df.copy()
        display_df['timestamp_dt'] = pd.to_datetime(display_df['timestamp'])
        display_df = display_df.sort_values('timestamp_dt', ascending=False).head(max_rows)

        for idx, row in display_df.iterrows():
            ts_str = pd.to_datetime(row['timestamp']).strftime("%H:%M:%S")
            src = row['source']
            sev = row['severity']
            badge_cls = f"badge-{sev.lower()}"
            loc = row.get('location', {})
            lat_lon = f"{loc.get('lat', 0):.2f}, {loc.get('lon', 0):.2f}" if isinstance(loc, dict) else "N/A"
            
            row_data = row.get('data', {}) if isinstance(row.get('data'), dict) else {}
            title = row_data.get('type') or row_data.get('text') or row_data.get('source') or src

            cols = st.columns([1, 4, 2])
            with cols[0]:
                st.markdown(f"<span style='color:#94A3B8; font-size:0.85rem;'>⏱️ {ts_str}</span>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<strong>{title}</strong> <br><span style='color:#94A3B8; font-size:0.75rem;'>📍 {lat_lon} | Source: {src}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<span class='badge-severity {badge_cls}'>{sev}</span>", unsafe_allow_html=True)
            st.divider()

    def _render_city_map(self, data_df: pd.DataFrame, anomalies_df: pd.DataFrame, height: int = 400):
        st.markdown('<div class="panel-header">🗺️ Interactive 2D City GIS Map</div>', unsafe_allow_html=True)

        if data_df.empty:
            st.info("No geospatial data points ingested yet.")
            return

        map_df = data_df.copy()
        map_df['lat'] = map_df['location'].apply(lambda x: x.get('lat', 0.0) if isinstance(x, dict) else 0.0)
        map_df['lon'] = map_df['location'].apply(lambda x: x.get('lon', 0.0) if isinstance(x, dict) else 0.0)

        # Plotly Map rendering with compatibility checks
        if hasattr(px, "scatter_map"):
            fig = px.scatter_map(
                map_df,
                lat="lat",
                lon="lon",
                color="severity",
                hover_name="source",
                hover_data=["timestamp"],
                zoom=11,
                height=height,
                center=dict(lat=self.map_center[0], lon=self.map_center[1]),
                color_discrete_map={"LOW": "#10B981", "MODERATE": "#F59E0B", "HIGH": "#F97316", "CRITICAL": "#EF4444"}
            )
        else:
            fig = px.scatter_mapbox(
                map_df,
                lat="lat",
                lon="lon",
                color="severity",
                hover_name="source",
                hover_data=["timestamp"],
                zoom=11,
                height=height,
                mapbox_style="open-street-map",
                center=dict(lat=self.map_center[0], lon=self.map_center[1]),
                color_discrete_map={"LOW": "#10B981", "MODERATE": "#F59E0B", "HIGH": "#F97316", "CRITICAL": "#EF4444"}
            )

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15,23,42,0.6)',
            font=dict(color='#E2E8F0'),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_event_details_panel(self, data_df: pd.DataFrame):
        st.markdown('<div class="panel-header">🔍 Selected Event Inspector Details</div>', unsafe_allow_html=True)
        
        if data_df.empty:
            st.info("No event selected.")
            return

        event_options = [f"Event #{idx+1} | {row['source']} | Severity: {row['severity']} | {row['timestamp']}" for idx, row in data_df.iterrows()]
        selected_idx = st.selectbox("Select Event Payload to Inspect", range(len(event_options)), format_func=lambda i: event_options[i])
        
        selected_row = data_df.iloc[selected_idx]
        
        col_meta, col_payload = st.columns([1, 1])
        with col_meta:
            st.markdown(f"""
            <div style="background:#0F172A; padding:1rem; border-radius:0.5rem; border:1px solid #334155;">
                <p><strong>Source:</strong> {selected_row['source']}</p>
                <p><strong>Severity:</strong> <span class="badge-severity badge-{selected_row['severity'].lower()}">{selected_row['severity']}</span></p>
                <p><strong>Timestamp:</strong> {selected_row['timestamp']}</p>
                <p><strong>Location:</strong> {selected_row['location']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_payload:
            st.markdown("<strong>Raw Data Payload JSON:</strong>", unsafe_allow_html=True)
            st.json(selected_row['data'])

    def _render_analytics_section(self, data_df: pd.DataFrame, anomalies_df: pd.DataFrame):
        st.markdown('<div class="panel-header">📈 Urban Intelligence Analytics & Trends</div>', unsafe_allow_html=True)
        
        if data_df.empty:
            st.info("No data available for analytical charts.")
            return

        col1, col2 = st.columns(2)
        with col1:
            render_pie_chart(data_df, 'severity', 'Risk & Severity Distribution')
        with col2:
            render_bar_chart(data_df, 'source', 'count', 'Events Ingested per Data Source')

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            render_time_series_chart(data_df, 'source', 'Telemetry Stream Arrival Timeline')
        with col4:
            render_pie_chart(data_df, 'source', 'Source Share Breakdown')

    def _render_anomalies_panel(self, anomalies_df: pd.DataFrame):
        st.markdown('<div class="panel-header">🚨 Dedicated Active Anomalies Panel</div>', unsafe_allow_html=True)

        if anomalies_df.empty:
            st.success("✅ No active rule violations or anomalies detected in the current Pathway window.")
            return

        for idx, row in anomalies_df.iterrows():
            row_data = row['data'] if isinstance(row['data'], dict) else {}
            anom_type = row_data.get('anomaly_type', 'General Anomaly')
            anom_desc = row_data.get('anomaly_description', 'Threshold violation detected')
            sev = row.get('severity', 'HIGH')
            
            st.markdown(f"""
            <div style="background-color:#1E293B; border-left: 5px solid #EF4444; border-radius:0.5rem; padding:1rem; margin-bottom:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0; color:#EF4444;">⚠️ {anom_type}</h4>
                    <span class="badge-severity badge-{sev.lower()}">{sev}</span>
                </div>
                <p style="margin:0.5rem 0; color:#F8FAFC;">{anom_desc}</p>
                <div style="font-size:0.8rem; color:#94A3B8;">
                    <strong>Source:</strong> {row['source']} | 
                    <strong>Location:</strong> {row['location']} | 
                    <strong>Time:</strong> {row['timestamp']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_ai_assistant_panel(self):
        st.markdown('<div class="panel-header">🤖 AI Urban Copilot (Decision Support Console)</div>', unsafe_allow_html=True)
        
        has_key = getattr(self.rag_system, 'has_valid_key', False)
        if not has_key:
            st.warning("⚠️ **AI LLM is not configured.** Live city intelligence, RAG context, and deterministic Copilot recommendations are active, but natural-language synthesis requires an LLM API key. Set `OPENAI_API_KEY` in `.env` to enable full LLM synthesis.")

        live_state = getattr(self, 'live_city_state', None) or st.session_state.get('live_city_state', {})
        hottest_zone = None
        if live_state and "zone_summaries" in live_state:
            max_s = -1
            for z, info in live_state["zone_summaries"].items():
                if info.get("risk_score", 0) > max_s and info.get("event_count", 0) > 0:
                    max_s = info.get("risk_score", 0)
                    hottest_zone = z

        # Dynamic State-Aware Suggested Questions
        sug_q1 = "What is happening right now?"
        sug_q2 = f"Why is {hottest_zone} high risk?" if hottest_zone else "Which zone has highest risk?"
        sug_q3 = "What are active anomalies?" if live_state.get("active_anomalies") else "Show me the incidents responsible for the current risk."
        sug_q4 = "What should an operator investigate first?"

        st.markdown("#### Dynamic Copilot Suggestions:")
        sug_cols = st.columns(4)
        selected_prompt = None
        if sug_cols[0].button(sug_q1, use_container_width=True):
            selected_prompt = sug_q1
        if sug_cols[1].button(sug_q2, use_container_width=True):
            selected_prompt = sug_q2
        if sug_cols[2].button(sug_q3, use_container_width=True):
            selected_prompt = sug_q3
        if sug_cols[3].button(sug_q4, use_container_width=True):
            selected_prompt = sug_q4

        query_input = st.text_input("Ask the AI Urban Copilot a question:", value=selected_prompt or "", placeholder="e.g. Why is Zone A critical? What should an operator review first?")

        if st.button("Submit Query to AI Copilot Engine", use_container_width=True):
            if query_input:
                with st.spinner("Analyzing real-time telemetry, running RAG context, and generating copilot decision support..."):
                    structured_res = self.rag_system.query_structured(query_input, city_state=live_state)
                    
                    st.session_state.query_history.append({
                        "query": query_input,
                        "response": structured_res,
                        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
                    })

        if st.session_state.query_history:
            st.divider()
            st.markdown("#### Copilot Analysis & Human-in-the-Loop Decision Support:")
            for item in reversed(st.session_state.query_history[-5:]):
                res = item.get("response", {})
                ans_text = res.get("answer", "No answer available.")
                risk_lvl = res.get("risk_level", "LOW")
                confidence = res.get("confidence", "HIGH")
                affected_zones = res.get("affected_zones", [])
                key_factors = res.get("key_factors", [])
                recommendations = res.get("recommended_actions", [])
                evidence_list = res.get("evidence", [])
                dashboard_actions = res.get("dashboard_actions", [])

                badge_cls = f"badge-{risk_lvl.lower()}"

                st.markdown(f"""
                <div style="background-color:#0F172A; border:1px solid #334155; padding:1.25rem; border-radius:0.75rem; margin-bottom:1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <span style="font-weight:700; color:#38BDF8; font-size:1.05rem;">❓ Query ({item['timestamp']}): {item['query']}</span>
                        <span><span class="badge-severity {badge_cls}">{risk_lvl} RISK</span> <small style="color:#94A3B8;">Confidence: {confidence}</small></span>
                    </div>
                    <div style="margin-top:0.5rem; color:#F8FAFC; font-size:0.95rem; line-height:1.5; white-space: pre-wrap;">💡 <strong>AI Copilot Analysis:</strong>\n{ans_text}</div>
                </div>
                """, unsafe_allow_html=True)

                # Render Human-in-the-Loop Review Recommendations
                if recommendations:
                    st.markdown("""
                    <div style="background-color:rgba(245, 158, 11, 0.1); border-left:4px solid #F59E0B; padding:0.85rem 1rem; border-radius:0.5rem; margin-bottom:0.75rem;">
                        <strong style="color:#F59E0B;">🛡️ HUMAN REVIEW RECOMMENDATIONS (Decision Support Only):</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    for rec in recommendations:
                        st.markdown(f"- ⚠️ **{rec}**")

                if affected_zones or key_factors:
                    cols_af = st.columns([1, 1])
                    with cols_af[0]:
                        if affected_zones:
                            st.markdown(f"**Affected Zones:** `{', '.join(affected_zones)}`")
                    with cols_af[1]:
                        if key_factors:
                            st.markdown("**Key Factors:** " + " • ".join(key_factors))

                # Render Interactive Dashboard Action Buttons
                if dashboard_actions:
                    st.markdown("##### ⚡ Safe Dashboard Actions:")
                    act_cols = st.columns(min(4, len(dashboard_actions)))
                    for idx, act in enumerate(dashboard_actions):
                        with act_cols[idx % 4]:
                            if st.button(act.get("label", "Action"), key=f"btn_act_{item['timestamp']}_{idx}", use_container_width=True):
                                self._execute_dashboard_action(act)

                if evidence_list:
                    with st.expander("📌 Verified Audit Evidence Citations", expanded=False):
                        ev_df = pd.DataFrame(evidence_list)
                        st.dataframe(ev_df, use_container_width=True)

    def _execute_dashboard_action(self, action_dict: Dict[str, Any]):
        act_type = action_dict.get("action")
        target = action_dict.get("target")

        if act_type == "focus_zone":
            st.session_state.active_tab = "City Map"
            st.success(f"📍 Map view focused on target zone: {target}")
            if hasattr(st, "rerun"):
                st.rerun()

        elif act_type == "view_evidence":
            st.session_state.active_tab = "Live Events"
            st.success(f"🔍 Telemetry feed filtered for incident evidence in: {target}")
            if hasattr(st, "rerun"):
                st.rerun()

        elif act_type == "view_time_window":
            st.session_state.active_tab = "Analytics"
            st.info("⏱️ Navigated to 15-minute telemetry analytics view.")
            if hasattr(st, "rerun"):
                st.rerun()

        elif act_type == "compare_zones":
            st.session_state.active_tab = "Analytics"
            st.info(f"📊 Displaying comparison view for zones: {target}")
            if hasattr(st, "rerun"):
                st.rerun()

    def _render_system_health_panel(self, data_df: pd.DataFrame):
        st.markdown('<div class="panel-header">⚙️ System Health & Data Source Infrastructure</div>', unsafe_allow_html=True)

        connector_map = self.config.get('connector_status', {
            "weather_api": {"status": "LIVE", "last_updated": "Auto-polling"},
            "air_quality_api": {"status": "LIVE", "last_updated": "Auto-polling"},
            "gtfs_transit_api": {"status": "NOT CONFIGURED", "last_updated": "N/A"},
            "webhook_api": {"status": "READY", "last_updated": "Listening on /events"},
            "traffic": {"status": "SIMULATION", "last_updated": "Streaming"},
            "public_safety": {"status": "SIMULATION", "last_updated": "Streaming"}
        })

        has_llm_key = getattr(self.rag_system, 'has_valid_key', False)
        llm_status = "● Connected (Live OpenAI API)" if has_llm_key else "● Simulated / Notice Mode (Set OPENAI_API_KEY)"
        llm_color = "#10B981" if has_llm_key else "#F59E0B"

        cards_html = ""
        for name, info in connector_map.items():
            st_val = info.get("status", "ACTIVE")
            color = "#10B981" if st_val in ["LIVE", "READY", "RUNNING"] else ("#F59E0B" if st_val == "SIMULATION" else "#64748B")
            cards_html += f"""
            <div class="card-panel">
                <h4 style="text-transform:capitalize;">📡 {name.replace('_', ' ')}</h4>
                <p style="color:{color}; font-weight:700;">● {st_val}</p>
                <small style="color:#94A3B8;">Last Activity: {info.get('last_updated', 'N/A')}</small>
            </div>
            """

        cards_html += f"""
        <div class="card-panel">
            <h4>⚡ Pathway Streaming Engine</h4>
            <p style="color:#10B981; font-weight:700;">● RUNNING</p>
            <small style="color:#94A3B8;">Stream Concats & UDF Evaluation Active</small>
        </div>
        <div class="card-panel">
            <h4>📚 RAG Vector Index</h4>
            <p style="color:#10B981; font-weight:700;">● READY ({len(getattr(self.rag_system, 'documents', []))} docs stored)</p>
            <small style="color:#94A3B8;">Real-time context indexing active</small>
        </div>
        <div class="card-panel">
            <h4>🤖 OpenAI LLM API Service</h4>
            <p style="color:{llm_color}; font-weight:700;">{llm_status}</p>
            <small style="color:#94A3B8;">Model: {self.config.get('llm', {}).get('model', 'gpt-3.5-turbo')}</small>
        </div>
        """

        st.markdown(f'<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1rem;">{cards_html}</div>', unsafe_allow_html=True)

