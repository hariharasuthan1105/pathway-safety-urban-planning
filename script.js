    // Global state
        let currentUser = null;
        let currentAuthTab = 'signin';
        let currentDashboardTab = 'overview';

        // Mock data
        let cityMetrics = {
            population: { value: "2.4M", change: 2.1, progress: 78, status: "normal" },
            traffic: { value: "68%", change: -5.2, progress: 68, status: "warning" },
            connectivity: { value: "94%", change: 1.8, progress: 94, status: "normal" },
            energy: { value: "1.2GW", change: -3.1, progress: 85, status: "normal" },
            water: { value: "98%", change: 0.5, progress: 98, status: "normal" },
            airQuality: { value: "Good", change: 12.3, progress: 76, status: "normal" },
            incidents: { value: "23", change: -15.4, progress: 15, status: "critical" },
            response: { value: "4.2 min", change: -8.5, progress: 88, status: "normal" }
        };

        let safetyAlerts = [
            {
                id: "1",
                type: "incident",
                severity: "high",
                title: "Crowd Gathering Detected",
                location: "Central Park West",
                time: "2 min ago",
                description: "Unusual crowd density detected via camera network and social media analysis",
                status: "active",
                sources: ["CCTV Network", "Social Media", "Foot Traffic Sensors"]
            },
            {
                id: "2",
                type: "emergency",
                severity: "critical",
                title: "Traffic Accident Reported",
                location: "5th Avenue & 42nd St",
                time: "5 min ago",
                description: "Multi-vehicle accident blocking major intersection",
                status: "responding",
                sources: ["911 Dispatch", "Traffic Cameras", "Citizen Reports"]
            },
            {
                id: "3",
                type: "anomaly",
                severity: "medium",
                title: "Noise Level Spike",
                location: "Times Square",
                time: "8 min ago",
                description: "Noise levels 40% above normal, possible event or disturbance",
                status: "active",
                sources: ["Noise Sensors", "Audio Analysis"]
            }
        ];

        let sensorData = [
            { location: "Downtown", noiseLevel: 65, crowdDensity: 78, trafficFlow: 85, status: "normal" },
            { location: "Financial District", noiseLevel: 72, crowdDensity: 45, trafficFlow: 92, status: "warning" },
            { location: "Central Park", noiseLevel: 55, crowdDensity: 95, trafficFlow: 35, status: "error" },
            { location: "Times Square", noiseLevel: 88, crowdDensity: 150, trafficFlow: 75, status: "error" }
        ];

        let chatMessages = [
            {
                id: "1",
                type: "assistant",
                content: "Hello! I'm your Urban Planning AI Assistant. I can help you analyze city data, traffic patterns, and provide insights for urban development. What would you like to know?",
                timestamp: new Date()
            }
        ];

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            startLoadingSequence();
            setupEventListeners();
        });

        // Loading sequence
        function startLoadingSequence() {
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            
            const loadingTexts = [
                'Initializing city monitoring systems...',
                'Connecting to sensor networks...',
                'Loading traffic data feeds...',
                'Establishing AI analysis engines...',
                'Preparing dashboard interface...',
                'System ready!'
            ];
            
            let progress = 0;
            let textIndex = 0;
            
            const interval = setInterval(() => {
                progress += Math.random() * 15 + 5;
                
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                    setTimeout(completeLoading, 500);
                }
                
                progressFill.style.width = progress + '%';
                progressText.textContent = `${loadingTexts[textIndex]} ${Math.round(progress)}%`;
                
                if (textIndex < loadingTexts.length - 1 && progress > (textIndex + 1) * (100 / loadingTexts.length)) {
                    textIndex++;
                }
            }, 200);
        }

        function completeLoading() {
            const loadingScreen = document.getElementById('loading-screen');
            const mainApp = document.getElementById('main-app');
            
            loadingScreen.style.opacity = '0';
            loadingScreen.style.transition = 'opacity 0.5s ease-out';
            
            setTimeout(() => {
                loadingScreen.style.display = 'none';
                mainApp.classList.remove('hidden');
            }, 500);
        }

        // Event listeners
        function setupEventListeners() {
            // Auth form
            document.getElementById('auth-form').addEventListener('submit', handleAuthSubmit);
            
            // Tab navigation
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const tab = e.target.closest('.tab-btn').dataset.tab;
                    switchDashboardTab(tab);
                });
            });
            
            // Chat input
            const chatInput = document.getElementById('chat-input-field');
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendChatMessage();
                }
            });
            
            // Start real-time updates
            startRealTimeUpdates();
        }

        // Auth functions
        function openAuthModal() {
            document.getElementById('auth-modal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeAuthModal() {
            document.getElementById('auth-modal').classList.remove('active');
            document.body.style.overflow = 'auto';
            resetAuthForm();
        }

        function switchAuthTab(tab) {
            currentAuthTab = tab;
            
            // Update tab buttons
            document.querySelectorAll('.auth-tab').forEach(tabBtn => {
                tabBtn.classList.remove('active');
            });
            document.querySelectorAll('.auth-tab').forEach(tabBtn => {
                if (tabBtn.textContent.toLowerCase().includes(tab)) {
                    tabBtn.classList.add('active');
                }
            });
            
            // Update form
            const nameGroup = document.getElementById('name-group');
            const confirmPasswordGroup = document.getElementById('confirm-password-group');
            const authTitle = document.getElementById('auth-title');
            const authDescription = document.getElementById('auth-description');
            const authButtonText = document.getElementById('auth-button-text');
            const authSwitchBtn = document.getElementById('auth-switch-btn');
            
            if (tab === 'signup') {
                nameGroup.classList.remove('hidden');
                confirmPasswordGroup.classList.remove('hidden');
                authTitle.textContent = 'Join Urban Intelligence';
                authDescription.textContent = 'Create your account to access city insights';
                authButtonText.textContent = 'Create Account';
                authSwitchBtn.textContent = 'Already have an account? Sign in';
                document.getElementById('name').required = true;
                document.getElementById('confirm-password').required = true;
            } else {
                nameGroup.classList.add('hidden');
                confirmPasswordGroup.classList.add('hidden');
                authTitle.textContent = 'Welcome Back';
                authDescription.textContent = 'Sign in to continue monitoring your city';
                authButtonText.textContent = 'Sign In';
                authSwitchBtn.textContent = 'Don\'t have an account? Sign up';
                document.getElementById('name').required = false;
                document.getElementById('confirm-password').required = false;
            }
        }

        function toggleAuthMode() {
            switchAuthTab(currentAuthTab === 'signin' ? 'signup' : 'signin');
        }

        function handleAuthSubmit(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const email = formData.get('email');
            const password = formData.get('password');
            const name = formData.get('name') || email.split('@')[0];
            
            if (!email || !password) {
                alert('Please fill in all required fields.');
                return;
            }
            
            // Simulate authentication
            setTimeout(() => {
                currentUser = { email, name };
                
                // Update UI
                document.getElementById('user-name').textContent = name;
                document.getElementById('user-email').textContent = email;
                document.getElementById('user-avatar').textContent = name.charAt(0).toUpperCase();
                
                // Show dashboard
                closeAuthModal();
                showDashboard();
                initializeDashboard();
            }, 1000);
        }

        function resetAuthForm() {
            document.getElementById('auth-form').reset();
            currentAuthTab = 'signin';
            switchAuthTab('signin');
        }

        // Dashboard functions
        function showDashboard() {
            document.getElementById('landing-page').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
        }

        function signOut() {
            currentUser = null;
            document.getElementById('dashboard').classList.add('hidden');
            document.getElementById('landing-page').classList.remove('hidden');
        }

        function switchDashboardTab(tab) {
            currentDashboardTab = tab;
            
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tab}-tab`).classList.add('active');
            
            // Initialize content
            if (tab === 'overview') {
                updateMetricsGrid();
            } else if (tab === 'safety') {
                updateSafetyPanel();
            } else if (tab === 'chat') {
                updateChatInterface();
            }
        }

        function initializeDashboard() {
            updateMetricsGrid();
            updateSafetyPanel();
            updateChatInterface();
        }

        // Metrics functions
        function updateMetricsGrid() {
            const metricsGrid = document.getElementById('metrics-grid');
            if (!metricsGrid) return;
            
            const metricConfigs = [
                { key: 'population', title: 'Active Population', icon: 'users', color: 'background: #3b82f6' },
                { key: 'traffic', title: 'Traffic Congestion', icon: 'car', color: 'background: #f59e0b' },
                { key: 'connectivity', title: 'Network Coverage', icon: 'wifi', color: 'background: #10b981' },
                { key: 'energy', title: 'Energy Consumption', icon: 'zap', color: 'background: #f59e0b' },
                { key: 'water', title: 'Water Quality', icon: 'droplets', color: 'background: #06b6d4' },
                { key: 'airQuality', title: 'Air Quality', icon: 'wind', color: 'background: #8b5cf6' },
                { key: 'incidents', title: 'Active Incidents', icon: 'alert-triangle', color: 'background: #ef4444' },
                { key: 'response', title: 'Emergency Response', icon: 'phone', color: 'background: #6366f1' }
            ];
            
            const iconSvgs = {
                users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
                car: '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18.7 9H5.3L3.5 11.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
                wifi: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
                zap: '<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>',
                droplets: '<path d="M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"/>',
                wind: '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
                'alert-triangle': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
                phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>'
            };
            
            metricsGrid.innerHTML = metricConfigs.map(config => {
                const metric = cityMetrics[config.key];
                const changeClass = metric.change >= 0 ? 'positive' : 'negative';
                const cardClass = metric.status === 'warning' ? 'warning' : metric.status === 'critical' ? 'critical' : '';
                
                return `
                    <div class="metric-card ${cardClass}">
                        <div class="metric-header">
                            <div class="metric-title">${config.title}</div>
                            <div class="metric-icon" style="${config.color}">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    ${iconSvgs[config.icon]}
                                </svg>
                            </div>
                        </div>
                        <div class="metric-value">${metric.value}</div>
                        <div class="metric-change ${changeClass}">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"/>
                                <polyline points="17,6 23,6 23,12"/>
                            </svg>
                            <span>${Math.abs(metric.change).toFixed(1)}%</span>
                        </div>
                        ${metric.progress ? `
                            <div class="metric-progress">
                                <div class="metric-progress-fill" style="width: ${metric.progress}%"></div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        // Safety panel functions
        function updateSafetyPanel() {
            updateAlertsList();
            updateSensorsList();
        }

        function updateAlertsList() {
            const alertsList = document.getElementById('alerts-list');
            if (!alertsList) return;
            
            alertsList.innerHTML = safetyAlerts.map(alert => {
                const severityClass = `badge-${alert.severity === 'critical' ? 'critical' : alert.severity === 'high' ? 'high' : 'medium'}`;
                
                return `
                    <div class="alert-item">
                        <div class="alert-header">
                            <div>
                                <div class="alert-badges">
                                    <span class="badge ${severityClass}">${alert.severity.toUpperCase()}</span>
                                    <span class="badge badge-outline">${alert.type}</span>
                                </div>
                                <h4 style="font-weight: 600; margin: 0.5rem 0;">${alert.title}</h4>
                                <div class="alert-info">
                                    <span>📍 ${alert.location}</span>
                                    <span>🕒 ${alert.time}</span>
                                </div>
                            </div>
                        </div>
                        <div class="alert-description">${alert.description}</div>
                        <div class="alert-footer">
                            <div class="alert-sources">
                                <span class="text-xs" style="color: var(--text-light);">Sources:</span>
                                ${alert.sources.map(source => `<span class="source-tag">${source}</span>`).join('')}
                            </div>
                            <button class="btn" style="font-size: 0.75rem; padding: 0.25rem 0.75rem;">View Details</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function updateSensorsList() {
            const sensorsList = document.getElementById('sensors-list');
            if (!sensorsList) return;
            
            sensorsList.innerHTML = sensorData.map(sensor => {
                const statusClass = `badge-${sensor.status === 'error' ? 'error' : sensor.status === 'warning' ? 'warning' : 'success'}`;
                
                return `
                    <div class="sensor-item">
                        <div class="sensor-header">
                            <span style="font-weight: 500;">${sensor.location}</span>
                            <span class="badge ${statusClass}">${sensor.status}</span>
                        </div>
                        <div class="sensor-metrics">
                            <div class="sensor-metric">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="11,5 6,9 2,9 2,15 6,15 11,19 11,5"/>
                                </svg>
                                <div style="font-weight: 500;">${sensor.noiseLevel}dB</div>
                                <div style="color: var(--text-light); font-size: 0.75rem;">Noise</div>
                            </div>
                            <div class="sensor-metric">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                                    <circle cx="9" cy="7" r="4"/>
                                    <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                </svg>
                                <div style="font-weight: 500;">${sensor.crowdDensity}%</div>
                                <div style="color: var(--text-light); font-size: 0.75rem;">Crowd</div>
                            </div>
                            <div class="sensor-metric">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18.7 9H5.3L3.5 11.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/>
                                    <circle cx="7" cy="17" r="2"/>
                                    <path d="M9 17h6"/>
                                    <circle cx="17" cy="17" r="2"/>
                                </svg>
                                <div style="font-weight: 500;">${sensor.trafficFlow}%</div>
                                <div style="color: var(--text-light); font-size: 0.75rem;">Traffic</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Chat functions
        function updateChatInterface() {
            renderChatMessages();
        }

        function renderChatMessages() {
            const chatMessagesContainer = document.getElementById('chat-messages');
            if (!chatMessagesContainer) return;
            
            // Keep existing messages, just update if needed
            const existingMessages = chatMessagesContainer.querySelectorAll('.message');
            if (existingMessages.length !== chatMessages.length) {
                chatMessagesContainer.innerHTML = chatMessages.map(message => {
                    if (message.type === 'assistant') {
                        return `
                            <div class="message assistant">
                                <div class="message-avatar">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M12 8V4H8"/>
                                        <rect width="16" height="12" x="4" y="8" rx="2"/>
                                        <path d="M2 14h2"/>
                                        <path d="M20 14h2"/>
                                        <path d="M15 13v2"/>
                                        <path d="M9 13v2"/>
                                    </svg>
                                </div>
                                <div class="message-content">
                                    <div class="message-bubble">
                                        <p>${message.content}</p>
                                    </div>
                                    ${message.data ? renderMessageData(message.data) : ''}
                                    <div class="message-time">${formatTime(message.timestamp)}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        return `
                            <div class="message user">
                                <div class="message-avatar">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                        <circle cx="12" cy="7" r="4"/>
                                    </svg>
                                </div>
                                <div class="message-content">
                                    <div class="message-bubble">
                                        <p>${message.content}</p>
                                    </div>
                                    <div class="message-time">${formatTime(message.timestamp)}</div>
                                </div>
                            </div>
                        `;
                    }
                }).join('');
                
                scrollChatToBottom();
            }
        }

        function renderMessageData(data) {
            if (!data) return '';
            
            let html = '<div style="background: #f8fafc; border-radius: 6px; padding: 1rem; margin-top: 0.5rem; font-size: 0.875rem;">';
            
            if (data.locations) {
                html += `
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.75rem; color: var(--text-light); margin-bottom: 0.5rem; font-weight: 500;">Key Locations:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                            ${data.locations.map(location => `
                                <span style="display: flex; align-items: center; gap: 0.25rem; background: white; border: 1px solid var(--border); border-radius: 4px; padding: 0.125rem 0.5rem; font-size: 0.75rem;">
                                    📍 ${location}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (data.metrics) {
                html += `
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.75rem; color: var(--text-light); margin-bottom: 0.5rem; font-weight: 500;">Key Metrics:</div>
                        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                            ${data.metrics.map(metric => `
                                <div style="display: flex; align-items: center; justify-content: space-between;">
                                    <span>${metric.label}:</span>
                                    <div style="display: flex; align-items: center; gap: 0.25rem;">
                                        <span style="font-weight: 500;">${metric.value}</span>
                                        <span style="color: ${metric.trend === 'up' ? 'var(--success)' : 'var(--error)'};">
                                            ${metric.trend === 'up' ? '↗️' : '↘️'}
                                        </span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (data.recommendations) {
                html += `
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-light); margin-bottom: 0.5rem; font-weight: 500;">Recommendations:</div>
                        <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                            ${data.recommendations.map(rec => `
                                <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                                    <span style="color: var(--success); margin-top: 0.125rem;">✓</span>
                                    <span>${rec}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            return html;
        }

        function sendChatMessage() {
            const input = document.getElementById('chat-input-field');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            chatMessages.push({
                id: Date.now().toString(),
                type: 'user',
                content: message,
                timestamp: new Date()
            });
            
            input.value = '';
            renderChatMessages();
            
            // Generate AI response
            setTimeout(() => {
                const response = generateAIResponse(message);
                chatMessages.push(response);
                renderChatMessages();
            }, 1500);
        }

        function askQuestion(question) {
            document.getElementById('chat-input-field').value = question;
            sendChatMessage();
        }

        function generateAIResponse(query) {
            const lowerQuery = query.toLowerCase();
            
            if (lowerQuery.includes('traffic')) {
                return {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: 'Based on current traffic data analysis, here\'s what I found:',
                    timestamp: new Date(),
                    data: {
                        locations: ['5th Avenue', 'Broadway', 'FDR Drive', 'West Side Highway'],
                        metrics: [
                            { label: 'Average Speed', value: '23 mph', trend: 'down' },
                            { label: 'Congestion Level', value: '68%', trend: 'up' },
                            { label: 'Incidents', value: '3 active', trend: 'down' }
                        ],
                        recommendations: [
                            'Increase traffic light timing on 5th Avenue',
                            'Deploy additional traffic officers to Broadway',
                            'Consider alternative route suggestions via mobile apps'
                        ]
                    }
                };
            }
            
            if (lowerQuery.includes('air quality')) {
                return {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: 'Air quality analysis for the past week shows the following trends:',
                    timestamp: new Date(),
                    data: {
                        locations: ['Downtown', 'Central Park', 'Financial District', 'Brooklyn Bridge'],
                        metrics: [
                            { label: 'PM2.5 Average', value: '28 μg/m³', trend: 'down' },
                            { label: 'AQI Score', value: 'Good (45)', trend: 'up' },
                            { label: 'Pollution Sources', value: 'Traffic 65%', trend: 'down' }
                        ],
                        recommendations: [
                            'Continue monitoring industrial areas',
                            'Promote electric vehicle adoption',
                            'Increase green spaces in high-traffic zones'
                        ]
                    }
                };
            }
            
            if (lowerQuery.includes('transport') || lowerQuery.includes('transit')) {
                return {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: 'Public transportation analysis reveals these insights:',
                    timestamp: new Date(),
                    data: {
                        locations: ['Outer Queens', 'South Brooklyn', 'Bronx Corridors', 'Staten Island'],
                        metrics: [
                            { label: 'Coverage Gap', value: '12 areas', trend: 'down' },
                            { label: 'Average Wait Time', value: '8.2 min', trend: 'up' },
                            { label: 'Ridership', value: '2.4M daily', trend: 'up' }
                        ],
                        recommendations: [
                            'Extend subway lines to underserved areas',
                            'Increase bus frequency during peak hours',
                            'Implement bus rapid transit (BRT) corridors'
                        ]
                    }
                };
            }
            
            return {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: 'I can help you analyze various aspects of urban planning including traffic patterns, air quality, public transportation, pedestrian flows, and infrastructure planning. Could you please specify what area you\'d like me to focus on?',
                timestamp: new Date()
            };
        }

        function scrollChatToBottom() {
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                setTimeout(() => {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }, 100);
            }
        }

        // Real-time updates
        function startRealTimeUpdates() {
            setInterval(() => {
                updateCityMetrics();
                if (currentDashboardTab === 'overview') {
                    updateMetricsGrid();
                }
            }, 5000);
            
            setInterval(() => {
                updateSafetyData();
                if (currentDashboardTab === 'safety') {
                    updateSafetyPanel();
                }
            }, 3000);
        }

        function updateCityMetrics() {
            Object.keys(cityMetrics).forEach(key => {
                const metric = cityMetrics[key];
                metric.change = (Math.random() - 0.5) * 10;
                
                if (key === 'traffic') {
                    const newValue = Math.floor(Math.random() * 30 + 50);
                    metric.value = `${newValue}%`;
                    metric.progress = newValue;
                    metric.status = newValue > 80 ? 'critical' : newValue > 65 ? 'warning' : 'normal';
                }
                
                if (key === 'incidents') {
                    const newValue = Math.floor(Math.random() * 20 + 15);
                    metric.value = `${newValue}`;
                    metric.progress = Math.min(newValue * 5, 100);
                    metric.status = newValue > 30 ? 'critical' : newValue > 20 ? 'warning' : 'normal';
                }
            });
        }

        function updateSafetyData() {
            sensorData.forEach(sensor => {
                sensor.noiseLevel = Math.max(40, Math.min(100, sensor.noiseLevel + (Math.random() - 0.5) * 10));
                sensor.crowdDensity = Math.max(0, Math.min(200, sensor.crowdDensity + (Math.random() - 0.5) * 20));
                sensor.trafficFlow = Math.max(0, Math.min(100, sensor.trafficFlow + (Math.random() - 0.5) * 15));
                sensor.status = Math.random() > 0.8 ? 'warning' : (Math.random() > 0.95 ? 'error' : 'normal');
            });
        }

        // Utility functions
        function formatTime(date) {
            return new Intl.DateTimeFormat('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        }
                // Smart City Projects JavaScript - Scoped
        (function() {
            // Project data
            const scpProjectData = {
                'public-safety': {
                    iconClass: 'scp-public-safety',
                    icon: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                    </svg>`,
                    title: 'Project 1: Public Safety & Anomaly Detection',
                    description: 'AI-powered real-time monitoring system that analyzes urban data streams to detect security threats, emergency situations, and unusual patterns for immediate response coordination',
                    image: 'https://images.unsplash.com/photo-1724883782580-91360d20cc50?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjaXR5JTIwc3VydmVpbGxhbmNlJTIwc2VjdXJpdHl8ZW58MXx8fHwxNzU5NDI1NDU0fDA&ixlib=rb-4.1.0&q=80&w=1080',
                    goals: [
                        'Deploy AI-powered threat detection across urban areas',
                        'Achieve sub-minute response time for critical incidents',
                        'Integrate 15+ data sources for comprehensive monitoring',
                        'Reduce false alarms by 85% through smart filtering'
                    ]
                },
                'urban-planning': {
                    iconClass: 'scp-urban-planning',
                    icon: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>`,
                    title: 'Project 2: Smart Urban Planning Assistant',
                    description: 'Intelligent planning platform that integrates real-time city data, traffic patterns, demographics, and environmental factors to optimize urban development and resource allocation',
                    image: 'https://images.unsplash.com/photo-1634452639706-fad607966e14?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx1cmJhbiUyMHBsYW5uaW5nJTIwY2l0eXxlbnwxfHx8fDE3NTk0MDY2MjF8MA&ixlib=rb-4.1.0&q=80&w=1080',
                    goals: [
                        'Create unified digital twin of entire metropolitan area',
                        'Enable real-time infrastructure optimization decisions',
                        'Reduce urban congestion by 30% through smart routing',
                        'Improve citizen satisfaction scores by 45%'
                    ]
                }
            };

            let scpCurrentTab = 'public-safety';

            // Function to render project content
            function scpRenderProject(tabName) {
                const project = scpProjectData[tabName];
                const goalsHTML = project.goals.map((goal, index) => `
                    <li class="scp-goal-item">
                        <span class="scp-goal-bullet"></span>
                        <span class="scp-goal-text">${goal}</span>
                    </li>
                `).join('');

                return `
                    <div class="scp-project-grid">
                        <div class="scp-project-content">
                            <div class="scp-project-icon ${project.iconClass}">
                                ${project.icon}
                            </div>
                            <h2 class="scp-project-title">${project.title}</h2>
                            <div class="scp-project-badge">Project Concept</div>
                            <p class="scp-project-description">${project.description}</p>
                            <div class="scp-goals-section">
                                <div class="scp-goals-header">
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                    </svg>
                                    <h3>Goals</h3>
                                </div>
                                <ul class="scp-goals-list">
                                    ${goalsHTML}
                                </ul>
                            </div>
                        </div>
                        <div class="scp-project-image">
                            <img src="${project.image}" alt="${project.title}">
                        </div>
                    </div>
                `;
            }

            // Function to switch tabs
            function scpSwitchTab(tabName) {
                if (tabName === scpCurrentTab) return;

                const projectCard = document.getElementById('scpProjectCard');
                const buttons = document.querySelectorAll('.scp-tab-button');

                // Update button states
                buttons.forEach(btn => {
                    btn.classList.remove('scp-active', 'scp-public-safety', 'scp-urban-planning');
                    const btnTab = btn.getAttribute('data-scp-tab');
                    btn.classList.add('scp-' + btnTab);
                    if (btnTab === tabName) {
                        btn.classList.add('scp-active', 'scp-' + tabName);
                    }
                });

                // Fade out current content
                projectCard.classList.add('scp-fade-out');

                // Wait for fade out, then update content
                setTimeout(() => {
                    scpCurrentTab = tabName;
                    projectCard.innerHTML = scpRenderProject(tabName);
                    projectCard.classList.remove('scp-fade-out');
                    projectCard.classList.add('scp-content-enter');
                    
                    // Remove animation class after it completes
                    setTimeout(() => {
                        projectCard.classList.remove('scp-content-enter');
                    }, 600);
                }, 300);
            }

            // Add event listeners to tab buttons
            document.querySelectorAll('.scp-tab-button').forEach(button => {
                button.addEventListener('click', () => {
                    const tabName = button.getAttribute('data-scp-tab');
                    scpSwitchTab(tabName);
                });
            });

            // Initial render
            document.getElementById('scpProjectCard').innerHTML = scpRenderProject('public-safety');
        })();

        class TechnicalArchitectureAnimations {
    constructor() {
        this.observers = [];
        this.animationDelays = new Map();
        this.init();
    }

    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupAnimations();
            });
        } else {
            this.setupAnimations();
        }
    }

    setupAnimations() {
        this.createObservers();
        this.setupHoverEffects();
    }

    createObservers() {
        // Hero section observer
        this.createHeroObserver();
        
        // Pipeline section observer
        this.createPipelineObserver();
        
        // Columns section observer
        this.createColumnsObserver();
        
        // Demo section observer
        this.createDemoObserver();
    }

    createHeroObserver() {
        const heroElement = document.getElementById('tech-arch-hero');
        if (!heroElement) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('tech-arch-visible');
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -10% 0px'
        });

        observer.observe(heroElement);
        this.observers.push(observer);
    }

    createPipelineObserver() {
        // Pipeline title observer
        const titleElement = document.getElementById('tech-arch-pipeline-title');
        if (titleElement) {
            const titleObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('tech-arch-visible');
                    }
                });
            }, { threshold: 0.3 });

            titleObserver.observe(titleElement);
            this.observers.push(titleObserver);
        }

        // Pipeline steps observer
        const stepElements = document.querySelectorAll('.tech-arch-pipeline-step');
        
        const stepsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const step = entry.target;
                    const stepNumber = parseInt(step.dataset.step);
                    const delay = parseFloat(step.dataset.delay) * 1000;

                    setTimeout(() => {
                        this.animatePipelineStep(step, stepNumber);
                    }, delay);
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -10% 0px'
        });

        stepElements.forEach(step => {
            stepsObserver.observe(step);
        });

        this.observers.push(stepsObserver);
    }

    animatePipelineStep(step, stepNumber) {
        // Animate the step container
        step.classList.add('tech-arch-visible');

        // Animate connecting line and arrow (if not last step)
        if (stepNumber < 4) {
            setTimeout(() => {
                const line = step.querySelector('.tech-arch-connecting-line');
                const arrow = step.querySelector('.tech-arch-arrow');
                
                if (line) line.classList.add('tech-arch-line-visible');
                
                setTimeout(() => {
                    if (arrow) arrow.classList.add('tech-arch-arrow-visible');
                }, 300);
            }, 300);
        }

        // Animate step elements in sequence
        setTimeout(() => {
            const badge = step.querySelector('.tech-arch-step-badge');
            if (badge) badge.classList.add('tech-arch-badge-visible');
        }, 200);

        setTimeout(() => {
            const icon = step.querySelector('.tech-arch-step-icon');
            if (icon) icon.classList.add('tech-arch-icon-visible');
        }, 400);

        setTimeout(() => {
            const content = step.querySelector('.tech-arch-step-content');
            if (content) content.classList.add('tech-arch-content-visible');
        }, 600);
    }

    createColumnsObserver() {
        const columnElements = document.querySelectorAll('.tech-arch-column');
        
        const columnsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const column = entry.target;
                    const columnIndex = Array.from(columnElements).indexOf(column);
                    
                    setTimeout(() => {
                        column.classList.add('tech-arch-visible');
                        this.animateFeatureCards(column);
                    }, columnIndex * 200);
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -10% 0px'
        });

        columnElements.forEach(column => {
            columnsObserver.observe(column);
        });

        this.observers.push(columnsObserver);
    }

    animateFeatureCards(column) {
        const featureCards = column.querySelectorAll('.tech-arch-feature-card');
        
        featureCards.forEach((card, index) => {
            const delay = parseFloat(card.dataset.delay) * 1000;
            
            setTimeout(() => {
                card.classList.add('tech-arch-visible');
            }, delay);
        });
    }

    createDemoObserver() {
        const demoContent = document.getElementById('tech-arch-demo');
        const demoImage = document.getElementById('tech-arch-demo-image');
        
        const demoObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    if (entry.target === demoContent) {
                        entry.target.classList.add('tech-arch-visible');
                    } else if (entry.target === demoImage) {
                        setTimeout(() => {
                            entry.target.classList.add('tech-arch-visible');
                        }, 300);
                    }
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -10% 0px'
        });

        if (demoContent) demoObserver.observe(demoContent);
        if (demoImage) demoObserver.observe(demoImage);
        
        this.observers.push(demoObserver);
    }

    setupHoverEffects() {
        // Pipeline step hover effects
        const pipelineSteps = document.querySelectorAll('.tech-arch-pipeline-step');
        pipelineSteps.forEach(step => {
            step.addEventListener('mouseenter', () => {
                const badge = step.querySelector('.tech-arch-step-badge');
                const icon = step.querySelector('.tech-arch-step-icon');
                
                if (badge && badge.classList.contains('tech-arch-badge-visible')) {
                    badge.style.transform = 'scale(1.1)';
                }
                
                if (icon && icon.classList.contains('tech-arch-icon-visible')) {
                    icon.style.color = '#374151';
                }
            });

            step.addEventListener('mouseleave', () => {
                const badge = step.querySelector('.tech-arch-step-badge');
                const icon = step.querySelector('.tech-arch-step-icon');
                
                if (badge) {
                    badge.style.transform = 'scale(1)';
                }
                
                if (icon) {
                    icon.style.color = '#6b7280';
                }
            });
        });

        // Feature card hover effects
        const featureCards = document.querySelectorAll('.tech-arch-feature-card');
        featureCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                const icon = card.querySelector('.tech-arch-feature-icon');
                const title = card.querySelector('.tech-arch-feature-title');
                
                if (icon) {
                    icon.style.transform = 'scale(1.1)';
                }
                
                if (title) {
                    title.style.color = '#111827';
                }
                
                card.style.backgroundColor = '#f9fafb';
            });

            card.addEventListener('mouseleave', () => {
                const icon = card.querySelector('.tech-arch-feature-icon');
                const title = card.querySelector('.tech-arch-feature-title');
                
                if (icon) {
                    icon.style.transform = 'scale(1)';
                }
                
                if (title) {
                    title.style.color = '#374151';
                }
                
                card.style.backgroundColor = 'white';
            });
        });
    }

    // Method to manually trigger animations (useful for testing)
    triggerAnimation(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('tech-arch-visible');
        }
    }

    // Method to reset animations
    resetAnimations() {
        const animatedElements = document.querySelectorAll('.tech-arch-visible, .tech-arch-badge-visible, .tech-arch-icon-visible, .tech-arch-content-visible, .tech-arch-line-visible, .tech-arch-arrow-visible');
        
        animatedElements.forEach(element => {
            element.classList.remove('tech-arch-visible', 'tech-arch-badge-visible', 'tech-arch-icon-visible', 'tech-arch-content-visible', 'tech-arch-line-visible', 'tech-arch-arrow-visible');
        });
    }

    // Cleanup method
    destroy() {
        this.observers.forEach(observer => {
            observer.disconnect();
        });
        this.observers = [];
    }
}

// Auto-initialize when script loads
const techArchAnimations = new TechnicalArchitectureAnimations();

// Expose to global scope for manual control if needed
window.TechnicalArchitectureAnimations = TechnicalArchitectureAnimations;
window.techArchAnimations = techArchAnimations;

// Handle page visibility changes to restart animations if needed
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Page became visible again, ensure animations work
        setTimeout(() => {
            techArchAnimations.setupAnimations();
        }, 100);
    }
});

// Handle window resize to ensure proper animation triggers
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Recreate observers after resize to handle layout changes
        techArchAnimations.destroy();
        techArchAnimations.setupAnimations();
    }, 250);
});
