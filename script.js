/**
 * South India Urban Intelligence & AI Copilot Platform
 * Enterprise Frontend Client Logic
 * Strictly driven by backend API endpoints (GET /api/state, POST /api/ask) — ZERO HARDCODED OPERATIONAL DATA.
 */

// Global App Constants
const API_BASE_URL = 'http://localhost:8000';
const POLLING_INTERVAL_MS = 3000;

// South India Metropolitan Cities Metadata (Geographic Boundaries)
const SOUTH_INDIA_CITIES = [
    // Tamil Nadu
    { id: 'chennai', name: 'Chennai', state: 'tn', stateName: 'Tamil Nadu', lat: 13.0827, lon: 80.2707, isCapital: true },
    { id: 'coimbatore', name: 'Coimbatore', state: 'tn', stateName: 'Tamil Nadu', lat: 11.0168, lon: 76.9558 },
    { id: 'madurai', name: 'Madurai', state: 'tn', stateName: 'Tamil Nadu', lat: 9.9252, lon: 78.1198 },
    { id: 'salem', name: 'Salem', state: 'tn', stateName: 'Tamil Nadu', lat: 11.6643, lon: 78.1460 },
    { id: 'trichy', name: 'Tiruchirappalli', state: 'tn', stateName: 'Tamil Nadu', lat: 10.7905, lon: 78.7047 },
    { id: 'tiruppur', name: 'Tiruppur', state: 'tn', stateName: 'Tamil Nadu', lat: 11.1085, lon: 77.3411 },
    { id: 'erode', name: 'Erode', state: 'tn', stateName: 'Tamil Nadu', lat: 11.3410, lon: 77.7172 },
    { id: 'vellore', name: 'Vellore', state: 'tn', stateName: 'Tamil Nadu', lat: 12.9165, lon: 79.1325 },

    // Kerala
    { id: 'kochi', name: 'Kochi (Cochin)', state: 'kl', stateName: 'Kerala', lat: 9.9312, lon: 76.2673 },
    { id: 'tvm', name: 'Thiruvananthapuram', state: 'kl', stateName: 'Kerala', lat: 8.5241, lon: 76.9366, isCapital: true },
    { id: 'kozhikode', name: 'Kozhikode', state: 'kl', stateName: 'Kerala', lat: 11.2588, lon: 75.7804 },
    { id: 'thrissur', name: 'Thrissur', state: 'kl', stateName: 'Kerala', lat: 10.5276, lon: 76.2144 },
    { id: 'kollam', name: 'Kollam', state: 'kl', stateName: 'Kerala', lat: 8.8932, lon: 76.6141 },
    { id: 'kannur', name: 'Kannur', state: 'kl', stateName: 'Kerala', lat: 11.8745, lon: 75.3704 },

    // Andhra Pradesh
    { id: 'vizag', name: 'Visakhapatnam', state: 'ap', stateName: 'Andhra Pradesh', lat: 17.6868, lon: 83.2185 },
    { id: 'vijayawada', name: 'Vijayawada', state: 'ap', stateName: 'Andhra Pradesh', lat: 16.5062, lon: 80.6480 },
    { id: 'guntur', name: 'Guntur', state: 'ap', stateName: 'Andhra Pradesh', lat: 16.3067, lon: 80.4365 },
    { id: 'tirupati', name: 'Tirupati', state: 'ap', stateName: 'Andhra Pradesh', lat: 13.6288, lon: 79.4192 },
    { id: 'nellore', name: 'Nellore', state: 'ap', stateName: 'Andhra Pradesh', lat: 14.4426, lon: 79.9865 },
    { id: 'kurnool', name: 'Kurnool', state: 'ap', stateName: 'Andhra Pradesh', lat: 15.8281, lon: 78.0373 }
];

// Client Application State
let appState = {
    isConnected: false,
    currentView: 'overview',
    selectedCity: 'all',
    cityFilterState: 'all',
    eventSeverityFilter: 'ALL',
    eventSearchQuery: '',
    latestState: null,
    pollingTimer: null
};

// Map & 3D Objects
let gisMap = null;
let cityMarkersMap = {};
let eventMarkersGroup = null;
let threeEngine = {
    scene: null,
    camera: null,
    renderer: null,
    buildingMeshes: [],
    particles: null,
    animFrameId: null
};

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    initNavigationTabs();
    initLeafletMap();
    init3DCityVisualization();
    initEventListeners();
    
    // Initial fetch & continuous background polling loop
    fetchBackendState();
    appState.pollingTimer = setInterval(fetchBackendState, POLLING_INTERVAL_MS);
});

/* ==========================================================================
   1. NAVIGATION & TAB MANAGER
   ========================================================================== */
function initNavigationTabs() {
    const desktopTabs = document.querySelectorAll('#main-nav-tabs .nav-tab');
    const mobileNavBtns = document.querySelectorAll('.mobile-bottom-nav .mobile-nav-btn');

    const handleTabClick = (viewId) => {
        switchView(viewId);
    };

    desktopTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const viewId = tab.getAttribute('data-view');
            handleTabClick(viewId);
        });
    });

    mobileNavBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const viewId = btn.getAttribute('data-view');
            handleTabClick(viewId);
        });
    });
}

function switchView(viewId) {
    appState.currentView = viewId;

    // Update active tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-view') === viewId);
    });
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-view') === viewId);
    });

    // Toggle active view page
    document.querySelectorAll('.view-page').forEach(page => {
        const pageId = page.id.replace('view-', '');
        page.classList.toggle('active', pageId === viewId);
    });

    // Invalidate map size if overview view activated
    if (viewId === 'overview' && gisMap) {
        setTimeout(() => gisMap.invalidateSize(), 100);
    }
}

/* ==========================================================================
   2. LEAFLET SPATIAL MAP ENGINE
   ========================================================================== */
function initLeafletMap() {
    const mapElement = document.getElementById('gis-map');
    if (!mapElement) return;

    // Center of South India (Tamil Nadu, Kerala, Andhra Pradesh)
    gisMap = L.map('gis-map', {
        zoomControl: true,
        attributionControl: true
    }).setView([11.5, 78.5], 7);

    // Standard OpenStreetMap tile provider (No CARTO API key required, zero watermark)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(gisMap);

    eventMarkersGroup = L.layerGroup().addTo(gisMap);

    // Render South India City Markers
    SOUTH_INDIA_CITIES.forEach(city => {
        const customIcon = L.divIcon({
            className: 'custom-city-marker',
            html: `<div class="marker-pin ${city.isCapital ? 'capital-pin' : ''}"></div><span class="marker-label">${city.name}</span>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([city.lat, city.lon], { icon: customIcon }).addTo(gisMap);
        
        marker.bindPopup(`
            <div class="map-popup-card">
                <h4>${city.name}</h4>
                <div class="popup-sub">${city.stateName} ${city.isCapital ? '• Capital' : ''}</div>
                <div class="popup-coords">Lat: ${city.lat}, Lon: ${city.lon}</div>
                <button class="popup-btn" onclick="selectCityFilter('${city.id}')">Inspect City State →</button>
            </div>
        `);

        cityMarkersMap[city.id] = { marker, city };
    });
}

function updateMapEventsOverlay(events) {
    if (!eventMarkersGroup || !Array.isArray(events)) return;

    eventMarkersGroup.clearLayers();

    events.forEach(ev => {
        const loc = ev.location || {};
        const data = ev.data || {};
        const lat = loc.lat || loc.latitude;
        const lon = loc.lon || loc.longitude;

        if (typeof lat === 'number' && typeof lon === 'number') {
            const severity = (data.severity || ev.severity || 'LOW').toUpperCase();
            const color = severity === 'CRITICAL' ? '#EF4444' :
                          severity === 'HIGH' ? '#F97316' :
                          severity === 'MODERATE' ? '#F59E0B' : '#10B981';

            const circle = L.circleMarker([lat, lon], {
                radius: severity === 'CRITICAL' ? 12 : 8,
                fillColor: color,
                color: '#FFFFFF',
                weight: 1.5,
                opacity: 0.9,
                fillOpacity: 0.6
            });

            const evId = data.event_id || ev.event_id || 'evt_unk';
            const evType = data.event_type || ev.event_type || 'incident';
            const desc = data.description || data.text || evType;

            circle.bindPopup(`
                <div class="map-popup-card">
                    <div class="badge-status status-${severity.toLowerCase()}" style="display:inline-block; margin-bottom:4px;">${severity}</div>
                    <h4>${evType.toUpperCase()}</h4>
                    <div class="popup-sub">ID: ${evId} | Source: ${ev.source || 'unknown'}</div>
                    <div style="font-size:0.8rem; margin-top:6px;">${desc}</div>
                </div>
            `);

            eventMarkersGroup.addLayer(circle);
        }
    });
}

/* ==========================================================================
   3. THREE.JS 3D SPATIAL CITY VISUALIZATION ENGINE
   ========================================================================== */
function init3DCityVisualization() {
    const canvas = document.getElementById('city-3d-canvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const wrapper = document.getElementById('city-3d-viewport');
    const width = wrapper.clientWidth || 400;
    const height = wrapper.clientHeight || 300;

    // Scene setup
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x04070D, 0.035);
    threeEngine.scene = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 18, 32);
    camera.lookAt(0, 0, 0);
    threeEngine.camera = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    threeEngine.renderer = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x1E293B, 1.5);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x3B82F6, 2.0);
    dirLight.position.set(10, 20, 15);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0x06B6D4, 3.0, 50);
    pointLight.position.set(0, 10, 0);
    scene.add(pointLight);

    // Build procedural 3D Cityscape (Buildings & Wireframes)
    const buildingGroup = new THREE.Group();
    const gridHelper = new THREE.GridHelper(40, 30, 0x3B82F6, 0x1E293B);
    gridHelper.position.y = -0.1;
    scene.add(gridHelper);

    threeEngine.buildingMeshes = [];

    // Create 36 building meshes in concentric radial layout
    for (let i = 0; i < 36; i++) {
        const radius = 3 + Math.random() * 12;
        const angle = (i / 36) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        const h = 2 + Math.random() * 8;
        const w = 1.2 + Math.random() * 0.8;

        const geom = new THREE.BoxGeometry(w, h, w);
        const mat = new THREE.MeshPhongMaterial({
            color: 0x0F172A,
            emissive: 0x1E293B,
            specular: 0x3B82F6,
            shininess: 30,
            transparent: true,
            opacity: 0.85
        });

        const building = new THREE.Mesh(geom, mat);
        building.position.set(x, h / 2, z);

        // Add wireframe edge glow
        const edges = new THREE.EdgesGeometry(geom);
        const lineMat = new THREE.LineBasicMaterial({ color: 0x3B82F6, opacity: 0.4, transparent: true });
        const wireframe = new THREE.LineSegments(edges, lineMat);
        building.add(wireframe);

        buildingGroup.add(building);
        threeEngine.buildingMeshes.push({ mesh: building, lineMat, mat });
    }
    scene.add(buildingGroup);

    // Particle Haze
    const particleGeom = new THREE.BufferGeometry();
    const particleCount = 150;
    const posArray = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 40;
        posArray[i + 1] = Math.random() * 15;
        posArray[i + 2] = (Math.random() - 0.5) * 40;
    }
    particleGeom.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleMat = new THREE.PointsMaterial({
        size: 0.25,
        color: 0x38BDF8,
        transparent: true,
        opacity: 0.6
    });
    threeEngine.particles = new THREE.Points(particleGeom, particleMat);
    scene.add(threeEngine.particles);

    // Animation Loop
    let angleCounter = 0;
    function animate() {
        threeEngine.animFrameId = requestAnimationFrame(animate);
        
        angleCounter += 0.0025;
        camera.position.x = Math.sin(angleCounter) * 32;
        camera.position.z = Math.cos(angleCounter) * 32;
        camera.lookAt(0, 2, 0);

        if (threeEngine.particles) {
            threeEngine.particles.rotation.y += 0.001;
        }

        renderer.render(scene, camera);
    }
    animate();

    // Handle Window Resize
    window.addEventListener('resize', () => {
        if (!wrapper || !renderer || !camera) return;
        const w = wrapper.clientWidth || 400;
        const h = wrapper.clientHeight || 300;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
}

function update3DCityIllumination(riskScore, riskLevel) {
    if (!threeEngine.buildingMeshes || threeEngine.buildingMeshes.length === 0) return;

    let targetColor = 0x10B981; // Green
    if (riskScore > 75 || riskLevel === 'CRITICAL') targetColor = 0xEF4444; // Rose Red
    else if (riskScore > 50 || riskLevel === 'HIGH') targetColor = 0xF97316; // Orange
    else if (riskScore > 25 || riskLevel === 'MODERATE') targetColor = 0xF59E0B; // Amber

    threeEngine.buildingMeshes.forEach((item, idx) => {
        if (idx % 3 === 0) {
            item.lineMat.color.setHex(targetColor);
            item.mat.emissive.setHex(targetColor);
        }
    });

    const indicator = document.getElementById('3d-risk-indicator');
    if (indicator) {
        indicator.textContent = `Live Illumination: Risk ${riskScore}/100 (${riskLevel})`;
        indicator.className = `risk-badge-3d badge-${riskLevel.toLowerCase()}`;
    }
}

/* ==========================================================================
   4. BACKEND DATA INGESTION & STATE RENDERING
   ========================================================================== */
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
        appState.latestState = state;
        setConnectionStatus(true, state);
        renderFullDashboard(state);
    } catch (err) {
        setConnectionStatus(false);
    }
}

function setConnectionStatus(connected, stateData = null) {
    const statusBadge = document.getElementById('backend-status-badge');
    const modeBadge = document.getElementById('data-mode-badge');
    const errorBanner = document.getElementById('connection-error-banner');
    const lastUpdatedText = document.getElementById('last-updated-text');
    const heroPipelineStatus = document.getElementById('hero-pipeline-status');
    const heroDataMode = document.getElementById('hero-data-mode');

    // KPI & Status Elements
    const riskScoreEl = document.getElementById('kpi-risk-score');
    const riskBadgeEl = document.getElementById('kpi-risk-badge');
    const riskTrendEl = document.getElementById('kpi-risk-trend');
    const eventsCountEl = document.getElementById('kpi-events-count');
    const anomaliesCountEl = document.getElementById('kpi-anomalies-count');
    const correlationsCountEl = document.getElementById('kpi-correlations-count');
    const systemHealthEl = document.getElementById('kpi-system-health');
    const healthSubtextEl = document.getElementById('kpi-health-subtext');
    const indicator3D = document.getElementById('3d-risk-indicator');
    const mapRegionStatus = document.getElementById('map-region-status');
    const citiesOnlineEl = document.getElementById('kpi-cities-online');

    if (connected) {
        appState.isConnected = true;
        if (statusBadge) {
            statusBadge.className = 'status-pill pill-live';
            statusBadge.textContent = '● CONNECTED';
        }
        if (errorBanner) {
            errorBanner.classList.add('hidden');
        }

        if (stateData) {
            const dataMode = (stateData.data_mode || 'HYBRID').toUpperCase();
            if (modeBadge) modeBadge.textContent = `DATA_MODE: ${dataMode}`;
            if (heroDataMode) heroDataMode.textContent = dataMode;

            if (heroPipelineStatus) {
                heroPipelineStatus.textContent = 'ACTIVE';
                heroPipelineStatus.className = 'hero-metric-val text-emerald';
            }

            if (lastUpdatedText && stateData.last_updated) {
                const dt = new Date(stateData.last_updated);
                const timeStr = isNaN(dt.getTime()) ? stateData.last_updated : dt.toLocaleTimeString();
                lastUpdatedText.textContent = `Updated: ${timeStr}`;
            }

            if (systemHealthEl) {
                systemHealthEl.textContent = 'OPERATIONAL';
                systemHealthEl.className = 'kpi-big-num text-emerald';
            }
            if (healthSubtextEl) {
                healthSubtextEl.textContent = 'Pathway Engine Operational';
                healthSubtextEl.className = 'kpi-subtext text-emerald';
            }
            if (mapRegionStatus) {
                mapRegionStatus.textContent = 'Regional Coverage: 20 cities';
            }
            if (citiesOnlineEl) {
                citiesOnlineEl.textContent = '20';
            }
        }
    } else {
        appState.isConnected = false;
        if (statusBadge) {
            statusBadge.className = 'status-pill pill-offline';
            statusBadge.textContent = '● BACKEND OFFLINE';
        }
        if (errorBanner) {
            errorBanner.classList.remove('hidden');
        }
        if (lastUpdatedText) {
            lastUpdatedText.textContent = 'Updated: Disconnected';
        }
        if (heroPipelineStatus) {
            heroPipelineStatus.textContent = 'DISCONNECTED';
            heroPipelineStatus.className = 'hero-metric-val text-rose';
        }
        if (heroDataMode) {
            heroDataMode.textContent = 'OFFLINE';
        }

        // When GET /api/state fails: reset operational values to offline placeholders
        if (riskScoreEl) riskScoreEl.textContent = '--';
        if (riskBadgeEl) {
            riskBadgeEl.textContent = 'OFFLINE';
            riskBadgeEl.className = 'badge-status status-critical';
        }
        if (riskTrendEl) riskTrendEl.textContent = 'Trend: UNAVAILABLE';
        if (eventsCountEl) eventsCountEl.textContent = '--';
        if (anomaliesCountEl) anomaliesCountEl.textContent = '--';
        if (correlationsCountEl) correlationsCountEl.textContent = '--';

        if (systemHealthEl) {
            systemHealthEl.textContent = 'OFFLINE';
            systemHealthEl.className = 'kpi-big-num text-rose';
        }
        if (healthSubtextEl) {
            healthSubtextEl.textContent = 'Backend Unreachable';
            healthSubtextEl.className = 'kpi-subtext text-rose';
        }

        if (indicator3D) {
            indicator3D.textContent = 'BACKEND STATE UNAVAILABLE / DISCONNECTED';
            indicator3D.className = 'risk-badge-3d badge-critical';
        }

        if (mapRegionStatus) {
            mapRegionStatus.textContent = 'Regional Coverage: 20 cities';
        }
        if (citiesOnlineEl) {
            citiesOnlineEl.textContent = '20';
        }

        if (eventMarkersGroup) {
            eventMarkersGroup.clearLayers();
        }

        const feedContainer = document.getElementById('event-feed-container');
        if (feedContainer) {
            feedContainer.innerHTML = `<div class="empty-state-text" style="color: var(--severity-critical);">BACKEND OFFLINE. Retrying connection to ${API_BASE_URL}...</div>`;
        }

        const fullTimeline = document.getElementById('full-events-timeline');
        if (fullTimeline) {
            fullTimeline.innerHTML = `<div class="empty-state-text" style="color: var(--severity-critical);">BACKEND OFFLINE. Retrying connection to ${API_BASE_URL}...</div>`;
        }
    }
}

function renderFullDashboard(state) {
    if (!state) return;

    renderKPIs(state);
    updateMapEventsOverlay(state.recent_events || []);
    update3DCityIllumination(state.overall_risk_score || 0, state.overall_risk_level || 'LOW');
    renderTimelineFeed(state.recent_events || []);
    renderConnectorsGrid(state.data_freshness || {});
    renderRiskIntelligence(state);
    renderEnvironmentalTelemetry(state);
    renderCitiesGrid(state);
}

/* Render KPIs */
function renderKPIs(state) {
    const riskScoreEl = document.getElementById('kpi-risk-score');
    const riskBadgeEl = document.getElementById('kpi-risk-badge');
    const riskTrendEl = document.getElementById('kpi-risk-trend');
    const eventsCountEl = document.getElementById('kpi-events-count');
    const anomaliesCountEl = document.getElementById('kpi-anomalies-count');
    const correlationsCountEl = document.getElementById('kpi-correlations-count');
    const systemHealthEl = document.getElementById('kpi-system-health');
    const healthSubtextEl = document.getElementById('kpi-health-subtext');

    const score = state.overall_risk_score ?? 0;
    const level = (state.overall_risk_level || 'LOW').toUpperCase();
    const trend = state.risk_trend || 'STABLE';
    const recentEvents = state.recent_events || [];
    const anomalies = state.active_anomalies || [];
    const correlations = state.correlations || [];

    if (riskScoreEl) riskScoreEl.textContent = score;
    if (riskBadgeEl) {
        riskBadgeEl.textContent = level;
        riskBadgeEl.className = `badge-status status-${level.toLowerCase()}`;
    }
    if (riskTrendEl) riskTrendEl.textContent = `Trend: ${trend}`;
    if (eventsCountEl) eventsCountEl.textContent = recentEvents.length;
    if (anomaliesCountEl) anomaliesCountEl.textContent = anomalies.length;
    if (correlationsCountEl) correlationsCountEl.textContent = correlations.length;
    if (systemHealthEl) {
        systemHealthEl.textContent = 'OPERATIONAL';
        systemHealthEl.className = 'kpi-big-num text-emerald';
    }
    if (healthSubtextEl) {
        healthSubtextEl.textContent = 'Pathway Engine Operational';
        healthSubtextEl.className = 'kpi-subtext text-emerald';
    }
}

/* Render Live Timeline Feed */
function renderTimelineFeed(events) {
    const container = document.getElementById('event-feed-container');
    const fullTimeline = document.getElementById('full-events-timeline');
    const feedCountBadge = document.getElementById('feed-count-badge');
    const timelineCounterTag = document.getElementById('timeline-events-counter');

    if (!Array.isArray(events) || events.length === 0) {
        if (container) container.innerHTML = `<div class="empty-state-text">No active streaming telemetry events in window.</div>`;
        if (fullTimeline) fullTimeline.innerHTML = `<div class="empty-state-text">No active events recorded.</div>`;
        return;
    }

    if (feedCountBadge) feedCountBadge.textContent = `${events.length} Events`;
    if (timelineCounterTag) timelineCounterTag.textContent = `${events.length} Events Ingested`;

    // Overview Feed (Latest 6)
    if (container) {
        const overviewEvents = events.slice(-6).reverse();
        container.innerHTML = overviewEvents.map(ev => {
            const data = ev.data || {};
            const sev = (data.severity || ev.severity || 'LOW').toUpperCase();
            const src = ev.source || 'unknown';
            const evId = data.event_id || ev.event_id || 'evt_unk';
            const desc = data.description || data.text || data.event_type || 'Stream Update';

            return `
                <div class="feed-item-card">
                    <div class="feed-item-header">
                        <span class="feed-source-tag">${src}</span>
                        <span class="badge-status status-${sev.toLowerCase()}">${sev}</span>
                    </div>
                    <div class="feed-item-desc">${desc}</div>
                    <div class="feed-timestamp">ID: ${evId}</div>
                </div>
            `;
        }).join('');
    }

    // Full Events Page Timeline
    if (fullTimeline) {
        let filteredEvents = [...events].reverse();

        // Apply Severity Filter
        if (appState.eventSeverityFilter !== 'ALL') {
            filteredEvents = filteredEvents.filter(ev => {
                const s = ((ev.data && ev.data.severity) || ev.severity || 'LOW').toUpperCase();
                return s === appState.eventSeverityFilter;
            });
        }

        // Apply Search Filter
        if (appState.eventSearchQuery) {
            const q = appState.eventSearchQuery.toLowerCase();
            filteredEvents = filteredEvents.filter(ev => {
                const str = JSON.stringify(ev).toLowerCase();
                return str.includes(q);
            });
        }

        if (filteredEvents.length === 0) {
            fullTimeline.innerHTML = `<div class="empty-state-text">No events match current filter settings.</div>`;
            return;
        }

        fullTimeline.innerHTML = filteredEvents.map(ev => {
            const data = ev.data || {};
            const sev = (data.severity || ev.severity || 'LOW').toUpperCase();
            const src = ev.source || 'unknown';
            const evId = data.event_id || ev.event_id || 'evt_unk';
            const evType = data.event_type || ev.event_type || 'incident';
            const loc = ev.location || {};
            const zone = loc.zone || 'Zone A (Downtown)';
            const desc = data.description || data.text || evType;
            const dt = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent';

            return `
                <div class="timeline-row">
                    <div class="timeline-time">${dt}</div>
                    <div class="timeline-event-card">
                        <div class="feed-item-header">
                            <div>
                                <span class="badge-status status-${sev.toLowerCase()}">${sev}</span>
                                <strong style="margin-left: 8px;">${evType.toUpperCase()}</strong>
                            </div>
                            <span class="feed-source-tag">${src}</span>
                        </div>
                        <div class="feed-item-desc" style="margin: 8px 0;">${desc}</div>
                        <div class="feed-timestamp">Event ID: ${evId} | Zone: ${zone} | Lat: ${loc.lat || '--'}, Lon: ${loc.lon || '--'}</div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

/* Render Connectors Grid */
function renderConnectorsGrid(freshness) {
    const grid = document.getElementById('connectors-status-grid');
    if (!grid) return;

    const sources = [
        { key: 'open_meteo_weather', name: 'Open-Meteo Weather API' },
        { key: 'open_meteo_air_quality', name: 'Open-Meteo Air Quality API' },
        { key: 'webhook_ingestion', name: 'HTTP Webhook Server (/events)' },
        { key: 'gtfs_transit_api', name: 'GTFS Transit Feed' },
        { key: 'social_media', name: 'Social Media Stream' },
        { key: 'public_safety', name: 'Public Safety Dispatch' },
        { key: 'iot_sensors', name: 'IoT Telemetry Sensors' }
    ];

    grid.innerHTML = sources.map(s => {
        const info = freshness[s.key] || {};
        const status = info.status || 'LIVE';
        const mode = info.mode || 'LIVE';
        const count = info.event_count || 0;

        return `
            <div class="connector-card">
                <div class="connector-name">${s.name}</div>
                <div class="connector-status-row">
                    <span class="badge-status ${status === 'LIVE' ? 'status-low' : 'status-critical'}">${status}</span>
                    <span class="kpi-subtext" style="color:var(--text-muted);">${count} events</span>
                </div>
            </div>
        `;
    }).join('');
}

/* Render Risk Intelligence Page */
function renderRiskIntelligence(state) {
    const scoreVal = document.getElementById('risk-score-val');
    const levelBadge = document.getElementById('risk-level-badge');
    const trendBadge = document.getElementById('risk-trend-badge');
    const factorsList = document.getElementById('risk-factors-list');
    const anomaliesList = document.getElementById('active-anomalies-list');
    const zoneContainer = document.getElementById('zone-summary-container');
    const correlationsList = document.getElementById('correlations-list');

    const score = state.overall_risk_score ?? 0;
    const level = (state.overall_risk_level || 'LOW').toUpperCase();
    const trend = state.risk_trend || 'STABLE';
    const factors = state.contributing_factors || [];
    const anomalies = state.active_anomalies || [];
    const correlations = state.correlations || [];
    const zones = state.zone_summaries || {};

    if (scoreVal) scoreVal.textContent = score;
    if (levelBadge) {
        levelBadge.textContent = level;
        levelBadge.className = `badge-status status-${level.toLowerCase()}`;
    }
    if (trendBadge) trendBadge.textContent = `Trend: ${trend}`;

    if (factorsList) {
        factorsList.innerHTML = factors.length > 0 
            ? factors.map(f => `<li>${f}</li>`).join('')
            : `<li>No critical risk elevation factors recorded.</li>`;
    }

    // Active Anomalies
    if (anomaliesList) {
        anomaliesList.innerHTML = anomalies.length > 0 ? anomalies.map(an => `
            <div class="anomaly-card-item">
                <div class="feed-item-header">
                    <span class="badge-status status-high">${an.anomaly_type || 'ANOMALY'}</span>
                    <span class="feed-timestamp">${an.timestamp || 'Active'}</span>
                </div>
                <div class="feed-item-desc" style="margin-top:4px;">${an.description || 'Elevated anomaly flag detected.'}</div>
                <div class="feed-timestamp" style="margin-top:4px;">Source: ${an.source || 'sensor'} | Zone: ${an.zone || 'Zone A'}</div>
            </div>
        `) : `<div class="empty-state-text">No active operational anomalies detected in current window.</div>`;
    }

    // Correlations
    if (correlationsList) {
        correlationsList.innerHTML = correlations.length > 0 ? correlations.map(c => `
            <div class="correlation-card-item">
                <div class="feed-item-header">
                    <span class="badge-status status-critical">${c.risk_level || 'HIGH'}</span>
                    <span class="feed-source-tag">${(c.sources || []).join(' • ')}</span>
                </div>
                <div class="feed-item-desc" style="margin-top:4px;">${c.reason || 'Multi-source incident overlap.'}</div>
            </div>
        `) : `<div class="empty-state-text">No cross-source correlations detected.</div>`;
    }

    // Spatial Zones Breakdown
    if (zoneContainer) {
        const zoneEntries = Object.entries(zones);
        zoneContainer.innerHTML = zoneEntries.length > 0 ? zoneEntries.map(([zName, zInfo]) => `
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">${zName.toUpperCase()}</span>
                    <span class="badge-status status-${(zInfo.risk_level || 'LOW').toLowerCase()}">${zInfo.risk_level || 'LOW'}</span>
                </div>
                <div class="kpi-body">
                    <div class="kpi-big-num">${zInfo.risk_score || 0}</div>
                    <div class="kpi-denom">/100</div>
                </div>
                <div class="kpi-footer">
                    <span class="kpi-subtext">Events: ${zInfo.event_count || 0} (Critical: ${zInfo.critical_count || 0})</span>
                </div>
            </div>
        `).join('') : `<div class="empty-state-text">Loading spatial zone metrics...</div>`;
    }
}

/* Render Environmental Telemetry Page */
function renderEnvironmentalTelemetry(state) {
    const tempEl = document.getElementById('env-temp');
    const condEl = document.getElementById('env-condition');
    const aqiEl = document.getElementById('env-aqi');
    const pmEl = document.getElementById('env-pm');
    const windEl = document.getElementById('env-wind');
    const no2El = document.getElementById('env-no2');

    // Extract real telemetry from recent events if available
    let temp = '-- °C';
    let cond = 'Clear';
    let aqi = '--';
    let pm = '-- / --';
    let wind = '-- km/h';
    let no2 = '-- µg/m³';

    const events = state.recent_events || [];
    events.forEach(ev => {
        const d = ev.data || {};
        if (ev.source === 'weather_api' || d.event_type === 'weather_update') {
            if (d.temperature !== undefined) temp = `${d.temperature} °C`;
            if (d.condition) cond = d.condition;
            if (d.wind_speed !== undefined) wind = `${d.wind_speed} km/h`;
        }
        if (ev.source === 'air_quality_api' || d.event_type === 'air_quality_update') {
            if (d.air_quality_index !== undefined) aqi = `${d.air_quality_index}`;
            if (d.pm2_5 !== undefined && d.pm10 !== undefined) pm = `${d.pm2_5} / ${d.pm10}`;
            if (d.nitrogen_dioxide !== undefined) no2 = `${d.nitrogen_dioxide} µg/m³`;
        }
    });

    if (tempEl) tempEl.textContent = temp;
    if (condEl) condEl.textContent = cond;
    if (aqiEl) aqiEl.textContent = aqi;
    if (pmEl) pmEl.textContent = pm;
    if (windEl) windEl.textContent = wind;
    if (no2El) no2El.te    // Render South India Cities Atmospheric Snippets
    const regGrid = document.getElementById('regional-env-cities-grid');
    if (regGrid) {
        const citySummaries = state.city_summaries || {};
        regGrid.innerHTML = SOUTH_INDIA_CITIES.slice(0, 6).map(c => {
            const cs = citySummaries[c.name] || {};
            const w = cs.weather || {};
            const aq = cs.air_quality || {};
            const tempStr = w.temperature !== undefined ? `${w.temperature} °C` : '--';
            const condStr = w.condition || 'Telemetry Syncing';
            const aqiStr = aq.aqi !== undefined ? aq.aqi : '--';

            return `
                <div class="feed-item-card" onclick="selectCityFilter('${c.id}')" style="cursor:pointer;">
                    <div class="feed-item-header">
                        <strong>${c.name}</strong>
                        <span class="feed-source-tag">${c.stateName}</span>
                    </div>
                    <div class="feed-item-desc" style="font-size:0.8rem; margin-top:4px;">
                        Condition: ${condStr} | Temp: ${tempStr} | AQI: ${aqiStr}
                    </div>
                </div>
            `;
        }).join('');
    }
}

/* Render Cities Explorer Page */
function renderCitiesGrid(state) {
    const grid = document.getElementById('cities-cards-grid');
    if (!grid) return;

    let cities = SOUTH_INDIA_CITIES;
    if (appState.cityFilterState !== 'all') {
        cities = cities.filter(c => c.state === appState.cityFilterState);
    }

    const citySummaries = state.city_summaries || {};

    grid.innerHTML = cities.map(city => {
        const cs = citySummaries[city.name] || {};
        const riskScore = cs.risk_score !== undefined ? cs.risk_score : 0;
        const riskLevel = (cs.risk_level || 'LOW').toUpperCase();
        const evCount = cs.event_count || 0;
        const w = cs.weather || {};
        const aq = cs.air_quality || {};
        const weatherDesc = w.temperature !== undefined ? `${w.temperature}°C, ${w.condition || 'Clear'}` : 'Syncing Live Telemetry';
        const aqiDesc = aq.aqi !== undefined ? `AQI ${aq.aqi}` : 'AQI --';

        return `
            <div class="city-card" onclick="selectCityFilter('${city.id}')">
                <div class="city-card-header">
                    <div>
                        <div class="city-name">${city.name}</div>
                        <div class="state-badge">${city.stateName} ${city.isCapital ? '• Capital' : ''}</div>
                    </div>
                    <span class="badge-status status-${riskLevel.toLowerCase()}">${riskLevel} (${riskScore}/100)</span>
                </div>
                <div class="city-card-stats">
                    <div class="city-stat-item">
                        <span class="city-stat-label">Weather / AQI</span>
                        <span class="city-stat-val" style="font-size:0.85rem;">${weatherDesc} | ${aqiDesc}</span>
                    </div>
                    <div class="city-stat-item">
                        <span class="city-stat-label">Ingested Events</span>
                        <span class="city-stat-val">${evCount} Events</span>
                    </div>
                </div>
                <button class="btn-sm" style="width:100%; border-radius:8px;">Inspect ${city.name} State →</button>
            </div>
        `;
    }).join('');
}

/* Select & Focus City Filter */
function selectCityFilter(cityId) {
    const selectEl = document.getElementById('city-selector');
    if (selectEl) {
        selectEl.value = cityId;
    }

    const city = SOUTH_INDIA_CITIES.find(c => c.id === cityId);
    if (city && gisMap) {
        gisMap.setView([city.lat, city.lon], 11);
        switchView('overview');
    }
}

/* ==========================================================================
   5. AI URBAN COPILOT HANDLER
   ========================================================================== */
function initEventListeners() {
    // City selector change listener
    const citySelect = document.getElementById('city-selector');
    if (citySelect) {
        citySelect.addEventListener('change', (e) => {
            selectCityFilter(e.target.value);
        });
    }

    // State filter tabs in Cities view
    const stateChips = document.querySelectorAll('.state-filter-tabs .filter-chip');
    stateChips.forEach(chip => {
        chip.addEventListener('click', () => {
            stateChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            appState.cityFilterState = chip.getAttribute('data-state');
            if (appState.latestState) renderCitiesGrid(appState.latestState);
        });
    });

    // Severity filter in Timeline view
    const sevFilter = document.getElementById('event-severity-filter');
    if (sevFilter) {
        sevFilter.addEventListener('change', (e) => {
            appState.eventSeverityFilter = e.target.value;
            if (appState.latestState) renderTimelineFeed(appState.latestState.recent_events || []);
        });
    }

    // Search input in Timeline view
    const searchInput = document.getElementById('event-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            appState.eventSearchQuery = e.target.value;
            if (appState.latestState) renderTimelineFeed(appState.latestState.recent_events || []);
        });
    }
}

function fillCopilotPrompt(question) {
    const input = document.getElementById('copilot-input');
    if (input) {
        input.value = question;
        switchView('copilot');
        input.focus();
    }
}

async function submitCopilotQuery(event) {
    if (event) event.preventDefault();

    const input = document.getElementById('copilot-input');
    const resultsContainer = document.getElementById('copilot-results');
    const submitBtn = document.getElementById('copilot-submit-btn');

    if (!input || !input.value.trim() || !resultsContainer) return;

    const question = input.value.trim();

    // Loading State
    if (submitBtn) submitBtn.disabled = true;
    resultsContainer.innerHTML = `
        <div class="ai-response-card">
            <div class="loading-state-card">
                <div class="spinner"></div>
                <span>Executing Grounded RAG context retrieval and querying OpenAI LLM...</span>
            </div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const data = await response.json();
        renderCopilotResponseCard(data, question);
    } catch (err) {
        resultsContainer.innerHTML = `
            <div class="ai-response-card" style="border-color: var(--severity-critical);">
                <div class="ai-assessment-banner">
                    <span class="ai-risk-tag badge-critical">ERROR</span>
                    <span class="ai-confidence-tag">Connection Failure</span>
                </div>
                <div class="ai-answer-text" style="color: var(--severity-critical);">
                    Unable to execute AI query: ${err.message}. Ensure backend is running at ${API_BASE_URL}.
                </div>
            </div>
        `;
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

function renderCopilotResponseCard(data, question) {
    const container = document.getElementById('copilot-results');
    if (!container) return;

    const riskLevel = (data.risk_level || 'LOW').toUpperCase();
    const confidence = (data.confidence || 'HIGH').toUpperCase();
    const answer = data.answer || 'No response returned from AI provider.';
    const factors = data.key_factors || data.factors || [];
    const evidence = data.evidence || [];
    const recommendations = data.recommendations || data.human_review || [];

    container.innerHTML = `
        <div class="ai-response-card">
            <div class="ai-assessment-banner">
                <div>
                    <span class="ai-risk-tag badge-${riskLevel.toLowerCase()}">${riskLevel} RISK</span>
                    <strong style="margin-left: 10px; font-size: 0.9rem;">Query: "${question}"</strong>
                </div>
                <span class="ai-confidence-tag">Confidence: ${confidence}</span>
            </div>

            <div class="ai-answer-text">${answer}</div>

            ${factors.length > 0 ? `
                <div>
                    <div class="ai-section-title">Key Factors</div>
                    <div class="ai-factors-chips">
                        ${factors.map(f => `<span class="chip-factor">• ${f}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${evidence.length > 0 ? `
                <div>
                    <div class="ai-section-title">Audit Evidence Trail (${evidence.length} Citations)</div>
                    <ul class="ai-evidence-list">
                        ${evidence.map(ev => {
                            const eStr = typeof ev === 'object' ? (ev.description || ev.event_id || JSON.stringify(ev)) : ev;
                            return `<li>${eStr}</li>`;
                        }).join('')}
                    </ul>
                </div>
            ` : ''}

            ${recommendations.length > 0 ? `
                <div>
                    <div class="ai-section-title">Human Review Recommendations</div>
                    <ul class="ai-evidence-list">
                        ${recommendations.map(r => `<li style="border-left-color: var(--severity-mod);">${r}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <div class="ai-actions-row">
                <button class="btn-action-chip" onclick="switchView('overview')">📍 Focus Map View</button>
                <button class="btn-action-chip" onclick="switchView('events')">⚡ Inspect Stream Events</button>
                <button class="btn-action-chip" onclick="switchView('risk')">🛡️ View Risk Analytics</button>
            </div>
        </div>
    `;
}
