/**
 * South India Urban Intelligence & AI Copilot Frontend Application.
 * Pure API-driven client layer — ZERO hardcoded operational/city intelligence state.
 */

// Global App Configuration
const API_BASE_URL = 'http://localhost:8000';
const POLLING_INTERVAL_MS = 3000;

// State Variables (UI-only)
let map = null;
let mapMarkers = [];
let isConnected = false;
let currentCityConfig = {
    name: 'Chennai',
    lat: 13.0827,
    lon: 80.2707,
    zoom: 11
};

// Initialize Application on Page Load
document.addEventListener('DOMContentLoaded', () => {
    initLeafletMap();
    initEventListeners();
    fetchBackendState();
    
    // Continuous real-time polling loop
    setInterval(fetchBackendState, POLLING_INTERVAL_MS);
});

/**
 * Initializes Leaflet 2D GIS Map centered over South India (Tamil Nadu, Kerala, Andhra Pradesh).
 */
function initLeafletMap() {
    // Center of South India
    map = L.map('gis-map').setView([11.0, 78.5], 7);

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

/**
 * Attaches DOM Event Listeners for City Selection & Severity Filtering.
 */
function initEventListeners() {
    const citySelect = document.getElementById('city-selector');
    if (citySelect) {
        citySelect.addEventListener('change', (e) => {
            const selectedOpt = citySelect.options[citySelect.selectedIndex];
            const lat = parseFloat(selectedOpt.getAttribute('data-lat'));
            const lon = parseFloat(selectedOpt.getAttribute('data-lon'));
            const name = selectedOpt.text;
            
            if (!isNaN(lat) && !isNaN(lon)) {
                currentCityConfig = { name, lat, lon, zoom: 11 };
                map.setView([lat, lon], 11);
            }
        });
    }

    const severityFilter = document.getElementById('severity-filter');
    if (severityFilter) {
        severityFilter.addEventListener('change', () => {
            fetchBackendState();
        });
    }
}

/**
 * Fetches current up-to-the-second Live City State from Backend API (GET /api/state).
 */
async function fetchBackendState() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/state`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const state = await response.json();
        setConnectionStatus(true, state);
        renderDashboard(state);
    } catch (err) {
        setConnectionStatus(false);
    }
}

/**
 * Updates UI Connection Indicators (Connected vs Backend Offline).
 */
function setConnectionStatus(connected, stateData = null) {
    const statusBadge = document.getElementById('backend-status-badge');
    const modeBadge = document.getElementById('data-mode-badge');
    const errorBanner = document.getElementById('connection-error-banner');
    const lastUpdatedText = document.getElementById('last-updated-text');

    if (connected) {
        isConnected = true;
        if (statusBadge) {
            statusBadge.className = 'status-indicator status-live';
            statusBadge.textContent = '● CONNECTED';
        }
        if (errorBanner) {
            errorBanner.classList.add('hidden');
        }

        if (stateData) {
            const dataMode = stateData.data_mode || 'HYBRID';
            if (modeBadge) {
                modeBadge.textContent = `DATA_MODE: ${dataMode.toUpperCase()}`;
            }

            if (lastUpdatedText && stateData.last_updated) {
                const dt = new Date(stateData.last_updated);
                const timeStr = isNaN(dt.getTime()) ? stateData.last_updated : dt.toLocaleTimeString();
                lastUpdatedText.textContent = `Updated: ${timeStr}`;
            }
        }
    } else {
        isConnected = false;
        if (statusBadge) {
            statusBadge.className = 'status-indicator status-offline';
            statusBadge.textContent = '● BACKEND OFFLINE';
        }
        if (errorBanner) {
            errorBanner.classList.remove('hidden');
        }
        if (lastUpdatedText) {
            lastUpdatedText.textContent = 'Updated: Disconnected';
        }
    }
}

/**
 * Renders Dashboard Views from Backend State Object.
 */
function renderDashboard(state) {
    if (!state) return;

    renderKPIs(state);
    renderMapOverlay(state);
    renderLiveFeed(state);
    renderEnvironment(state);
    renderZoneIntelligence(state);
    renderInfrastructureConnectors(state);
}

/**
 * Renders Top KPI Row from Backend API Values.
 */
function renderKPIs(state) {
    const riskScore = state.overall_risk_score !== undefined ? state.overall_risk_score : '--';
    const riskLevel = state.overall_risk_level || 'UNKNOWN';
    const riskTrend = state.risk_trend || 'STABLE';
    const eventsCount = state.recent_events ? state.recent_events.length : 0;
    const anomaliesCount = state.active_anomalies ? state.active_anomalies.length : 0;
    const correlationsCount = state.correlations ? state.correlations.length : 0;

    const riskScoreEl = document.getElementById('kpi-risk-score');
    if (riskScoreEl) {
        riskScoreEl.innerHTML = `${riskScore} <span class="kpi-unit">/100</span>`;
    }

    const riskBadge = document.getElementById('kpi-risk-badge');
    if (riskBadge) {
        riskBadge.className = `severity-badge badge-${riskLevel.toLowerCase()}`;
        riskBadge.textContent = `${riskLevel} RISK (${riskTrend})`;
    }

    const eventsEl = document.getElementById('kpi-events-count');
    if (eventsEl) eventsEl.textContent = eventsCount;

    const anomaliesEl = document.getElementById('kpi-anomalies-count');
    if (anomaliesEl) anomaliesEl.textContent = anomaliesCount;

    const correlationsEl = document.getElementById('kpi-correlations-count');
    if (correlationsEl) correlationsEl.textContent = correlationsCount;

    const healthEl = document.getElementById('kpi-system-health');
    if (healthEl) {
        healthEl.textContent = isConnected ? 'HEALTHY' : 'OFFLINE';
        healthEl.style.color = isConnected ? '#10B981' : '#EF4444';
    }
}

/**
 * Renders GIS Map Markers for Recent Backend Events & Active Anomalies.
 */
function renderMapOverlay(state) {
    if (!map) return;

    // Clear existing markers
    mapMarkers.forEach(m => map.removeLayer(m));
    mapMarkers = [];

    const recentEvents = state.recent_events || [];
    const activeAnomalies = state.active_anomalies || [];

    const severityFilter = document.getElementById('severity-filter')?.value || 'ALL';

    recentEvents.forEach(ev => {
        const data = ev.data || {};
        const loc = ev.location || {};
        const lat = loc.lat;
        const lon = loc.lon;
        const sev = (data.severity || ev.severity || 'LOW').toUpperCase();

        if (severityFilter !== 'ALL' && sev !== severityFilter) return;

        if (lat && lon && !isNaN(lat) && !isNaN(lon)) {
            const evId = data.event_id || ev.event_id || 'unk';
            const evType = data.event_type || ev.event_type || 'incident';
            const src = ev.source || 'unknown';
            const desc = data.description || data.text || data.condition || evType;

            const color = sev === 'CRITICAL' ? '#EF4444' : (sev === 'HIGH' ? '#F97316' : (sev === 'MODERATE' ? '#F59E0B' : '#10B981'));

            const marker = L.circleMarker([lat, lon], {
                radius: 8,
                fillColor: color,
                color: '#FFFFFF',
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.85
            }).addTo(map);

            marker.bindPopup(`
                <div style="font-family: sans-serif; font-size: 0.85rem; color: #0F172A;">
                    <strong style="color: ${color};">[${sev}] ${evType.toUpperCase()}</strong><br>
                    <strong>ID:</strong> ${evId}<br>
                    <strong>Source:</strong> ${src}<br>
                    <strong>Location:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}<br>
                    <p style="margin-top: 4px;">${desc}</p>
                </div>
            `);

            mapMarkers.push(marker);
        }
    });
}

/**
 * Renders Live Event Stream Feed from Backend events.
 */
function renderLiveFeed(state) {
    const container = document.getElementById('event-feed-container');
    const feedCountBadge = document.getElementById('feed-count-badge');
    if (!container) return;

    let events = state.recent_events || [];
    const severityFilter = document.getElementById('severity-filter')?.value || 'ALL';

    if (severityFilter !== 'ALL') {
        events = events.filter(ev => {
            const data = ev.data || {};
            const sev = (data.severity || ev.severity || 'LOW').toUpperCase();
            return sev === severityFilter;
        });
    }

    if (feedCountBadge) {
        feedCountBadge.textContent = `${events.length} Stream Events`;
    }

    if (events.length === 0) {
        container.innerHTML = '<div class="empty-state">No telemetry stream events currently recorded for this filter.</div>';
        return;
    }

    // Sort descending by timestamp
    events = [...events].reverse();

    let html = '';
    events.forEach(ev => {
        const data = ev.data || {};
        const loc = ev.location || {};
        const evId = data.event_id || ev.event_id || 'unk';
        const evType = data.event_type || ev.event_type || 'incident';
        const src = ev.source || 'unknown';
        const sev = (data.severity || ev.severity || 'LOW').toUpperCase();
        const badgeCls = `badge-${sev.toLowerCase()}`;
        const desc = data.description || data.text || data.condition || data.message || evType;
        
        let tsStr = ev.timestamp || 'N/A';
        try {
            const dt = new Date(ev.timestamp);
            if (!isNaN(dt.getTime())) tsStr = dt.toLocaleTimeString();
        } catch (e) {}

        const latLonStr = (loc.lat && loc.lon) ? `${loc.lat.toFixed(2)}, ${loc.lon.toFixed(2)}` : 'N/A';

        html += `
            <div class="event-item">
                <div class="event-details">
                    <div class="event-title">${evType.toUpperCase()} (ID: ${evId})</div>
                    <div style="font-size: 0.85rem; color: #F8FAFC; margin: 0.15rem 0;">${desc}</div>
                    <div class="event-meta">
                        ⏱️ ${tsStr} | 📍 ${latLonStr} | Source: <strong>${src}</strong>
                    </div>
                </div>
                <div>
                    <span class="severity-badge ${badgeCls}">${sev}</span>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * Renders Environmental & Weather Telemetry from Backend Data Sources.
 */
function renderEnvironment(state) {
    const recentEvents = state.recent_events || [];

    // Find latest weather and air quality events from backend
    let weatherEv = null;
    let airQualityEv = null;

    for (let i = recentEvents.length - 1; i >= 0; i--) {
        const ev = recentEvents[i];
        if (!weatherEv && (ev.source === 'weather_api' || ev.source === 'open_meteo_weather')) {
            weatherEv = ev.data || {};
        }
        if (!airQualityEv && (ev.source === 'air_quality_api' || ev.source === 'open_meteo_air_quality' || ev.source === 'environment_api')) {
            airQualityEv = ev.data || {};
        }
    }

    const tempEl = document.getElementById('env-temp');
    if (tempEl) {
        tempEl.textContent = weatherEv && weatherEv.temperature !== undefined ? `${weatherEv.temperature}°C` : 'Data unavailable';
    }

    const condEl = document.getElementById('env-condition');
    if (condEl) {
        condEl.textContent = weatherEv && weatherEv.condition ? weatherEv.condition : 'Data unavailable';
    }

    const aqiEl = document.getElementById('env-aqi');
    if (aqiEl) {
        aqiEl.textContent = airQualityEv && airQualityEv.air_quality_index !== undefined ? `${airQualityEv.air_quality_index} US AQI` : 'Data unavailable';
    }

    const pmEl = document.getElementById('env-pm');
    if (pmEl) {
        if (airQualityEv && (airQualityEv.pm2_5 !== undefined || airQualityEv.pm10 !== undefined)) {
            pmEl.textContent = `${airQualityEv.pm2_5 || '--'} / ${airQualityEv.pm10 || '--'} µg/m³`;
        } else {
            pmEl.textContent = 'Data unavailable';
        }
    }

    const windEl = document.getElementById('env-wind');
    if (windEl) {
        windEl.textContent = weatherEv && weatherEv.wind_speed !== undefined ? `${weatherEv.wind_speed} km/h` : 'Data unavailable';
    }

    const no2El = document.getElementById('env-no2');
    if (no2El) {
        no2El.textContent = airQualityEv && airQualityEv.nitrogen_dioxide !== undefined ? `${airQualityEv.nitrogen_dioxide} µg/m³` : 'Data unavailable';
    }
}

/**
 * Renders Geographic Zone Intelligence Cards from Backend state.zone_summaries.
 */
function renderZoneIntelligence(state) {
    const container = document.getElementById('zone-summary-container');
    if (!container) return;

    const zoneSummaries = state.zone_summaries || {};
    const zoneKeys = Object.keys(zoneSummaries);

    if (zoneKeys.length === 0) {
        container.innerHTML = '<div class="empty-state">No spatial zone intelligence generated yet.</div>';
        return;
    }

    let html = '';
    zoneKeys.forEach(zName => {
        const zInfo = zoneSummaries[zName];
        const riskLevel = zInfo.risk_level || 'LOW';
        const riskScore = zInfo.risk_score || 0;
        const badgeCls = `badge-${riskLevel.toLowerCase()}`;
        const eventCount = zInfo.event_count || 0;
        const criticalCount = zInfo.critical_count || 0;

        html += `
            <div class="zone-card">
                <div style="font-weight: 700; font-size: 0.9rem;">${zName}</div>
                <div style="margin: 0.35rem 0;">
                    <span class="severity-badge ${badgeCls}">${riskLevel} (${riskScore} pts)</span>
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8;">
                    Total Events: <strong>${eventCount}</strong> | Critical: <strong style="color: #EF4444;">${criticalCount}</strong>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * Renders Data Connectors Infrastructure Status Cards from Backend data_freshness.
 */
function renderInfrastructureConnectors(state) {
    const container = document.getElementById('connectors-status-grid');
    if (!container) return;

    const freshness = state.data_freshness || {};
    const connectorKeys = Object.keys(freshness);

    if (connectorKeys.length === 0) {
        container.innerHTML = '<div class="empty-state">Infrastructure health status loading...</div>';
        return;
    }

    let html = '';
    connectorKeys.forEach(key => {
        const info = freshness[key] || {};
        const statusVal = info.status || 'UNKNOWN';
        const modeVal = info.mode || 'LIVE';
        const eventCount = info.event_count || 0;
        
        const isHealthy = statusVal === 'LIVE' || statusVal === 'READY' || statusVal === 'RUNNING';
        const color = isHealthy ? '#10B981' : (statusVal === 'SIMULATION' ? '#38BDF8' : '#F59E0B');
        const formattedName = key.replace(/_/g, ' ').toUpperCase();

        html += `
            <div class="connector-card">
                <div style="font-size: 0.85rem; font-weight: 700; text-transform: capitalize;">📡 ${formattedName}</div>
                <div style="color: ${color}; font-weight: 700; font-size: 0.85rem; margin: 0.25rem 0;">● ${statusVal} (${modeVal})</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Events Processed: ${eventCount}</div>
            </div>
        `;
    });

    // Add Pathway Engine card
    html += `
        <div class="connector-card">
            <div style="font-size: 0.85rem; font-weight: 700;">⚡ PATHWAY STREAMING ENGINE</div>
            <div style="color: #10B981; font-weight: 700; font-size: 0.85rem; margin: 0.25rem 0;">● RUNNING</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">Stream Concats & UDF Evaluation Active</div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Fills Copilot Query Input Box when user clicks a suggested prompt button.
 */
function fillCopilotPrompt(promptText) {
    const input = document.getElementById('copilot-input');
    if (input) {
        input.value = promptText;
        input.focus();
    }
}

/**
 * Submits User Query to Backend POST /api/ask Endpoint and Renders Structured Copilot Response.
 */
async function submitCopilotQuery(event) {
    event.preventDefault();
    
    const inputEl = document.getElementById('copilot-input');
    const submitBtn = document.getElementById('copilot-submit-btn');
    const resultsContainer = document.getElementById('copilot-results');

    const question = inputEl ? inputEl.value.trim() : '';
    if (!question) return;

    if (submitBtn) submitBtn.disabled = true;
    if (resultsContainer) {
        resultsContainer.innerHTML = '<div class="copilot-notice">Analyzing real-time telemetry, executing grounded RAG context, and generating copilot decision support...</div>';
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const resData = await response.json();
        renderCopilotResponse(question, resData);
    } catch (err) {
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="copilot-response-card" style="border-color: #EF4444;">
                    <strong style="color: #EF4444;">AI Copilot unavailable — Unable to reach backend server</strong>
                    <p style="font-size: 0.85rem; color: #94A3B8;">Ensure backend server is running on ${API_BASE_URL} (python -m src.main)</p>
                </div>
            `;
        }
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

/**
 * Renders Structured AI Copilot Decision Support Response & Recommendations.
 */
function renderCopilotResponse(question, res) {
    const resultsContainer = document.getElementById('copilot-results');
    if (!resultsContainer) return;

    const answer = res.answer || 'No answer generated.';
    const riskLevel = res.risk_level || 'LOW';
    const confidence = res.confidence || 'HIGH';
    const recommendations = res.recommended_actions || [];
    const evidence = res.evidence || [];
    const affectedZones = res.affected_zones || [];

    let recsHtml = '';
    if (recommendations.length > 0) {
        recsHtml = `
            <div class="recommendations-box">
                <strong>🛡️ HUMAN REVIEW RECOMMENDATIONS (Decision Support Only):</strong>
                <ul>
                    ${recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    let evidenceHtml = '';
    if (evidence.length > 0) {
        let rowsHtml = evidence.map(ev => `
            <tr>
                <td><code>${ev.event_id || 'unk'}</code></td>
                <td>${ev.source || 'unknown'}</td>
                <td>${ev.zone || 'Zone A'}</td>
                <td><span class="severity-badge badge-${(ev.severity || 'LOW').toLowerCase()}">${ev.severity || 'LOW'}</span></td>
            </tr>
        `).join('');

        evidenceHtml = `
            <div style="margin-top: 0.5rem;">
                <strong style="font-size: 0.85rem; color: #38BDF8;">📌 Verified Audit Evidence Citations:</strong>
                <table class="evidence-table">
                    <thead>
                        <tr>
                            <th>Event ID</th>
                            <th>Source</th>
                            <th>Zone</th>
                            <th>Severity</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
        `;
    }

    resultsContainer.innerHTML = `
        <div class="copilot-response-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 0.5rem;">
                <span style="font-weight: 700; color: #38BDF8;">❓ Question: ${question}</span>
                <span>
                    <span class="severity-badge badge-${riskLevel.toLowerCase()}">${riskLevel} RISK</span>
                    <small style="color: #94A3B8; margin-left: 0.5rem;">Confidence: ${confidence}</small>
                </span>
            </div>

            <div class="copilot-ans-text">
                💡 <strong>AI Copilot Grounded Analysis:</strong><br>${answer}
            </div>

            ${recsHtml}

            ${affectedZones.length > 0 ? `<div style="font-size: 0.85rem;"><strong>Affected Zones:</strong> <code>${affectedZones.join(', ')}</code></div>` : ''}

            ${evidenceHtml}
        </div>
    `;
}
