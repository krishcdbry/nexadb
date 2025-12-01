        function initTheme() {
            const savedTheme = localStorage.getItem('nexadb-theme') || 'dark';
            setTheme(savedTheme);
        }

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('nexadb-theme', theme);
            const themeIcon = document.getElementById('themeIcon');
            if (themeIcon) {
                themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }

            // Update logo based on theme
            const logoImage = document.getElementById('logoImage');
            if (logoImage) {
                // Dark theme uses light logo (white/light colored)
                // Light theme uses dark logo (dark colored)
                logoImage.src = theme === 'dark'
                    ? 'https://nexadb.io/logo-light.svg'
                    : 'https://nexadb.io/logo-dark.svg';
            }
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        }

        // Sidebar Toggle
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');

            // Persist state
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('nexadb-sidebar-collapsed', isCollapsed);
        }

        // Check authentication on page load
        auth.requireAuth();

        // State
        const state = {
            connected: false,
            currentView: 'dashboard',
            currentCollection: null,
            collections: [],
            baseUrl: window.location.origin,  // Use same origin as admin panel (port 9999)
            currentPage: 1,
            currentUser: auth.getCurrentUser(),
            pageSize: 50,
            totalDocuments: 0,
            currentFilter: {},
            currentSort: {},
            visibleColumns: ['_id', '_created_at', '_updated_at'],
            queryHistory: [],
            operationsData: [],
            connectedAt: null,
            operationsCount: 0,
            viewMode: 'json', // 'json' or 'table'
            resultFormat: 'json', // 'json' or 'toon' for query editor results
            currentResultData: null, // Store query results for format switching
            operationsTimeline: {
                '1h': [],
                '6h': [],
                '24h': [],
                '7d': []
            },
            collectionToDelete: null,
            documentToDelete: null,
            // NEW v3.0.0: Database management
            currentDatabase: null, // v3.0.1: Changed from 'default' to null to force database selection on first load
            databases: [],
            databaseToDelete: null,
            // NEW v3.0.0: User permissions management
            currentPermissionsUser: null,
            currentPermissionsData: {},
            // Vector search view mode and results
            searchViewMode: 'tree', // 'tree', 'compact', or 'toon'
            currentSearchResults: null
        };

        // ============================================================================
        // DATABASE TREE NAVIGATOR (v3.0.0 Enterprise - Hierarchical View)
        // ============================================================================

        // v3.0.0: Load databases into header dropdown
        async function loadDatabaseSelector() {
            try {
                const response = await fetch('/api/databases');
                const data = await response.json();

                if (data.error) {
                    console.error('Error loading databases:', data.error);
                    return;
                }

                const databases = data.databases || [];
                const selector = document.getElementById('databaseSelector');

                if (!selector) return;

                // Build options
                selector.innerHTML = databases.map(db =>
                    `<option value="${db}" ${db === state.currentDatabase ? 'selected' : ''}>${db}</option>`
                ).join('');

            } catch (error) {
                console.error('Error loading databases:', error);
            }
        }

        function toggleDatabaseNode(databaseName) {
            const chevron = document.querySelector(`[data-database="${databaseName}"] .tree-chevron`);
            const collections = document.getElementById(`tree-${databaseName}`);

            if (chevron && collections) {
                chevron.classList.toggle('expanded');
                collections.classList.toggle('expanded');
            }

            // Switch database if clicking on a different one
            if (databaseName !== state.currentDatabase) {
                const selector = document.getElementById('databaseSelector');
                if (selector) {
                    selector.value = databaseName;
                    switchDatabase();
                }
            }
        }

        function selectCollectionFromTree(databaseName, collectionName) {
            // Switch database if needed
            if (databaseName !== state.currentDatabase) {
                const selector = document.getElementById('databaseSelector');
                if (selector) {
                    selector.value = databaseName;
                    state.currentDatabase = databaseName;
                }
            }

            // Select the collection and switch to collections view
            selectCollection(collectionName);
            switchView('collections');
        }

        // ============================================================================
        // ENHANCED DASHBOARD FUNCTIONS (v3.0.0 Enterprise)
        // ============================================================================

        function updateCollectionsOverviewTable(collectionStats) {
            const container = document.getElementById('collectionsOverviewTable');
            if (!container) return;

            if (collectionStats.length === 0) {
                const canAdmin = state.currentUser.role === 'admin';

                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📦</div>
                        <h3>No collections in this database</h3>
                        <p>${canAdmin ? 'Create your first collection to start managing data' : 'No collections available'}</p>
                        ${canAdmin ? `
                        <button class="btn btn-primary" onclick="showCreateCollectionModal()">
                            <span>+</span>
                            <span>Create Collection</span>
                        </button>
                        ` : ''}
                    </div>
                `;
                return;
            }

            let html = `
                <table class="data-table" style="width: 100%;">
                    <thead>
                        <tr>
                            <th style="text-align: left;">Collection Name</th>
                            <th style="text-align: right;">Documents</th>
                            <th style="text-align: right;">Estimated Size</th>
                            <th style="text-align: right;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            collectionStats.forEach(coll => {
                const sizeKB = (coll.documents * 0.5).toFixed(2); // Rough estimate
                html += `
                    <tr style="cursor: pointer;" onclick="viewCollectionFromDashboard('${coll.name}')">
                        <td style="font-weight: 600;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--primary);">
                                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                                </svg>
                                <span>${coll.name}</span>
                            </div>
                        </td>
                        <td style="text-align: right; font-family: 'Monaco', monospace;">${coll.documents.toLocaleString()}</td>
                        <td style="text-align: right; color: var(--text-tertiary); font-size: 13px;">${sizeKB} KB</td>
                        <td style="text-align: right;">
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); viewCollectionFromDashboard('${coll.name}')" title="View collection">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                    <circle cx="12" cy="12" r="3"/>
                                </svg>
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        function viewCollectionFromDashboard(collectionName) {
            selectCollection(collectionName);
            switchView('collections');
        }

        // View Switching (v3.0.0 Enterprise - Updated for Tree View)
        function switchView(viewName) {
            state.currentView = viewName;

            // v3.0.1: Update horizontal nav items
            document.querySelectorAll('.horizontal-nav-item').forEach(item => {
                item.classList.remove('active');
            });

            const horizontalNavItems = document.querySelectorAll('.horizontal-nav-item');
            horizontalNavItems.forEach(item => {
                const span = item.querySelector('span');
                if (span) {
                    const text = span.textContent.trim().toLowerCase();
                    const viewMap = {
                        'dashboard': 'dashboard',
                        'query editor': 'query',
                        'vector search': 'search',
                        'monitoring': 'monitoring',
                        'settings': 'settings'
                    };
                    if (viewMap[text] === viewName) {
                        item.classList.add('active');
                    }
                }
            });

            // Update nav items (legacy - for backwards compatibility)
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });

            // Find and activate the clicked nav item
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(item => {
                const span = item.querySelector('span');
                if (span) {
                    const text = span.textContent.trim().toLowerCase();
                    const viewMap = {
                        'dashboard': 'dashboard',
                        'collections': 'collections',
                        'query editor': 'query',
                        'vector search': 'search',
                        'monitoring': 'monitoring',
                        'settings': 'settings'
                    };
                    if (viewMap[text] === viewName) {
                        item.classList.add('active');
                    }
                }
            });

            // Hide all views
            document.querySelectorAll('.view-container').forEach(view => {
                view.classList.remove('active');
            });

            // Show selected view
            const views = {
                'dashboard': 'dashboardView',
                'collections': 'collectionsView',
                'query': 'queryView',
                'search': 'searchView',
                'monitoring': 'monitoringView',
                'users': 'usersView',
                'databases': 'databasesView',
                'settings': 'settingsView'
            };

            document.getElementById(views[viewName]).classList.add('active');

            // Update header
            const titles = {
                'dashboard': 'Dashboard',
                'collections': 'Collections',
                'query': 'Query Editor',
                'search': 'Vector Search',
                'monitoring': 'Monitoring',
                'users': 'User Management',
                'databases': 'Database Management',
                'settings': 'Settings'
            };

            const subtitles = {
                'dashboard': 'Real-time metrics and analytics',
                'collections': 'Browse and manage your data',
                'query': 'Execute queries and view results',
                'search': 'Search with vector embeddings',
                'monitoring': 'Real-time performance metrics',
                'users': 'Manage users and permissions (Admin Only)',
                'databases': 'Manage databases (Admin Only)',
                'settings': 'System configuration and management'
            };

            // v3.0.1: Content headers removed - tab names provide context

            // v3.0.1: Show/hide sidebar only on dashboard
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                if (viewName === 'dashboard') {
                    sidebar.style.display = 'flex';
                } else {
                    sidebar.style.display = 'none';
                }
            }

            // Initialize view-specific content
            if (viewName === 'dashboard') {
                loadEnhancedDashboard();
            } else if (viewName === 'query') {
                loadQueryEditor();
            } else if (viewName === 'search') {
                loadVectorSearch();
            } else if (viewName === 'monitoring') {
                loadMonitoring();
            } else if (viewName === 'users') {
                loadUsers();
            } else if (viewName === 'databases') {
                loadDatabasesList();
            } else if (viewName === 'settings') {
                // Load settings view with databases tab by default
                loadSettingsView('databases');
            } else if (viewName === 'collections') {
                // Load collections for the selected database
                loadCollections();
                // If a collection is selected, load its documents
                if (state.currentCollection) {
                    loadDocuments();
                }
            }
        }

        // Settings tab switching (v3.0.0 Enterprise)
        function switchSettingsTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('#settingsView .editor-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.getElementById(`settingsTab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`).classList.add('active');

            // Hide all tab contents
            document.querySelectorAll('.settings-tab-content').forEach(content => {
                content.style.display = 'none';
            });

            // Show selected tab content
            document.getElementById(`settingsContent${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`).style.display = 'block';

            // Load tab-specific content
            if (tabName === 'databases') {
                loadSettingsDatabases();
            } else if (tabName === 'users') {
                loadSettingsUsers();
            } else if (tabName === 'monitoring') {
                loadSettingsMonitoring();
            }
        }

        // Load Settings view (v3.0.0 Enterprise)
        function loadSettingsView(initialTab = 'databases') {
            switchSettingsTab(initialTab);
        }

        // Load Databases tab in Settings
        async function loadSettingsDatabases() {
            await loadDatabasesList();
            // Copy the content from databasesTableContainer to settingsDatabasesTableContainer
            const source = document.getElementById('databasesTableContainer');
            const target = document.getElementById('settingsDatabasesTableContainer');
            if (source && target) {
                target.innerHTML = source.innerHTML;
            }
        }

        // Load Users tab in Settings
        async function loadSettingsUsers() {
            await loadUsers();
            // Copy the content from usersTableContainer to settingsUsersTableContainer
            const source = document.getElementById('usersTableContainer');
            const target = document.getElementById('settingsUsersTableContainer');
            if (source && target) {
                target.innerHTML = source.innerHTML;
            }
        }

        // Load Overall Monitoring tab in Settings
        let monitoringLoading = false;
        let monitoringCache = null;
        let monitoringCacheTime = 0;

        async function loadSettingsMonitoring() {
            // Prevent multiple simultaneous loads
            if (monitoringLoading) {
                console.log('[MONITORING] Already loading, skipping...');
                return;
            }

            // Use cache if less than 30 seconds old
            const now = Date.now();
            if (monitoringCache && (now - monitoringCacheTime) < 30000) {
                console.log('[MONITORING] Using cached data');
                document.getElementById('systemTotalDatabases').textContent = monitoringCache.databases;
                document.getElementById('systemTotalCollections').textContent = monitoringCache.collections;
                document.getElementById('systemTotalUsers').textContent = monitoringCache.users;
                return;
            }

            try {
                monitoringLoading = true;
                console.log('[MONITORING] Loading system statistics...');

                // Use the new aggregated monitoring endpoint (v3.0.0)
                // This replaces 44+ API calls with a single efficient call
                const response = await fetch('/api/stats/monitoring');
                const stats = await response.json();

                // Cache the results
                monitoringCache = {
                    databases: stats.databases || 0,
                    collections: stats.collections || 0,
                    users: stats.users || 0
                };
                monitoringCacheTime = Date.now();

                // Update metrics
                document.getElementById('systemTotalDatabases').textContent = stats.databases || 0;
                document.getElementById('systemTotalCollections').textContent = stats.collections || 0;
                document.getElementById('systemTotalUsers').textContent = stats.users || 0;

                console.log('[MONITORING] Statistics loaded successfully:', stats);

            } catch (error) {
                console.error('Error loading system monitoring:', error);
            } finally {
                monitoringLoading = false;
            }
        }

        // API Helper
        async function apiCall(method, path, data = null) {
            const url = `${state.baseUrl}${path}`;
            const headers = { 'Content-Type': 'application/json' };

            // Add API key authentication
            if (state.currentUser && state.currentUser.apiKey) {
                headers['X-API-Key'] = state.currentUser.apiKey;
            }

            const options = {
                method,
                headers
            };
            if (data) options.body = JSON.stringify(data);

            const startTime = Date.now();
            const response = await fetch(url, options);

            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                showToast('error', 'Authentication Failed', 'Please log in again');
                auth.clearSession();
                setTimeout(() => {
                    window.location.href = '/admin_panel/login.html';
                }, 2000);
                throw new Error('Authentication required');
            }

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Request failed');

            // Track operation with timing
            const endTime = Date.now();
            const operation = {
                time: endTime,
                type: method,
                duration: endTime - startTime
            };

            state.operationsCount++;
            state.operationsData.push(operation);

            // Track in timeline buckets
            ['1h', '6h', '24h', '7d'].forEach(range => {
                state.operationsTimeline[range].push(operation);

                // Cleanup old data
                const cutoff = {
                    '1h': 60 * 60 * 1000,
                    '6h': 6 * 60 * 60 * 1000,
                    '24h': 24 * 60 * 60 * 1000,
                    '7d': 7 * 24 * 60 * 60 * 1000
                }[range];

                const threshold = Date.now() - cutoff;
                state.operationsTimeline[range] = state.operationsTimeline[range].filter(op => op.time > threshold);
            });

            return result;
        }

        // Auto-connect on load
        async function connect() {
            try {
                const status = await apiCall('GET', '/status');
                state.connected = true;
                state.connectedAt = Date.now();
                updateConnectionStatus(true, `Connected to ${status.server}`);
                // Load databases list - user must select database before loading collections
                await loadDatabases();
                showToast('success', 'Connected', `Connected to ${status.server} v${status.version}`);
            } catch (error) {
                state.connected = false;
                updateConnectionStatus(false, 'Connection failed');
                showToast('error', 'Connection Failed', error.message);
            }
        }

        function updateConnectionStatus(connected, message) {
            const statusEl = document.getElementById('connectionStatus');
            statusEl.className = `connection-status ${connected ? 'status-connected' : 'status-disconnected'}`;
            statusEl.innerHTML = `<span class="status-dot"></span><span>${message}</span>`;
        }

        // Dashboard Functions (v3.0.0 Enterprise - Enhanced Dashboard)
        async function loadEnhancedDashboard() {
            // Validate that a database is selected
            if (!state.currentDatabase) {
                console.log('No database selected - cannot load dashboard');
                return;
            }

            try {
                // Update current database display
                const dashboardDbEl = document.getElementById('dashboardCurrentDatabase');
                if (dashboardDbEl) {
                    dashboardDbEl.textContent = state.currentDatabase;
                }

                // Load collections for the current database
                const response = await fetch(`/api/databases/${state.currentDatabase}/collections?_t=${Date.now()}`, {
                    cache: 'no-store'
                });
                const result = await response.json();
                state.collections = result.collections || [];

                // v3.0.1: Metrics cards removed - data now shown in collections table

                // Simple collection stats without counts
                const collectionStats = state.collections.map(name => ({
                    name: name,
                    documents: '-',
                    size: 0
                }));

                // Update operations chart
                updateOperationsChart();

                // Update collections overview table
                updateCollectionsOverviewTable(collectionStats);

            } catch (error) {
                console.error('Failed to load enhanced dashboard:', error);
            }
        }

        function updateRecentCollections() {
            const container = document.getElementById('recentCollectionsList');
            const canAdmin = state.currentUser.role === 'admin';

            if (state.collections.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📦</div>
                        <h3>No collections yet</h3>
                        <p>${canAdmin ? 'Create your first collection to get started' : 'No collections available'}</p>
                        ${canAdmin ? `
                        <button class="btn btn-primary" onclick="showCreateCollectionModal()">
                            <span>+</span>
                            <span>Create Collection</span>
                        </button>
                        ` : ''}
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div style="padding: 20px;">
                    ${state.collections.map(name => `
                        <div style="padding: 16px; margin-bottom: 8px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${name}</div>
                                <div style="font-size: 13px; color: var(--text-tertiary); margin-top: 4px;">Collection</div>
                            </div>
                            <button class="btn btn-sm btn-primary" onclick="viewCollection('${name}')">View</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function viewCollection(name) {
            // Load current collections to validate
            await loadCollections();

            // Check if collection still exists
            if (!state.collections.includes(name)) {
                showToast('error', 'Collection Not Found',
                          `Collection "${name}" no longer exists`);
                loadEnhancedDashboard();  // Reload to refresh recent list
                return;
            }

            selectCollection(name);
            switchView('collections');
        }

        // Chart Functions
        let operationsChart = null;
        let monitoringChart = null;

        function updateOperationsChart() {
            const ctx = document.getElementById('operationsChart');
            if (!ctx) return;

            const range = document.getElementById('chartTimeRange')?.value || '1h';
            const operations = state.operationsTimeline[range] || [];

            const now = Date.now();
            const labels = [];
            const data = [];

            // Define bucket configuration based on range
            const config = {
                '1h': { buckets: 12, interval: 5 * 60 * 1000, format: { hour: '2-digit', minute: '2-digit' } },
                '6h': { buckets: 12, interval: 30 * 60 * 1000, format: { hour: '2-digit', minute: '2-digit' } },
                '24h': { buckets: 24, interval: 60 * 60 * 1000, format: { hour: '2-digit', minute: '2-digit' } },
                '7d': { buckets: 14, interval: 12 * 60 * 60 * 1000, format: { month: 'short', day: 'numeric', hour: '2-digit' } }
            };

            const { buckets, interval, format } = config[range];

            // Create time buckets and count operations in each
            for (let i = buckets - 1; i >= 0; i--) {
                const bucketEnd = now - (i * interval);
                const bucketStart = bucketEnd - interval;
                const time = new Date(bucketEnd);

                labels.push(time.toLocaleTimeString('en-US', format));

                // Count operations in this bucket
                const count = operations.filter(op => op.time >= bucketStart && op.time < bucketEnd).length;
                data.push(count);
            }

            if (operationsChart) {
                operationsChart.destroy();
            }

            operationsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Operations',
                        data: data,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                precision: 0
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                maxRotation: 45,
                                minRotation: 0
                            }
                        }
                    }
                }
            });
        }

        // Add updateChart function for dropdown
        function updateChart() {
            updateOperationsChart();
        }

        function updateMonitoringChart() {
            const ctx = document.getElementById('monitoringChart');
            if (!ctx) return;

            const now = Date.now();
            const labels = [];
            const readData = [];
            const writeData = [];

            // Use last 30 data points (1 minute of data at 2-second intervals)
            const recentOps = state.operationsData.slice(-30);

            for (let i = 29; i >= 0; i--) {
                const bucketEnd = now - (i * 2 * 1000);
                const bucketStart = bucketEnd - 2000;
                const time = new Date(bucketEnd);

                labels.push(time.toLocaleTimeString('en-US', { minute: '2-digit', second: '2-digit' }));

                // Count read (GET) and write (POST/PUT/DELETE) operations in this 2-second bucket
                const bucketOps = recentOps.filter(op => op.time >= bucketStart && op.time < bucketEnd);
                const reads = bucketOps.filter(op => op.type === 'GET').length;
                const writes = bucketOps.filter(op => ['POST', 'PUT', 'DELETE'].includes(op.type)).length;

                readData.push(reads);
                writeData.push(writes);
            }

            if (monitoringChart) {
                monitoringChart.destroy();
            }

            monitoringChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Read Operations',
                            data: readData,
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Write Operations',
                            data: writeData,
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: '#94a3b8'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                precision: 0
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }

        // Collections Functions
        async function loadCollections(database = state.currentDatabase) {
            // Validate that a database is selected - database is MANDATORY
            if (!database) {
                showToast('error', 'No Database Selected', 'Please select a database first');
                state.collections = [];
                renderCollections();
                return;
            }

            try {
                // Update sidebar database indicator
                const sidebarDbName = document.getElementById('sidebarDatabaseName');
                if (sidebarDbName) {
                    sidebarDbName.textContent = database;
                }

                // Use admin server API endpoint with database context
                // Add cache-busting timestamp to force fresh data
                const response = await fetch(`/api/databases/${database}/collections?_t=${Date.now()}`, {
                    cache: 'no-store'  // Force no caching
                });
                const result = await response.json();
                state.collections = result.collections || [];
                renderCollections();

                // Update query editor collection dropdown
                const select = document.getElementById('queryEditorCollection');
                if (select) {
                    select.innerHTML = '<option value="">Select collection...</option>' +
                        state.collections.map(name => `<option value="${name}">${name}</option>`).join('');
                }

                // Update search collection dropdown
                const searchSelect = document.getElementById('searchCollection');
                if (searchSelect) {
                    searchSelect.innerHTML = '<option value="">Select collection...</option>' +
                        state.collections.map(name => `<option value="${name}">${name}</option>`).join('');
                }
            } catch (error) {
                showToast('error', 'Error', 'Failed to load collections');
            }
        }

        function renderCollections() {
            const container = document.getElementById('collectionsList');
            if (state.collections.length === 0) {
                container.innerHTML = `
                    <div class="empty-collections">
                        <div class="empty-collections-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="opacity: 0.5;">
                                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M3 8h18M8 3v18" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                        </div>
                        <p>No collections yet</p>
                    </div>
                `;
                return;
            }

            const canDelete = state.currentUser.role === 'admin';

            container.innerHTML = state.collections.map(name => `
                <div class="collection-item ${name === state.currentCollection ? 'active' : ''}">
                    <div class="collection-info" onclick="selectCollection('${name}')" style="flex: 1; cursor: pointer;">
                        <span class="collection-icon">□</span>
                        <span>${name}</span>
                    </div>
                    ${canDelete ? `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button class="collection-delete-btn" onclick="event.stopPropagation(); deleteCollection('${name}')" title="Delete collection">
                            ×
                        </button>
                    </div>
                    ` : ''}
                </div>
            `).join('');

            // v3.0.1: Removed automatic count loading for performance - counts are now only loaded when needed
        }

        async function loadCollectionCount(name) {
            try {
                const database = state.currentDatabase || 'default';
                const result = await apiCall('GET', `/collections/${name}?query={}&limit=999999&database=${database}`);
                const countEl = document.getElementById(`count-${name}`);
                if (countEl) countEl.textContent = result.count;
            } catch (error) {
                console.error('Failed to load count for', name);
            }
        }

        function filterCollections() {
            const search = document.getElementById('collectionSearchInput').value.toLowerCase();
            const items = document.querySelectorAll('.collection-item');
            items.forEach(item => {
                const name = item.textContent.toLowerCase();
                item.style.display = name.includes(search) ? 'flex' : 'none';
            });
        }

        async function selectCollection(name) {
            state.currentCollection = name;
            state.selectedCollection = name; // NEW v3.0.0: Also update selectedCollection for tree
            state.currentPage = 1;
            renderCollections();

            // v3.0.1: Stay on dashboard and show collection documents in dashboard
            if (state.currentView === 'dashboard') {
                // Show collection view in dashboard
                document.getElementById('dashboardCollectionView').style.display = 'block';
                // document.getElementById('dashboardOverviewSection').style.display = 'none';
                document.getElementById('dashboardCollectionTitle').textContent = `${name} - Documents`;
                loadDocuments();
            } else {
                // Switch to collections view for other tabs
                if (state.currentView !== 'collections') {
                    switchView('collections');
                }
                loadDocuments();
            }
        }

        function closeDashboardCollection() {
            // Hide collection view and show overview
            document.getElementById('dashboardCollectionView').style.display = 'none';
            // document.getElementById('dashboardOverviewSection').style.display = 'block';
            state.currentCollection = '';
            state.currentPage = 1;
            renderCollections();
        }

        async function loadDocuments() {
            // v3.0.1: Use dashboard container if on dashboard view, otherwise use regular container
            const isDashboardView = state.currentView === 'dashboard' && document.getElementById('dashboardCollectionView').style.display === 'block';
            const container = isDashboardView ? document.getElementById('dashboardTableContainer') : document.getElementById('tableContainer');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading documents...</p></div>';

            try {
                const skip = (state.currentPage - 1) * state.pageSize;
                const filterQuery = Object.keys(state.currentFilter).length > 0 ?
                    JSON.stringify(state.currentFilter) : '{}';

                // First, get the total count with a large limit to get the actual total
                let countUrl = `/collections/${state.currentCollection}?query=${encodeURIComponent(filterQuery)}&limit=999999`;
                if (state.currentDatabase) {
                    countUrl += `&database=${encodeURIComponent(state.currentDatabase)}`;
                }
                const countResult = await apiCall('GET', countUrl);
                state.totalDocuments = countResult.count;

                // Then, get the actual page of documents
                let url = `/collections/${state.currentCollection}?query=${encodeURIComponent(filterQuery)}&limit=${state.pageSize}&skip=${skip}`;
                if (state.currentDatabase) {
                    url += `&database=${encodeURIComponent(state.currentDatabase)}`;
                }

                if (Object.keys(state.currentSort).length > 0) {
                    url += `&sort=${encodeURIComponent(JSON.stringify(state.currentSort))}`;
                }

                const result = await apiCall('GET', url);

                if (state.viewMode === 'json') {
                    renderDocumentsJSON(result.documents, isDashboardView);
                } else {
                    renderDocumentsTable(result.documents, isDashboardView);
                }
                updatePagination(isDashboardView);
            } catch (error) {
                container.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${error.message}</p></div>`;
            }
        }

        function setViewMode(mode) {
            state.viewMode = mode;
            // Update regular view buttons
            const jsonViewBtn = document.getElementById('jsonViewBtn');
            const tableViewBtn = document.getElementById('tableViewBtn');
            if (jsonViewBtn) {
                jsonViewBtn.classList.toggle('active', mode === 'json');
            }
            if (tableViewBtn) {
                tableViewBtn.classList.toggle('active', mode === 'table');
            }

            // Update dashboard view buttons if they exist
            const dashJsonViewBtn = document.getElementById('dashJsonViewBtn');
            const dashTableViewBtn = document.getElementById('dashTableViewBtn');
            if (dashJsonViewBtn) {
                dashJsonViewBtn.classList.toggle('active', mode === 'json');
            }
            if (dashTableViewBtn) {
                dashTableViewBtn.classList.toggle('active', mode === 'table');
            }

            // Hide columns button in JSON view
            const columnsBtn = document.getElementById('columnsBtn');
            if (columnsBtn) {
                columnsBtn.style.display = mode === 'table' ? 'inline-flex' : 'none';
            }

            loadDocuments();
        }

        function renderDocumentsJSON(documents, isDashboardView = false) {
            const container = isDashboardView ? document.getElementById('dashboardTableContainer') : document.getElementById('tableContainer');

            if (documents.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">
                            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                                <rect x="4" y="3" width="16" height="18" rx="2"/>
                                <path d="M8 7h8M8 11h8M8 15h5"/>
                            </svg>
                        </div>
                        <h3>No documents found</h3>
                        <p>This collection is empty. Start by inserting your first document.</p>
                        <button class="btn btn-primary" onclick="showInsertDocumentModal()">
                            <span>+</span>
                            <span>Insert Document</span>
                        </button>
                    </div>
                `;
                return;
            }

            const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';

            // v3.0.1: Show collapsed view by default to handle large JSON documents
            container.innerHTML = `
                <div style="padding: 0px;">
                    ${documents.map((doc, index) => {
                        const docIndex = (state.currentPage - 1) * state.pageSize + index + 1;
                        const docId = `doc-${docIndex}`;

                        // Get preview info (first 3 fields excluding internal fields)
                        const previewFields = Object.entries(doc)
                            .filter(([key]) => !key.startsWith('_') || key === '_id')
                            .slice(0, 3);

                        return `
                        <div style="margin-bottom: 12px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">
                            <div style="padding: 12px 20px; background: var(--bg-secondary); display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleDocumentExpansion('${docId}')">
                                <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                                    <svg id="${docId}-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition: transform 0.2s;">
                                        <polyline points="9 18 15 12 9 6"/>
                                    </svg>
                                    <div>
                                        <div style="font-size: 14px; font-weight: 700; color: var(--text-primary);">Document ${docIndex}</div>
                                        <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 2px;">
                                            ${previewFields.map(([key, val]) => {
                                                const valStr = typeof val === 'string' ? val : JSON.stringify(val);
                                                const truncated = valStr.length > 30 ? valStr.substring(0, 30) + '...' : valStr;
                                                return `<span style="margin-right: 12px;"><strong>${key}:</strong> ${truncated}</span>`;
                                            }).join('')}
                                        </div>
                                    </div>
                                </div>
                                ${canWrite ? `
                                <div style="display: flex; gap: 8px;" onclick="event.stopPropagation()">
                                    <button class="icon-btn" onclick='editDocumentFromTable(${JSON.stringify(doc).replace(/'/g, "&apos;")})' title="Edit">✎</button>
                                    <button class="icon-btn" onclick='deleteDocument("${doc._id}")' title="Delete">×</button>
                                </div>
                                ` : ''}
                            </div>
                            <div id="${docId}-content" style="display: none; padding: 20px; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.6; color: var(--text-secondary); overflow-x: auto; border-top: 1px solid var(--border-color);">
                                ${renderJSONTree(doc, `${docId}-tree`, 0)}
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            `;

            const paginationEl = document.getElementById('pagination');
            if (paginationEl) {
                paginationEl.style.display = 'flex';
            }
        }

        // v3.0.1: Toggle document expansion (one at a time)
        function toggleDocumentExpansion(docId) {
            const content = document.getElementById(`${docId}-content`);
            const icon = document.getElementById(`${docId}-icon`);
            const isExpanded = content.style.display !== 'none';

            // Collapse all other documents first
            document.querySelectorAll('[id$="-content"]').forEach(el => {
                if (el.id !== `${docId}-content`) {
                    el.style.display = 'none';
                    const otherId = el.id.replace('-content', '');
                    const otherIcon = document.getElementById(`${otherId}-icon`);
                    if (otherIcon) {
                        otherIcon.style.transform = 'rotate(0deg)';
                    }
                }
            });

            // Toggle current document
            if (isExpanded) {
                content.style.display = 'none';
                icon.style.transform = 'rotate(0deg)';
            } else {
                content.style.display = 'block';
                icon.style.transform = 'rotate(90deg)';
            }
        }

        // v3.0.1: Render JSON as collapsible tree structure
        let nodeCounter = 0;
        function renderJSONTree(data, prefix, depth) {
            const indent = depth * 12;
            const type = Array.isArray(data) ? 'array' : typeof data;

            if (type === 'object' && data !== null) {
                const keys = Object.keys(data);
                const nodeId = `${prefix}-node-${nodeCounter++}`;
                const isEmpty = keys.length === 0;

                return `
                    <div style="margin-left: ${indent}px;">
                        <div style="display: flex; align-items: center; cursor: pointer; user-select: none;" onclick="toggleJSONNode('${nodeId}')">
                            ${!isEmpty ? `<svg id="${nodeId}-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; transition: transform 0.15s;">
                                <polyline points="9 18 15 12 9 6"/>
                            </svg>` : '<span style="width: 18px; display: inline-block;"></span>'}
                            <span style="color: var(--text-secondary);">{</span>
                            ${isEmpty ? '<span style="color: var(--text-secondary);">}</span>' : `<span style="color: var(--text-tertiary); font-style: italic; margin-left: 4px;">${keys.length} ${keys.length === 1 ? 'property' : 'properties'}</span>`}
                        </div>
                        ${!isEmpty ? `
                        <div id="${nodeId}-content" style="display: none; line-height: 1.3;">
                            ${keys.map((key, idx) => {
                                const value = data[key];
                                const isLast = idx === keys.length - 1;
                                return `
                                    <div style="margin-left: 20px; margin-top: 2px;">
                                        <span class="json-key">"${escapeHtml(key)}"</span><span style="color: var(--text-secondary);">: </span>${renderJSONValue(value, `${prefix}-${key}`, depth + 1)}${!isLast ? '<span style="color: var(--text-secondary);">,</span>' : ''}
                                    </div>
                                `;
                            }).join('')}
                            <div style="margin-left: ${indent}px; margin-top: 2px;"><span style="color: var(--text-secondary);">}</span></div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else if (type === 'array') {
                const nodeId = `${prefix}-node-${nodeCounter++}`;
                const isEmpty = data.length === 0;

                return `
                    <div style="margin-left: ${indent}px;">
                        <div style="display: flex; align-items: center; cursor: pointer; user-select: none;" onclick="toggleJSONNode('${nodeId}')">
                            ${!isEmpty ? `<svg id="${nodeId}-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; transition: transform 0.15s;">
                                <polyline points="9 18 15 12 9 6"/>
                            </svg>` : '<span style="width: 18px; display: inline-block;"></span>'}
                            <span style="color: var(--text-secondary);">[</span>
                            ${isEmpty ? '<span style="color: var(--text-secondary);">]</span>' : `<span style="color: var(--text-tertiary); font-style: italic; margin-left: 4px;">${data.length} ${data.length === 1 ? 'item' : 'items'}</span>`}
                        </div>
                        ${!isEmpty ? `
                        <div id="${nodeId}-content" style="display: none; line-height: 1.3;">
                            ${data.map((item, idx) => {
                                const isLast = idx === data.length - 1;
                                return `
                                    <div style="margin-left: 20px; margin-top: 2px;">
                                        ${renderJSONValue(item, `${prefix}-${idx}`, depth + 1)}${!isLast ? '<span style="color: var(--text-secondary);">,</span>' : ''}
                                    </div>
                                `;
                            }).join('')}
                            <div style="margin-left: ${indent}px; margin-top: 2px;"><span style="color: var(--text-secondary);">]</span></div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                return renderPrimitiveValue(data);
            }
        }

        function renderJSONValue(value, prefix, depth) {
            const type = Array.isArray(value) ? 'array' : typeof value;
            if (type === 'object' && value !== null || type === 'array') {
                return renderJSONTree(value, prefix, depth);
            } else {
                return renderPrimitiveValue(value);
            }
        }

        function renderPrimitiveValue(value) {
            if (value === null) {
                return '<span class="json-null">null</span>';
            } else if (typeof value === 'boolean') {
                return `<span class="json-boolean">${value}</span>`;
            } else if (typeof value === 'number') {
                return `<span class="json-number">${value}</span>`;
            } else if (typeof value === 'string') {
                return `<span class="json-string">"${escapeHtml(value)}"</span>`;
            } else {
                return `<span class="json-string">"${escapeHtml(String(value))}"</span>`;
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function toggleJSONNode(nodeId) {
            const content = document.getElementById(`${nodeId}-content`);
            const icon = document.getElementById(`${nodeId}-icon`);

            if (!content) return;

            const isExpanded = content.style.display !== 'none';

            if (isExpanded) {
                content.style.display = 'none';
                if (icon) icon.style.transform = 'rotate(0deg)';
            } else {
                content.style.display = 'block';
                if (icon) icon.style.transform = 'rotate(90deg)';
            }
        }

        function syntaxHighlightJSON(obj) {
            let json = JSON.stringify(obj, null, 2);
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }

        function renderDocumentsTable(documents, isDashboardView = false) {
            const container = isDashboardView ? document.getElementById('dashboardTableContainer') : document.getElementById('tableContainer');

            if (documents.length === 0) {
                const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';

                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">
                            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                                <rect x="4" y="3" width="16" height="18" rx="2"/>
                                <path d="M8 7h8M8 11h8M8 15h5"/>
                            </svg>
                        </div>
                        <h3>No documents found</h3>
                        <p>This collection is empty.${canWrite ? ' Start by inserting your first document.' : ''}</p>
                        ${canWrite ? `
                        <button class="btn btn-primary" onclick="showInsertDocumentModal()">
                            <span>+</span>
                            <span>Insert Document</span>
                        </button>
                        ` : ''}
                    </div>
                `;
                return;
            }

            // Get all unique keys from documents
            const allKeys = new Set();
            documents.forEach(doc => {
                Object.keys(doc).forEach(key => allKeys.add(key));
            });

            const keys = Array.from(allKeys).filter(key => state.visibleColumns.includes(key) || !['_id', '_created_at', '_updated_at'].includes(key));
            const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';

            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th class="checkbox-cell"><input type="checkbox" id="selectAllCheckbox" onclick="toggleSelectAll(this)"></th>
                            ${keys.map(key => `<th>${key}</th>`).join('')}
                            ${canWrite ? '<th class="actions-cell">Actions</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
                        ${documents.map(doc => `
                            <tr>
                                <td class="checkbox-cell"><input type="checkbox" class="row-checkbox" data-doc-id="${doc._id}" onchange="updateBulkDeleteButton()"></td>
                                ${keys.map(key => `<td title="${JSON.stringify(doc[key]) || ''}">${formatValue(doc[key])}</td>`).join('')}
                                ${canWrite ? `
                                <td class="actions-cell">
                                    <button class="icon-btn" onclick='editDocumentFromTable(${JSON.stringify(doc).replace(/'/g, "&apos;")})' title="Edit">✎</button>
                                    <button class="icon-btn" onclick='deleteDocument("${doc._id}")' title="Delete">×</button>
                                </td>
                                ` : ''}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            document.getElementById('pagination').style.display = 'flex';

            // Update bulk delete button visibility
            updateBulkDeleteButton();
        }

        function formatValue(value) {
            if (value === null || value === undefined) return '<span class="json-null">null</span>';
            if (typeof value === 'boolean') return `<span class="json-boolean">${value}</span>`;
            if (typeof value === 'number') return `<span class="json-number">${value}</span>`;
            if (typeof value === 'object') return `<span class="json-string">${JSON.stringify(value)}</span>`;
            if (typeof value === 'string' && value.length > 50) return `<span class="json-string">${value.substring(0, 50)}...</span>`;
            return `<span class="json-string">${value}</span>`;
        }

        function toggleSelectAll(checkbox) {
            document.querySelectorAll('.row-checkbox').forEach(cb => {
                cb.checked = checkbox.checked;
            });
            updateBulkDeleteButton();
        }

        function updateBulkDeleteButton() {
            const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
            const deleteBtn = document.getElementById('deleteSelectedBtn');
            const deleteText = document.getElementById('deleteSelectedText');
            const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';

            if (!deleteBtn || !canWrite) return;

            if (selectedCheckboxes.length > 0) {
                deleteBtn.style.display = 'inline-flex';
                deleteText.textContent = `Delete Selected (${selectedCheckboxes.length})`;
            } else {
                deleteBtn.style.display = 'none';
            }

            // Update select all checkbox state
            const allCheckboxes = document.querySelectorAll('.row-checkbox');
            const selectAllCheckbox = document.getElementById('selectAllCheckbox');
            if (selectAllCheckbox && allCheckboxes.length > 0) {
                selectAllCheckbox.checked = selectedCheckboxes.length === allCheckboxes.length;
                selectAllCheckbox.indeterminate = selectedCheckboxes.length > 0 && selectedCheckboxes.length < allCheckboxes.length;
            }
        }

        function getSelectedDocumentIds() {
            const selectedCheckboxes = document.querySelectorAll('.row-checkbox:checked');
            return Array.from(selectedCheckboxes).map(cb => cb.getAttribute('data-doc-id'));
        }

        function showBulkDeleteModal() {
            const selectedIds = getSelectedDocumentIds();

            if (selectedIds.length === 0) {
                showToast('error', 'Error', 'No documents selected');
                return;
            }

            // Update modal with count
            document.getElementById('bulkDeleteCount').textContent = selectedIds.length;
            showModal('bulkDeleteModal');

            // Add input event listener to enable/disable button
            const input = document.getElementById('bulkDeleteConfirmInput');
            const btn = document.getElementById('bulkDeleteBtn');

            input.value = '';
            input.oninput = function() {
                if (this.value === 'DELETE') {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                } else {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                }
            };

            // Focus input
            setTimeout(() => input.focus(), 100);
        }

        function clearBulkDeleteInput() {
            document.getElementById('bulkDeleteConfirmInput').value = '';
            document.getElementById('bulkDeleteBtn').disabled = true;
            document.getElementById('bulkDeleteBtn').style.opacity = '0.5';
        }

        async function confirmBulkDelete() {
            const selectedIds = getSelectedDocumentIds();

            if (selectedIds.length === 0) {
                showToast('error', 'Error', 'No documents selected');
                return;
            }

            const input = document.getElementById('bulkDeleteConfirmInput');
            if (input.value !== 'DELETE') {
                showToast('error', 'Error', 'Please type DELETE to confirm');
                return;
            }

            try {
                closeModal('bulkDeleteModal');
                clearBulkDeleteInput();

                // Show progress toast
                showToast('success', 'Deleting...', `Deleting ${selectedIds.length} documents...`);

                // Delete documents one by one
                let successCount = 0;
                let errorCount = 0;

                // v3.0.0: Include database parameter in path
                const database = state.currentDatabase || 'default';

                for (const docId of selectedIds) {
                    try {
                        await apiCall('DELETE', `/databases/${database}/collections/${state.currentCollection}/documents/${docId}`);
                        successCount++;
                    } catch (error) {
                        errorCount++;
                        console.error(`Failed to delete document ${docId}:`, error);
                    }
                }

                // Show final result
                if (errorCount === 0) {
                    showToast('success', 'Success', `Deleted ${successCount} documents`);
                } else {
                    showToast('error', 'Partial Success', `Deleted ${successCount} documents, ${errorCount} failed`);
                }

                // Reload documents and update count
                loadDocuments();
                loadCollectionCount(state.currentCollection);

                if (state.currentView === 'dashboard') {
                    loadEnhancedDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function updatePagination(isDashboardView = false) {
            const totalPages = Math.ceil(state.totalDocuments / state.pageSize) || 1;
            state.totalPages = totalPages;
            const start = state.totalDocuments > 0 ? (state.currentPage - 1) * state.pageSize + 1 : 0;
            const end = Math.min(state.currentPage * state.pageSize, state.totalDocuments);

            if (isDashboardView) {
                // Update dashboard pagination
                const dashPagination = document.getElementById('dashboardPagination');
                if (dashPagination) {
                    dashPagination.style.display = state.totalDocuments > 0 ? 'flex' : 'none';
                }

                const dashStartRecord = document.getElementById('dashStartRecord');
                const dashEndRecord = document.getElementById('dashEndRecord');
                const dashTotalRecords = document.getElementById('dashTotalRecords');

                if (dashStartRecord) dashStartRecord.textContent = start;
                if (dashEndRecord) dashEndRecord.textContent = end;
                if (dashTotalRecords) dashTotalRecords.textContent = state.totalDocuments;

                // Update dashboard button states
                const dashPrevBtn = document.getElementById('dashPrevPageBtn');
                const dashNextBtn = document.getElementById('dashNextPageBtn');
                const dashFirstBtn = document.getElementById('dashFirstPageBtn');
                const dashLastBtn = document.getElementById('dashLastPageBtn');

                if (dashPrevBtn) {
                    if (state.currentPage <= 1) {
                        dashPrevBtn.setAttribute('disabled', 'disabled');
                        dashPrevBtn.style.opacity = '0.5';
                    } else {
                        dashPrevBtn.removeAttribute('disabled');
                        dashPrevBtn.style.opacity = '1';
                    }
                }

                if (dashNextBtn) {
                    if (state.currentPage >= totalPages) {
                        dashNextBtn.setAttribute('disabled', 'disabled');
                        dashNextBtn.style.opacity = '0.5';
                    } else {
                        dashNextBtn.removeAttribute('disabled');
                        dashNextBtn.style.opacity = '1';
                    }
                }

                if (dashFirstBtn) {
                    dashFirstBtn.disabled = state.currentPage <= 1;
                    dashFirstBtn.style.opacity = state.currentPage <= 1 ? '0.5' : '1';
                }

                if (dashLastBtn) {
                    dashLastBtn.disabled = state.currentPage >= totalPages;
                    dashLastBtn.style.opacity = state.currentPage >= totalPages ? '0.5' : '1';
                }
            } else {
                // Update regular pagination
                const paginationInfo = document.getElementById('paginationInfo');
                const pageNumbers = document.getElementById('pageNumbers');

                if (paginationInfo) {
                    paginationInfo.textContent = `Showing ${start}-${end} of ${state.totalDocuments} rows`;
                }

                if (pageNumbers) {
                    pageNumbers.textContent = `Page ${state.currentPage} of ${totalPages}`;
                }

                // Update button states
                const prevBtn = document.getElementById('prevPageBtn');
                const nextBtn = document.getElementById('nextPageBtn');

                if (prevBtn) {
                    if (state.currentPage <= 1) {
                        prevBtn.setAttribute('disabled', 'disabled');
                        prevBtn.style.opacity = '0.5';
                        prevBtn.style.cursor = 'not-allowed';
                    } else {
                        prevBtn.removeAttribute('disabled');
                        prevBtn.style.opacity = '1';
                        prevBtn.style.cursor = 'pointer';
                    }
                }

                if (nextBtn) {
                    if (state.currentPage >= totalPages) {
                        nextBtn.setAttribute('disabled', 'disabled');
                        nextBtn.style.opacity = '0.5';
                        nextBtn.style.cursor = 'not-allowed';
                    } else {
                        nextBtn.removeAttribute('disabled');
                        nextBtn.style.opacity = '1';
                        nextBtn.style.cursor = 'pointer';
                    }
                }
            }
        }

        function goToPage(pageNum) {
            const totalPages = Math.ceil(state.totalDocuments / state.pageSize);
            if (pageNum >= 1 && pageNum <= totalPages) {
                state.currentPage = pageNum;
                loadDocuments();
            }
        }

        function changePageSize(newSize) {
            state.pageSize = parseInt(newSize);
            state.currentPage = 1;
            loadDocuments();
        }

        function previousPage() {
            console.log('previousPage called, currentPage:', state.currentPage);
            if (state.currentPage > 1) {
                state.currentPage--;
                console.log('Moving to page:', state.currentPage);
                loadDocuments();
            } else {
                console.log('Already on first page');
            }
        }

        function nextPage() {
            const totalPages = Math.ceil(state.totalDocuments / state.pageSize);
            console.log('nextPage called, currentPage:', state.currentPage, 'totalPages:', totalPages);
            if (state.currentPage < totalPages) {
                state.currentPage++;
                console.log('Moving to page:', state.currentPage);
                loadDocuments();
            } else {
                console.log('Already on last page');
            }
        }

        // Filter Functions
        function toggleFilters() {
            const panel = document.getElementById('filtersPanel');
            panel.classList.toggle('active');
        }

        function applyFilter() {
            const field = document.getElementById('filterField').value;
            const operator = document.getElementById('filterOperator').value;
            const value = document.getElementById('filterValue').value;

            if (!field || !value) {
                showToast('error', 'Error', 'Please select field and enter value');
                return;
            }

            if (operator === '$regex') {
                state.currentFilter[field] = { [operator]: value };
            } else if (operator === '$eq') {
                state.currentFilter[field] = value;
            } else {
                // Try to parse as number
                const numValue = !isNaN(value) ? Number(value) : value;
                state.currentFilter[field] = { [operator]: numValue };
            }

            state.currentPage = 1;
            loadDocuments();
            showToast('success', 'Filter Applied', `Filtering by ${field}`);
        }

        function clearFilters() {
            state.currentFilter = {};
            state.currentPage = 1;
            document.getElementById('filterField').value = '';
            document.getElementById('filterValue').value = '';
            loadDocuments();
            showToast('success', 'Filters Cleared', 'Showing all documents');
        }

        // Sort Functions
        function toggleSort() {
            const panel = document.getElementById('sortPanel');
            panel.classList.toggle('active');
        }

        function applySort() {
            const field = document.getElementById('sortField').value;
            const order = parseInt(document.getElementById('sortOrder').value);

            if (!field) {
                showToast('error', 'Error', 'Please select a field to sort by');
                return;
            }

            state.currentSort = { [field]: order };
            state.currentPage = 1;
            loadDocuments();
            showToast('success', 'Sort Applied', `Sorting by ${field}`);
        }

        function clearSort() {
            state.currentSort = {};
            state.currentPage = 1;
            document.getElementById('sortField').value = '';
            loadDocuments();
            showToast('success', 'Sort Cleared', 'Default sorting restored');
        }

        // Column Functions
        function toggleColumns() {
            const panel = document.getElementById('columnsPanel');
            panel.classList.toggle('active');
        }

        function toggleColumn(columnName) {
            if (state.visibleColumns.includes(columnName)) {
                state.visibleColumns = state.visibleColumns.filter(c => c !== columnName);
            } else {
                state.visibleColumns.push(columnName);
            }
            loadDocuments();
        }

        // Close columns panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('columnsPanel');
            const button = e.target.closest('button');

            if (panel && panel.classList.contains('active') &&
                !panel.contains(e.target) &&
                !(button && button.onclick && button.onclick.toString().includes('toggleColumns'))) {
                panel.classList.remove('active');
            }
        });

        // CRUD Operations
        function showCreateCollectionModal() {
            showModal('createCollectionModal');
        }

        async function createCollection() {
            const name = document.getElementById('newCollectionName').value.trim();

            // Validate collection name
            if (!name) {
                showToast('error', 'Error', 'Collection name is required');
                return;
            }

            // Check for invalid characters
            if (!/^[a-zA-Z0-9_]+$/.test(name)) {
                showToast('error', 'Error', 'Collection name can only contain letters, numbers, and underscores');
                return;
            }

            try {
                // Get current database (v3.0.0 multi-database support)
                const database = state.currentDatabase || 'default';

                // Create collection by inserting and deleting a dummy document
                const initDoc = {_init: true, _timestamp: Date.now()};
                await apiCall('POST', `/collections/${name}?database=${database}`, initDoc);

                // Verify collection was created and clean up init document
                const result = await apiCall('GET', `/collections/${name}?query={}&database=${database}`);
                if (result.documents && result.documents.length > 0) {
                    // Delete all init documents
                    for (const doc of result.documents) {
                        if (doc._init) {
                            await apiCall('DELETE', `/collections/${name}/${doc._id}?database=${database}`);
                        }
                    }
                }

                closeModal('createCollectionModal');
                showToast('success', 'Success', `Collection "${name}" created in database "${database}"`);
                document.getElementById('newCollectionName').value = '';
                loadCollections();
                selectCollection(name);

                // Reload dashboard if visible
                if (state.currentView === 'dashboard') {
                    loadEnhancedDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function deleteCollection(name) {
            // Store collection name and show modal
            state.collectionToDelete = name;
            document.getElementById('deleteCollectionName').textContent = name;
            showModal('deleteCollectionModal');

            // Add input event listener to enable/disable button
            const input = document.getElementById('deleteConfirmationInput');
            const btn = document.getElementById('deleteCollectionBtn');

            input.value = '';
            input.oninput = function() {
                if (this.value === 'DELETE') {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                } else {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                }
            };

            // Focus input
            setTimeout(() => input.focus(), 100);
        }

        function clearDeleteInput() {
            document.getElementById('deleteConfirmationInput').value = '';
            document.getElementById('deleteCollectionBtn').disabled = true;
            document.getElementById('deleteCollectionBtn').style.opacity = '0.5';
            state.collectionToDelete = null;
        }

        async function confirmDeleteCollection() {
            const name = state.collectionToDelete;
            if (!name) return;

            const input = document.getElementById('deleteConfirmationInput');
            if (input.value !== 'DELETE') {
                showToast('error', 'Error', 'Please type DELETE to confirm');
                return;
            }

            try {
                closeModal('deleteCollectionModal');
                clearDeleteInput();

                // Show loading toast
                showToast('success', 'Deleting...', `Dropping collection "${name}"...`);

                // Use the DELETE /collections/{name} endpoint to drop the entire collection
                // Include database parameter in query string
                const url = state.currentDatabase
                    ? `/collections/${name}?database=${encodeURIComponent(state.currentDatabase)}`
                    : `/collections/${name}`;
                await apiCall('DELETE', url);

                // If current collection was deleted, clear selection
                if (state.currentCollection === name) {
                    state.currentCollection = null;
                    const container = document.getElementById('tableContainer');
                    if (container) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-state-icon">
                                    <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                                        <path d="M3 9h18M9 3v18"/>
                                    </svg>
                                </div>
                                <h3>Select a collection</h3>
                                <p>Choose a collection from the sidebar to view its documents</p>
                            </div>
                        `;
                    }
                }

                showToast('success', 'Success', `Collection "${name}" deleted successfully`);

                // Reload collections list
                await loadCollections();

                // Reload dashboard if visible
                if (state.currentView === 'dashboard') {
                    loadEnhancedDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function showInsertDocumentModal() {
            if (!state.currentCollection) {
                showToast('error', 'Error', 'Select a collection first');
                return;
            }
            // Reset to regular template
            document.getElementById('documentType').value = 'regular';
            updateDocumentTemplate();
            showModal('insertDocumentModal');
        }

        function updateDocumentTemplate() {
            const type = document.getElementById('documentType').value;
            const textarea = document.getElementById('insertDocumentData');

            const templates = {
                regular: `{
  "name": "Alice",
  "age": 28,
  "email": "alice@example.com",
  "city": "New York"
}`,
                vector_4d: `{
  "title": "Example Movie",
  "year": 2024,
  "genre": "Sci-Fi",
  "plot": "Description of the movie",
  "vector": [0.5, 0.3, 0.8, 0.2]
}`,
                vector_768d: `{
  "text": "Your text content here",
  "category": "AI",
  "metadata": {
    "source": "document.pdf",
    "page": 1
  },
  "vector": [0.023, -0.012, 0.045, 0.087, -0.034, 0.019, -0.056, 0.078, 0.001, -0.023]
}`,
                custom: ''
            };

            if (templates[type] !== undefined) {
                textarea.value = templates[type];
            }

            if (type === 'vector_768d') {
                textarea.placeholder = 'Note: This shows only 10 dimensions. You need 768 dimensions for full vector search. Use create_vector_collection.py script for realistic embeddings.';
            } else {
                textarea.placeholder = 'Enter valid JSON data';
            }
        }

        async function insertDocument() {
            // Double-check collection is selected
            if (!state.currentCollection) {
                showToast('error', 'Error', 'No collection selected');
                closeModal('insertDocumentModal');
                return;
            }

            const dataStr = document.getElementById('insertDocumentData').value;

            // Validate JSON
            if (!dataStr.trim()) {
                showToast('error', 'Error', 'Document data is required');
                return;
            }

            try {
                const data = JSON.parse(dataStr);
                // v3.0.0: Include database parameter
                const database = state.currentDatabase || 'default';
                await apiCall('POST', `/collections/${state.currentCollection}?database=${encodeURIComponent(database)}`, data);
                closeModal('insertDocumentModal');
                showToast('success', 'Success', 'Document inserted');
                document.getElementById('insertDocumentData').value = '';
                loadDocuments();
                loadCollectionCount(state.currentCollection);

                if (state.currentView === 'dashboard') {
                    loadEnhancedDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function showBulkInsertModal() {
            if (!state.currentCollection) {
                showToast('error', 'Error', 'Please select a collection first');
                return;
            }
            document.getElementById('bulkInsertData').value = '';
            document.getElementById('bulkInsertProgress').style.display = 'none';
            document.getElementById('bulkInsertProgressBar').style.width = '0%';
            document.getElementById('bulkInsertBtn').disabled = false;
            document.getElementById('bulkInsertCancelBtn').disabled = false;
            showModal('bulkInsertModal');
        }

        async function executeBulkInsert() {
            if (!state.currentCollection) {
                showToast('error', 'Error', 'No collection selected');
                closeModal('bulkInsertModal');
                return;
            }

            const dataStr = document.getElementById('bulkInsertData').value;

            // Validate JSON
            if (!dataStr.trim()) {
                showToast('error', 'Error', 'Documents array is required');
                return;
            }

            let documents;
            try {
                documents = JSON.parse(dataStr);
            } catch (error) {
                showToast('error', 'Error', 'Invalid JSON: ' + error.message);
                return;
            }

            // Validate it's an array
            if (!Array.isArray(documents)) {
                showToast('error', 'Error', 'Input must be a JSON array of objects');
                return;
            }

            // Validate array is not empty
            if (documents.length === 0) {
                showToast('error', 'Error', 'Array cannot be empty');
                return;
            }

            // Validate all elements are objects
            for (let i = 0; i < documents.length; i++) {
                if (typeof documents[i] !== 'object' || documents[i] === null || Array.isArray(documents[i])) {
                    showToast('error', 'Error', `Element at index ${i} is not a valid object`);
                    return;
                }
            }

            // Show progress bar
            document.getElementById('bulkInsertProgress').style.display = 'block';
            document.getElementById('bulkInsertBtn').disabled = true;
            document.getElementById('bulkInsertCancelBtn').disabled = true;

            let successCount = 0;
            let failureCount = 0;
            const total = documents.length;

            // Insert each document
            for (let i = 0; i < documents.length; i++) {
                try {
                    // v3.0.0: Include database parameter in bulk insert
                    const database = state.currentDatabase || 'default';
                    await apiCall('POST', `/collections/${state.currentCollection}?database=${encodeURIComponent(database)}`, documents[i]);
                    successCount++;
                } catch (error) {
                    console.error(`Failed to insert document ${i}:`, error);
                    failureCount++;
                }

                // Update progress
                const progress = ((i + 1) / total) * 100;
                document.getElementById('bulkInsertProgressBar').style.width = `${progress}%`;
                document.getElementById('bulkInsertProgressText').textContent = `${i + 1} / ${total}`;
            }

            // Show result
            closeModal('bulkInsertModal');
            if (failureCount === 0) {
                showToast('success', 'Success', `Successfully inserted ${successCount} documents`);
            } else {
                showToast('warning', 'Partial Success', `Inserted ${successCount} documents, ${failureCount} failed`);
            }

            // Clear textarea
            document.getElementById('bulkInsertData').value = '';

            // Reload data
            loadDocuments();
            loadCollectionCount(state.currentCollection);

            if (state.currentView === 'dashboard') {
                loadEnhancedDashboard();
            }
        }

        function editDocumentFromTable(doc) {
            const editableDoc = { ...doc };
            delete editableDoc._id;
            delete editableDoc._created_at;
            delete editableDoc._updated_at;

            document.getElementById('editDocumentId').value = doc._id;
            document.getElementById('editDocumentData').value = JSON.stringify(editableDoc, null, 2);
            showModal('editDocumentModal');
        }

        async function updateDocument() {
            const docId = document.getElementById('editDocumentId').value;
            const updatesStr = document.getElementById('editDocumentData').value;
            try {
                const updates = JSON.parse(updatesStr);
                // v3.0.0: Include database parameter in path
                const database = state.currentDatabase || 'default';
                await apiCall('PUT', `/databases/${database}/collections/${state.currentCollection}/documents/${docId}`, updates);
                closeModal('editDocumentModal');
                showToast('success', 'Success', 'Document updated');
                loadDocuments();
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function deleteDocument(docId) {
            // Store document ID and show modal
            state.documentToDelete = docId;
            document.getElementById('deleteDocumentId').textContent = docId;
            showModal('deleteDocumentModal');

            // Add input event listener to enable/disable button
            const input = document.getElementById('deleteDocumentConfirmInput');
            const btn = document.getElementById('deleteDocumentBtn');

            input.value = '';
            input.oninput = function() {
                if (this.value === 'DELETE') {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                } else {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                }
            };

            // Focus input
            setTimeout(() => input.focus(), 100);
        }

        function clearDeleteDocumentInput() {
            document.getElementById('deleteDocumentConfirmInput').value = '';
            document.getElementById('deleteDocumentBtn').disabled = true;
            document.getElementById('deleteDocumentBtn').style.opacity = '0.5';
            state.documentToDelete = null;
        }

        async function confirmDeleteDocument() {
            const docId = state.documentToDelete;
            if (!docId) return;

            const input = document.getElementById('deleteDocumentConfirmInput');
            if (input.value !== 'DELETE') {
                showToast('error', 'Error', 'Please type DELETE to confirm');
                return;
            }

            try {
                closeModal('deleteDocumentModal');
                clearDeleteDocumentInput();

                // Show loading toast
                showToast('success', 'Deleting...', 'Deleting document...');

                // v3.0.0: Include database parameter in path
                const database = state.currentDatabase || 'default';
                await apiCall('DELETE', `/databases/${database}/collections/${state.currentCollection}/documents/${docId}`);
                showToast('success', 'Success', 'Document deleted');
                loadDocuments();
                loadCollectionCount(state.currentCollection);

                if (state.currentView === 'dashboard') {
                    loadEnhancedDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        // Query Editor Functions
        function loadQueryEditor() {
            // Update collection dropdown
            const select = document.getElementById('queryEditorCollection');
            select.innerHTML = '<option value="">Select collection...</option>' +
                state.collections.map(name => `<option value="${name}">${name}</option>`).join('');

            // Load query history
            renderQueryHistory();
        }

        function renderQueryHistory() {
            const container = document.getElementById('queryHistoryList');

            if (state.queryHistory.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: var(--text-muted);">
                        <p>No queries yet</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = state.queryHistory.map((query, index) => `
                <div class="history-item" onclick="loadHistoryQuery(${index})" title="${query.query}">
                    <div style="font-weight: 600; margin-bottom: 4px;">${query.collection}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${query.timestamp}</div>
                </div>
            `).join('');
        }

        function loadHistoryQuery(index) {
            const query = state.queryHistory[index];
            document.getElementById('queryEditorCollection').value = query.collection;
            document.getElementById('queryEditorTextarea').value = query.query;
            state.currentCollection = query.collection;
        }

        function updateEditorCollection() {
            const collection = document.getElementById('queryEditorCollection').value;
            state.currentCollection = collection;
        }

        function loadQueryTemplate() {
            const template = document.getElementById('queryTemplate').value;
            const textarea = document.getElementById('queryEditorTextarea');

            const templates = {
                'find_all': '{ }',
                'find_with_filter': `{
  "age": { "$gt": 25 },
  "status": "active"
}`,
                'aggregation': `[
  {
    "$match": {
      "age": { "$gte": 30 }
    }
  },
  {
    "$group": {
      "_id": "$city",
      "count": { "$sum": 1 },
      "avgAge": { "$avg": "$age" }
    }
  },
  {
    "$sort": { "count": -1 }
  }
]`
            };

            if (template && templates[template]) {
                textarea.value = templates[template];
                document.getElementById('queryTemplate').value = '';
            }
        }

        async function executeEditorQuery() {
            const collection = document.getElementById('queryEditorCollection').value;
            const queryStr = document.getElementById('queryEditorTextarea').value.trim();

            if (!collection) {
                showToast('error', 'Error', 'Please select a collection');
                return;
            }

            if (!queryStr) {
                showToast('error', 'Error', 'Please enter a query');
                return;
            }

            try {
                const query = JSON.parse(queryStr);
                let result;

                // v3.0.0: Include database parameter
                const database = state.currentDatabase || 'default';

                // Check if it's an aggregation pipeline (array)
                if (Array.isArray(query)) {
                    result = await apiCall('POST', `/collections/${collection}/aggregate?database=${encodeURIComponent(database)}`, { pipeline: query });
                    result.documents = result.results;
                } else {
                    result = await apiCall('GET',
                        `/collections/${collection}?query=${encodeURIComponent(JSON.stringify(query))}&limit=100&database=${encodeURIComponent(database)}`);
                }

                // Store result data for format switching
                state.currentResultData = {
                    collection,
                    documents: result.documents || result.results,
                    count: result.count
                };

                // Add to history
                state.queryHistory.unshift({
                    collection,
                    query: queryStr,
                    timestamp: new Date().toLocaleTimeString()
                });

                if (state.queryHistory.length > 10) {
                    state.queryHistory = state.queryHistory.slice(0, 10);
                }

                renderQueryHistory();

                // Display in current format
                displayQueryResults();

                showToast('success', 'Success', `Found ${result.count} results`);
            } catch (error) {
                showToast('error', 'Error', error.message);

                const resultsContainer = document.getElementById('editorResults');
                const resultsContent = document.getElementById('editorResultsContent');

                resultsContainer.style.display = 'block';
                resultsContent.textContent = `Error: ${error.message}`;
                document.getElementById('editorToonStats').style.display = 'none';
            }
        }

        function setResultFormat(format) {
            state.resultFormat = format;

            // Update button states
            document.getElementById('resultJsonBtn').classList.toggle('active', format === 'json');
            document.getElementById('resultCompactBtn').classList.toggle('active', format === 'compact');
            document.getElementById('resultToonBtn').classList.toggle('active', format === 'toon');

            // Re-display results if they exist
            if (state.currentResultData) {
                displayQueryResults();
            }
        }

        async function displayQueryResults() {
            if (!state.currentResultData) return;

            const resultsContainer = document.getElementById('editorResults');
            const resultsContent = document.getElementById('editorResultsContent');
            const statsContainer = document.getElementById('editorToonStats');

            resultsContainer.style.display = 'block';

            if (state.resultFormat === 'json') {
                // Display JSON Tree View (collapsible)
                nodeCounter = 0; // Reset node counter
                const treeHtml = state.currentResultData.documents.map((doc, index) => {
                    return `
                        <div style="margin-bottom: 8px; padding: 8px 12px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px;">
                            <div style="font-weight: 600; color: var(--primary); margin-bottom: 4px; font-size: 13px;">Document ${index + 1}</div>
                            ${renderJSONTree(doc, `result-${index}`, 0)}
                        </div>
                    `;
                }).join('');
                resultsContent.innerHTML = treeHtml;
                statsContainer.style.display = 'none';
            } else if (state.resultFormat === 'compact') {
                // Display Compact JSON (single line)
                resultsContent.textContent = JSON.stringify(state.currentResultData.documents);
                statsContainer.style.display = 'none';
            } else {
                // Display TOON - convert the current query results (not entire collection)
                try {
                    const toonData = convertJsonToToon(
                        state.currentResultData.collection,
                        state.currentResultData.documents
                    );

                    // Compare TOON size vs pretty-printed JSON (which is what users actually use)
                    const jsonPretty = JSON.stringify(state.currentResultData.documents, null, 2);
                    const jsonSize = jsonPretty.length;
                    const toonSize = toonData.length;
                    const reductionPercent = ((jsonSize - toonSize) / jsonSize * 100).toFixed(1);
                    const savingsPerMillion = (reductionPercent * 1000).toFixed(2);

                    // Display stats at the top, then TOON content
                    resultsContent.innerHTML = `
                        <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                                <div>
                                    <div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px;">JSON Size</div>
                                    <div style="font-size: 18px; font-weight: 600; color: var(--text-primary);">${jsonSize.toLocaleString()} bytes</div>
                                </div>
                                <div>
                                    <div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px;">Token Reduction</div>
                                    <div style="font-size: 18px; font-weight: 600; color: var(--success);">${reductionPercent}%</div>
                                </div>
                                <div>
                                    <div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px;">Est. Savings (1M calls)</div>
                                    <div style="font-size: 18px; font-weight: 600; color: var(--success);">$${savingsPerMillion}</div>
                                </div>
                            </div>
                        </div>
                        <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px;">
                            <div style="font-size: 13px; color: var(--text-tertiary); margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                                TOON Format - Optimized for LLMs
                            </div>
                            <pre style="margin: 0; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.8; color: var(--text-secondary); overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(toonData)}</pre>
                        </div>
                    `;
                    statsContainer.style.display = 'none'; // Hide bottom stats container
                } catch (error) {
                    resultsContent.textContent = `Error converting to TOON: ${error.message}`;
                    statsContainer.style.display = 'none';
                }
            }
        }

        function convertJsonToToon(collectionName, documents) {
            if (!documents || documents.length === 0) {
                return '[0]';
            }

            // Extract schema from all documents (union of all keys)
            const allKeys = new Set();
            documents.forEach(doc => {
                Object.keys(doc).forEach(key => allKeys.add(key));
            });
            const schema = Array.from(allKeys).sort();

            // Build TOON output
            let output = `[${documents.length}]{${schema.join(',')}}:\n`;

            documents.forEach(doc => {
                const values = schema.map(key => {
                    const value = doc[key];
                    return formatToonValue(value);
                });
                output += `  ${values.join(',')}\n`;
            });

            return output.trim();
        }

        function formatToonValue(value) {
            if (value === null || value === undefined) {
                return 'null';
            }
            if (typeof value === 'boolean') {
                return String(value);
            }
            if (typeof value === 'number') {
                return String(value);
            }
            if (typeof value === 'string') {
                // Always quote strings in TOON format
                return `"${value.replace(/"/g, '\\"')}"`;
            }
            if (Array.isArray(value)) {
                // Inline array representation
                const items = value.map(v => formatToonValue(v));
                return `[${items.join(',')}]`;
            }
            if (typeof value === 'object') {
                // Nested object as inline JSON
                const pairs = Object.entries(value).map(([k, v]) => `${k}:${formatToonValue(v)}`);
                return `{${pairs.join(',')}}`;
            }
            return String(value);
        }

        function clearEditor() {
            document.getElementById('queryEditorTextarea').value = '{ }';
            document.getElementById('editorResults').style.display = 'none';
        }

        // Export query results
        async function exportQueryResults() {
            if (!state.currentResultData || state.currentResultData.length === 0) {
                showToast('error', 'Error', 'No results to export');
                return;
            }

            try {
                let content, filename, mimeType;

                if (state.resultFormat === 'toon') {
                    // Export as TOON format
                    content = buildToonOutput(state.currentResultData);
                    filename = 'query_results.toon';
                    mimeType = 'text/plain';
                } else {
                    // Export as JSON (for both 'json' and 'compact' formats)
                    content = JSON.stringify(state.currentResultData, null, 2);
                    filename = 'query_results.json';
                    mimeType = 'application/json';
                }

                // Create download
                const blob = new Blob([content], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                showToast('success', 'Exported!', `Results exported as ${filename}`);
            } catch (error) {
                showToast('error', 'Error', `Failed to export results: ${error.message}`);
            }
        }

        // Monitoring Functions
        function loadMonitoring() {
            updateMonitoringMetrics();
            updateMonitoringChart();
            loadDatabaseStatus();
            loadVectorIndexes();

            // Update every 5 seconds
            setInterval(() => {
                if (state.currentView === 'monitoring') {
                    updateMonitoringMetrics();
                    updateMonitoringChart();
                    loadVectorIndexes();
                }
            }, 5000);
        }

        function updateMonitoringMetrics() {
            // Calculate average response time from recent operations
            const recentOps = state.operationsData.slice(-100);
            if (recentOps.length > 0) {
                const avgDuration = recentOps.reduce((sum, op) => sum + (op.duration || 0), 0) / recentOps.length;
                document.getElementById('avgResponseTime').textContent = Math.round(avgDuration) + 'ms';
            } else {
                document.getElementById('avgResponseTime').textContent = '0ms';
            }

            // Update uptime
            if (state.connectedAt) {
                const uptime = Date.now() - state.connectedAt;
                const hours = Math.floor(uptime / 3600000);
                const minutes = Math.floor((uptime % 3600000) / 60000);
                document.getElementById('uptime').textContent = `${hours}h ${minutes}m`;
            }
        }

        async function loadDatabaseStatus() {
            const container = document.getElementById('databaseStatus');

            try {
                const status = await apiCall('GET', '/status');

                container.innerHTML = `
                    <div style="display: grid; gap: 16px;">
                        <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">Database</div>
                            <div style="font-size: 20px; font-weight: 700; color: var(--text-primary);">${status.database || 'NexaDB'}</div>
                        </div>
                        <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">Version</div>
                            <div style="font-size: 20px; font-weight: 700; color: var(--text-primary);">${status.version || '1.0.0'}</div>
                        </div>
                        <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">Status</div>
                            <div style="font-size: 20px; font-weight: 700; color: var(--success);">Running</div>
                        </div>
                        <div style="padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">Collections</div>
                            <div style="font-size: 20px; font-weight: 700; color: var(--text-primary);">${state.collections.length}</div>
                        </div>
                    </div>
                `;
            } catch (error) {
                container.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${error.message}</p></div>`;
            }
        }

        async function loadVectorIndexes() {
            const container = document.getElementById('vectorIndexes');

            try {
                const response = await fetch('/api/vectors');
                const data = await response.json();

                if (data.total_vectors === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon" style="font-size: 48px;">📊</div>
                            <h3>No Vector Indexes</h3>
                            <p>Insert documents with vector fields to see vector indexes here</p>
                        </div>
                    `;
                    return;
                }

                let html = `
                    <div style="padding: 16px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="font-size: 24px;">📊</div>
                            <div>
                                <div style="font-weight: 600; margin-bottom: 4px;">Total Vectors: ${data.total_vectors}</div>
                                <div style="font-size: 13px; color: var(--text-secondary);">
                                    ${Object.keys(data.collections).length} collections with vector embeddings
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="display: grid; gap: 12px;">
                `;

                for (const [collectionName, collectionData] of Object.entries(data.collections)) {
                    const docList = collectionData.documents.slice(0, 5).map(doc =>
                        `<span style="font-size: 11px; color: var(--text-tertiary); font-family: monospace;">${doc.doc_id}</span>`
                    ).join(', ');

                    const remaining = collectionData.count - 5;

                    html += `
                        <div style="padding: 16px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                <div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">${collectionName}</div>
                                    <div style="font-size: 13px; color: var(--text-tertiary);">
                                        ${collectionData.count} vectors • ${collectionData.dimensions} dimensions
                                    </div>
                                </div>
                                <div style="background: rgba(139, 92, 246, 0.15); color: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 18px; font-weight: 700;">
                                    ${collectionData.count}
                                </div>
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                                Documents: ${docList}${remaining > 0 ? ` <span style="color: var(--text-tertiary);">+${remaining} more</span>` : ''}
                            </div>
                        </div>
                    `;
                }

                html += `</div>`;
                container.innerHTML = html;

            } catch (error) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>Error Loading Vectors</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        // TOON Export Functions
        let currentToonData = null;

        async function exportToTOON() {
            if (!state.currentCollection) {
                showToast('error', 'Error', 'Please select a collection first');
                return;
            }

            try {
                showToast('success', 'Exporting...', `Converting ${state.currentCollection} to TOON format...`);

                // Call the admin server API endpoint
                const response = await fetch(`/api/toon/export?collection=${encodeURIComponent(state.currentCollection)}`);
                const result = await response.json();

                if (!result.success) {
                    throw new Error(result.error || 'Export failed');
                }

                // Store TOON data for download
                currentToonData = result.toon_data;

                // Update modal with results
                document.getElementById('toonDocCount').textContent = result.count || 0;
                document.getElementById('toonReduction').textContent =
                    (result.token_stats?.reduction_percent || 0).toFixed(1) + '%';
                document.getElementById('toonSavings').textContent =
                    '$' + ((result.token_stats?.reduction_percent || 0) * 10).toFixed(2);
                document.getElementById('toonOutput').value = result.toon_data;

                // Show modal
                showModal('toonExportModal');
                showToast('success', 'Export Complete',
                    `Exported ${result.count} documents with ${result.token_stats?.reduction_percent?.toFixed(1)}% token reduction`);

            } catch (error) {
                showToast('error', 'Export Failed', error.message);
                console.error('TOON export error:', error);
            }
        }

        function downloadTOON() {
            if (!currentToonData) {
                showToast('error', 'Error', 'No TOON data to download');
                return;
            }

            try {
                // Create blob and download
                const blob = new Blob([currentToonData], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${state.currentCollection}.toon`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                showToast('success', 'Downloaded', `${state.currentCollection}.toon saved successfully`);
            } catch (error) {
                showToast('error', 'Download Failed', error.message);
            }
        }

        // User Management Functions (Admin Only)
        async function loadUsers() {
            const container = document.getElementById('usersTableContainer');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading users...</p></div>';

            try {
                // Call admin server endpoint for listing users
                const response = await fetch(`/api/users/list`, {
                    headers: {
                        'X-API-Key': state.currentUser.apiKey
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to load users');
                }

                const result = await response.json();
                const users = result.users || [];

                if (users.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">
                                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                    <circle cx="9" cy="7" r="4"/>
                                </svg>
                            </div>
                            <h3>No users found</h3>
                            <p>Create your first user to get started</p>
                        </div>
                    `;
                    return;
                }

                // Fetch detailed user data with database permissions
                const usersWithPerms = await Promise.all(
                    users.map(async (user) => {
                        try {
                            const userResponse = await fetch(`/api/users/${user.username}`);
                            const userData = await userResponse.json();
                            return {
                                ...user,
                                database_permissions: userData.database_permissions || {}
                            };
                        } catch (error) {
                            return {
                                ...user,
                                database_permissions: {}
                            };
                        }
                    })
                );

                container.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Role</th>
                                <th>Database Access</th>
                                <th>API Key</th>
                                <th>Created At</th>
                                <th>Last Login</th>
                                <th class="actions-cell">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${usersWithPerms.map(user => {
                                const dbPerms = user.database_permissions || {};
                                const dbCount = Object.keys(dbPerms).length;
                                const dbAccessText = dbCount > 0
                                    ? `${dbCount} database${dbCount > 1 ? 's' : ''}`
                                    : 'None';

                                return `
                                <tr>
                                    <td><span style="font-weight: 600;">${user.username}</span></td>
                                    <td>
                                        <span class="role-badge role-${user.role || 'unknown'}" style="padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; background: ${getRoleColor(user.role || 'read')}15; color: ${getRoleColor(user.role || 'read')};">
                                            ${user.role ? user.role.toUpperCase() : 'UNKNOWN'}
                                        </span>
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary" onclick='showUserDatabasePermissions("${user.username}")' title="Manage database access">
                                            ${dbAccessText}
                                        </button>
                                    </td>
                                    <td>
                                        <code style="font-size: 12px; background: var(--bg-tertiary); padding: 4px 8px; border-radius: 4px;">${user.api_key ? user.api_key.substring(0, 20) + '...' : 'N/A'}</code>
                                    </td>
                                    <td>${user.created_at ? new Date(user.created_at * 1000).toLocaleString() : 'N/A'}</td>
                                    <td>${user.last_login ? new Date(user.last_login * 1000).toLocaleString() : 'Never'}</td>
                                    <td class="actions-cell">
                                        <button class="icon-btn" onclick='editUser(${JSON.stringify(user).replace(/'/g, "&apos;")})' title="${user.username === 'root' ? 'Change Password' : 'Edit User'}">✎</button>
                                        <button class="icon-btn" onclick='deleteUser("${user.username}")' title="Delete" ${user.username === 'root' ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>×</button>
                                    </td>
                                </tr>
                            `}).join('')}
                        </tbody>
                    </table>
                `;
            } catch (error) {
                container.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${error.message}</p></div>`;
            }
        }

        function getRoleColor(role) {
            const colors = {
                'admin': '#8b5cf6',
                'write': '#6366f1',
                'read': '#10b981',
                'guest': '#94a3b8'
            };
            return colors[role] || '#94a3b8';
        }

        function showCreateUserModal() {
            showModal('createUserModal');
        }

        async function createUser() {
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newUserPassword').value;
            const role = document.getElementById('newUserRole').value;

            if (!username || !password) {
                showToast('error', 'Error', 'Username and password are required');
                return;
            }

            if (!/^[a-zA-Z0-9_]+$/.test(username)) {
                showToast('error', 'Error', 'Username can only contain letters, numbers, and underscores');
                return;
            }

            try {
                const response = await fetch(`${state.baseUrl}/users/create`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': state.currentUser.apiKey
                    },
                    body: JSON.stringify({ username, password, role })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to create user');
                }

                const result = await response.json();

                // Close create modal
                closeModal('createUserModal');

                // Show success modal with user details
                document.getElementById('createdUsername').value = username;
                document.getElementById('createdPassword').value = password;
                document.getElementById('createdRole').value = role.toUpperCase();
                document.getElementById('createdApiKey').value = result.api_key;
                showModal('userCreatedModal');

                // Clear form
                document.getElementById('newUsername').value = '';
                document.getElementById('newUserPassword').value = '';
                document.getElementById('newUserRole').value = 'read';

                loadUsers();
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        async function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.value;

            if (!text) {
                showToast('error', 'Error', 'Nothing to copy');
                return;
            }

            try {
                await navigator.clipboard.writeText(text);
                showToast('success', 'Copied!', 'Copied to clipboard');
            } catch (error) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    showToast('success', 'Copied!', 'Copied to clipboard');
                } catch (err) {
                    showToast('error', 'Error', 'Failed to copy');
                }
                document.body.removeChild(textArea);
            }
        }

        function editUser(user) {
            const isRoot = user.username === 'root';

            document.getElementById('editUsername').value = user.username;
            document.getElementById('editUserPassword').value = '';
            document.getElementById('editUserRole').value = user.role;

            // Update modal for root user
            if (isRoot) {
                document.getElementById('editUserModalTitle').textContent = 'Change Root Password';
                document.getElementById('editRoleGroup').style.display = 'none';
                document.getElementById('passwordOptionalLabel').style.display = 'none';
                document.getElementById('passwordRequiredLabel').style.display = 'inline';
                document.getElementById('updateUserBtn').textContent = 'Change Password';
            } else {
                document.getElementById('editUserModalTitle').textContent = 'Edit User';
                document.getElementById('editRoleGroup').style.display = 'block';
                document.getElementById('passwordOptionalLabel').style.display = 'inline';
                document.getElementById('passwordRequiredLabel').style.display = 'none';
                document.getElementById('updateUserBtn').textContent = 'Update User';
            }

            showModal('editUserModal');
        }

        async function updateUser() {
            const username = document.getElementById('editUsername').value;
            const password = document.getElementById('editUserPassword').value;
            const role = document.getElementById('editUserRole').value;
            const isRoot = username === 'root';

            // Validate password required for root
            if (isRoot && !password) {
                showToast('error', 'Error', 'Password is required for root user');
                return;
            }

            const updates = {};

            // For root user, only send password
            if (isRoot) {
                updates.password = password;
            } else {
                // For other users, send role and optional password
                updates.role = role;
                if (password) {
                    updates.password = password;
                }
            }

            try {
                const response = await fetch(`${state.baseUrl}/users/${username}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': state.currentUser.apiKey
                    },
                    body: JSON.stringify(updates)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to update user');
                }

                closeModal('editUserModal');

                if (isRoot) {
                    showToast('success', 'Success', 'Root password changed successfully');
                } else {
                    showToast('success', 'Success', `User "${username}" updated`);
                }

                loadUsers();
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        async function deleteUser(username) {
            if (username === 'root') {
                showToast('error', 'Error', 'Cannot delete root user');
                return;
            }

            if (!confirm(`Delete user "${username}"? This action cannot be undone.`)) {
                return;
            }

            try {
                const response = await fetch(`${state.baseUrl}/users/${username}`, {
                    method: 'DELETE',
                    headers: {
                        'X-API-Key': state.currentUser.apiKey
                    }
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to delete user');
                }

                showToast('success', 'Success', `User "${username}" deleted`);
                loadUsers();
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        // Modal helpers
        function showModal(id) {
            document.getElementById(id).classList.add('active');
        }

        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }

        // Toast notifications
        function showToast(type, title, message) {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-icon">${type === 'success' ? '✓' : '✕'}</div>
                <div class="toast-content">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                </div>
            `;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }

        // Initialize
        window.addEventListener('load', () => {
            initTheme();

            // Display user info
            if (state.currentUser) {
                document.getElementById('username').textContent = state.currentUser.username || 'Guest';
                document.getElementById('userRole').textContent = state.currentUser.role || 'guest';

                // Show Users and Settings menu items only for admins
                if (state.currentUser.role === 'admin') {
                    const usersNavItem = document.getElementById('usersNavItem');
                    if (usersNavItem) {
                        usersNavItem.style.display = 'flex';
                    }

                    const settingsNavItem = document.getElementById('settingsNavItemHorizontal');
                    if (settingsNavItem) {
                        settingsNavItem.style.display = 'flex';
                    }

                    const quickActionBtn = document.getElementById('quickActionCreateCollection');
                    if (quickActionBtn) {
                        quickActionBtn.style.display = 'flex';
                    }

                    const quickActionSettings = document.getElementById('quickActionSettings');
                    if (quickActionSettings) {
                        quickActionSettings.style.display = 'flex';
                    }
                } else {
                    // Hide Settings tab for non-admin users
                    const settingsNavItem = document.getElementById('settingsNavItemHorizontal');
                    if (settingsNavItem) {
                        settingsNavItem.style.display = 'none';
                    }

                    const quickActionBtn = document.getElementById('quickActionCreateCollection');
                    if (quickActionBtn) {
                        quickActionBtn.style.display = 'none';
                    }

                    const quickActionSettings = document.getElementById('quickActionSettings');
                    if (quickActionSettings) {
                        quickActionSettings.style.display = 'none';
                    }
                }

                // Hide write/admin buttons for read-only users
                const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';
                const canAdmin = state.currentUser.role === 'admin';

                if (!canWrite) {
                    // Hide insert/edit buttons
                    const addRecordBtn = document.getElementById('addRecordBtn');
                    if (addRecordBtn) addRecordBtn.style.display = 'none';

                    const bulkAddBtn = document.getElementById('bulkAddBtn');
                    if (bulkAddBtn) bulkAddBtn.style.display = 'none';

                    const addRecordBtnCollection = document.getElementById('addRecordBtnCollection');
                    if (addRecordBtnCollection) addRecordBtnCollection.style.display = 'none';

                    const bulkAddBtnCollection = document.getElementById('bulkAddBtnCollection');
                    if (bulkAddBtnCollection) bulkAddBtnCollection.style.display = 'none';
                } else {
                    // Show write buttons for write/admin users
                    const addRecordBtn = document.getElementById('addRecordBtn');
                    if (addRecordBtn) addRecordBtn.style.display = 'inline-flex';

                    const bulkAddBtn = document.getElementById('bulkAddBtn');
                    if (bulkAddBtn) bulkAddBtn.style.display = 'inline-flex';

                    const addRecordBtnCollection = document.getElementById('addRecordBtnCollection');
                    if (addRecordBtnCollection) addRecordBtnCollection.style.display = 'inline-flex';

                    const bulkAddBtnCollection = document.getElementById('bulkAddBtnCollection');
                    if (bulkAddBtnCollection) bulkAddBtnCollection.style.display = 'inline-flex';
                }

                if (!canAdmin) {
                    // Hide collection management buttons
                    const newCollectionBtn = document.getElementById('newCollectionBtn');
                    if (newCollectionBtn) newCollectionBtn.style.display = 'none';
                }
            }

            // Restore sidebar state
            const isCollapsed = localStorage.getItem('nexadb-sidebar-collapsed') === 'true';
            if (isCollapsed) {
                document.getElementById('sidebar').classList.add('collapsed');
            }

            // Load databases on startup (v3.0.0)
            loadDatabases();

            // Load database selector dropdown (v3.0.0)
            loadDatabaseSelector();

            setTimeout(connect, 500);
        });

        // Vector Search Functions
        function loadVectorSearch() {
            // Update collection dropdown
            const select = document.getElementById('searchCollection');
            select.innerHTML = '<option value="">Select collection...</option>' +
                state.collections.map(name => `<option value="${name}">${name}</option>`).join('');

            // Load search history
            renderSearchHistory();
        }

        function renderSearchHistory() {
            const container = document.getElementById('searchHistoryList');

            if (!state.searchHistory || state.searchHistory.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: var(--text-muted);">
                        <p>No searches yet</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = state.searchHistory.map((search, index) => `
                <div class="history-item" onclick="loadHistorySearch(${index})" title="Search in ${search.collection}">
                    <div style="font-weight: 600; margin-bottom: 4px;">${search.collection}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">k=${search.k} • ${search.timestamp}</div>
                </div>
            `).join('');
        }

        function loadHistorySearch(index) {
            const search = state.searchHistory[index];
            document.getElementById('searchCollection').value = search.collection;
            document.getElementById('searchK').value = search.k;
            document.getElementById('searchVectorInput').value = search.vector;
            state.currentCollection = search.collection;
        }

        function updateSearchCollection() {
            const collection = document.getElementById('searchCollection').value;
            state.currentCollection = collection;
        }

        async function executeVectorSearch() {
            const collection = document.getElementById('searchCollection').value;
            const vectorStr = document.getElementById('searchVectorInput').value.trim();
            const k = parseInt(document.getElementById('searchK').value) || 10;
            const dimensions = parseInt(document.getElementById('searchDimensions').value) || 768;

            if (!collection) {
                showToast('error', 'Error', 'Please select a collection');
                return;
            }

            if (!vectorStr) {
                showToast('error', 'Error', 'Please enter a query vector');
                return;
            }

            try {
                const queryVector = JSON.parse(vectorStr);

                if (!Array.isArray(queryVector)) {
                    throw new Error('Query vector must be an array of numbers');
                }

                // Call admin server API endpoint for vector search
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        collection,
                        query_vector: queryVector,
                        k,
                        dimensions,
                        database: state.currentDatabase  // v3.0.0: Include current database
                    })
                });

                const result = await response.json();

                if (!result.success) {
                    throw new Error(result.error || 'Search failed');
                }

                // Initialize search history if it doesn't exist
                if (!state.searchHistory) {
                    state.searchHistory = [];
                }

                // Add to history
                state.searchHistory.unshift({
                    collection,
                    vector: vectorStr,
                    k,
                    dimensions,
                    timestamp: new Date().toLocaleTimeString()
                });

                if (state.searchHistory.length > 10) {
                    state.searchHistory = state.searchHistory.slice(0, 10);
                }

                renderSearchHistory();

                // Display results
                displaySearchResults(result.results, result.count);

                showToast('success', 'Success', `Found ${result.count} results`);
            } catch (error) {
                showToast('error', 'Error', error.message);

                const resultsContainer = document.getElementById('searchResults');
                const resultsContent = document.getElementById('searchResultsContent');

                resultsContainer.style.display = 'block';
                resultsContent.textContent = `Error: ${error.message}`;
            }
        }

        function displaySearchResults(results, count) {
            const resultsContainer = document.getElementById('searchResults');
            const resultsContent = document.getElementById('searchResultsContent');
            const resultsCountEl = document.getElementById('searchResultsCount');

            resultsContainer.style.display = 'block';
            resultsCountEl.textContent = `${count} result${count !== 1 ? 's' : ''} found`;

            // Store results for view mode switching and export
            state.currentSearchResults = results;

            if (!results || results.length === 0) {
                resultsContent.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🔍</div>
                        <h3>No results found</h3>
                        <p>Try adjusting your query vector or increasing k</p>
                    </div>
                `;
                return;
            }

            // Render based on view mode
            if (state.searchViewMode === 'tree') {
                renderSearchResultsTree(results, resultsContent);
            } else if (state.searchViewMode === 'toon') {
                renderSearchResultsTOON(results, resultsContent);
            }
        }

        // Tree view (collapsed by default, expandable)
        function renderSearchResultsTree(results, container) {
            let html = '<div style="padding: 0px;">';

            results.forEach((result, index) => {
                const similarity = (result.similarity * 100).toFixed(2);
                const doc = result.document;
                const docId = `search-result-${index}`;

                // Get preview info
                const previewFields = Object.entries(doc)
                    .filter(([key]) => !key.startsWith('_') || key === '_id')
                    .slice(0, 3);

                html += `
                <div style="margin-bottom: 12px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">
                    <div style="padding: 12px 20px; background: var(--bg-secondary); display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleDocumentExpansion('${docId}')">
                        <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                            <svg id="${docId}-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition: transform 0.2s;">
                                <polyline points="9 18 15 12 9 6"/>
                            </svg>
                            <div>
                                <div style="font-size: 14px; font-weight: 700; color: var(--text-primary);">Result #${index + 1}</div>
                                <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 2px;">
                                    ${previewFields.map(([key, val]) => {
                                        const valStr = typeof val === 'string' ? val : JSON.stringify(val);
                                        const truncated = valStr.length > 30 ? valStr.substring(0, 30) + '...' : valStr;
                                        return `<span style="margin-right: 12px;"><strong>${key}:</strong> ${escapeHtml(truncated)}</span>`;
                                    }).join('')}
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(139, 92, 246, 0.15); color: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 700;">
                            ${similarity}% match
                        </div>
                    </div>
                    <div id="${docId}-content" style="display: none; padding: 20px; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.6; color: var(--text-secondary); overflow-x: auto; border-top: 1px solid var(--border-color);">
                        ${renderJSONTree(doc, `${docId}-tree`, 0)}
                    </div>
                </div>
                `;
            });

            html += '</div>';
            container.innerHTML = html;
        }

        // JSON Compact view
        function renderSearchResultsCompact(results, container) {
            let html = '<div style="padding: 20px;">';

            results.forEach((result, index) => {
                const similarity = (result.similarity * 100).toFixed(2);
                const doc = result.document;
                const jsonStr = JSON.stringify(doc, null, 2);

                html += `
                <div style="margin-bottom: 16px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">
                    <div style="padding: 12px 20px; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 14px; font-weight: 700; color: var(--text-secondary);">Result #${index + 1}</span>
                            ${doc._id ? `<span style="font-size: 12px; color: var(--text-tertiary); margin-left: 12px;">ID: ${escapeHtml(doc._id)}</span>` : ''}
                        </div>
                        <div style="background: rgba(139, 92, 246, 0.15); color: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 700;">
                            ${similarity}% match
                        </div>
                    </div>
                    <div style="padding: 20px; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.8; color: var(--text-secondary); overflow-x: auto;">
                        <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(jsonStr)}</pre>
                    </div>
                </div>
                `;
            });

            html += '</div>';
            container.innerHTML = html;
        }

        // TOON view
        function renderSearchResultsTOON(results, container) {
            try {
                // Extract documents from results
                const documents = results.map(r => ({
                    ...r.document,
                    _similarity: r.similarity
                }));

                // Convert to TOON format
                const toonOutput = documentsToTOON(documents);

                container.innerHTML = `
                    <div style="padding: 20px;">
                        <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px;">
                            <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                                <div style="font-size: 13px; color: var(--text-tertiary); margin-bottom: 4px;">
                                    TOON Format - Optimized for LLMs (40-50% token reduction)
                                </div>
                                <div style="font-size: 12px; color: var(--text-tertiary);">
                                    Results include similarity scores as _similarity field
                                </div>
                            </div>
                            <pre style="margin: 0; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.8; color: var(--text-secondary); overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(toonOutput)}</pre>
                        </div>
                    </div>
                `;
            } catch (error) {
                container.innerHTML = `
                    <div style="padding: 20px;">
                        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 20px; color: var(--text-secondary);">
                            Error converting to TOON: ${escapeHtml(error.message)}
                        </div>
                    </div>
                `;
            }
        }

        // Helper function to convert documents to TOON format
        function documentsToTOON(documents) {
            if (!documents || documents.length === 0) {
                return '[0]';
            }

            // Extract schema from all documents
            const allKeys = new Set();
            documents.forEach(doc => {
                Object.keys(doc).forEach(key => allKeys.add(key));
            });
            const schema = Array.from(allKeys).sort();

            // Build TOON output
            let output = `[${documents.length}]{${schema.join(',')}}:\n`;

            documents.forEach(doc => {
                const values = schema.map(key => {
                    const value = doc[key];
                    return formatToonValue(value);
                });
                output += `  ${values.join(',')}\n`;
            });

            return output.trim();
        }

        function clearSearchEditor() {
            document.getElementById('searchVectorInput').value = '[]';
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('searchK').value = '10';
        }

        // Set search view mode (tree, toon)
        function setSearchViewMode(mode) {
            state.searchViewMode = mode;

            // Update button states
            document.getElementById('searchTreeViewBtn').classList.toggle('active', mode === 'tree');
            document.getElementById('searchToonViewBtn').classList.toggle('active', mode === 'toon');

            // Re-render results with new mode
            if (state.currentSearchResults && state.currentSearchResults.length > 0) {
                const resultsContent = document.getElementById('searchResultsContent');
                if (mode === 'tree') {
                    renderSearchResultsTree(state.currentSearchResults, resultsContent);
                } else if (mode === 'toon') {
                    renderSearchResultsTOON(state.currentSearchResults, resultsContent);
                }
            }
        }

        // Export search results
        async function exportSearchResults() {
            if (!state.currentSearchResults || state.currentSearchResults.length === 0) {
                showToast('error', 'Error', 'No results to export');
                return;
            }

            try {
                let content, filename, mimeType;

                if (state.searchViewMode === 'toon') {
                    // Export as TOON format
                    const documents = state.currentSearchResults.map(r => ({
                        ...r.document,
                        _similarity: r.similarity
                    }));
                    content = documentsToTOON(documents);
                    filename = 'vector_search_results.toon';
                    mimeType = 'text/plain';
                } else {
                    // Export as JSON
                    content = JSON.stringify(state.currentSearchResults, null, 2);
                    filename = 'vector_search_results.json';
                    mimeType = 'application/json';
                }

                // Create download
                const blob = new Blob([content], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                showToast('success', 'Exported!', `Results exported as ${filename}`);
            } catch (error) {
                showToast('error', 'Error', `Failed to export results: ${error.message}`);
            }
        }

        // ============================================================================
        // DATABASE MANAGEMENT FUNCTIONS (v3.0.0)
        // ============================================================================

        // Load databases list and update selector
        // Show database selection modal (v3.0.1 - First Load UX)
        function showDatabaseSelectionModal() {
            const modal = document.getElementById('selectDatabaseModal');
            const listContainer = document.getElementById('databaseSelectionList');
            const searchInput = document.getElementById('databaseSearchInput');

            if (!modal || !listContainer) return;

            // Clear search input
            if (searchInput) {
                searchInput.value = '';
            }

            // Populate the modal with database options
            renderDatabaseList(state.databases);

            // Show the modal
            modal.style.display = 'flex';

            // Focus on search input
            if (searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        }

        // Render database list
        function renderDatabaseList(databases) {
            const listContainer = document.getElementById('databaseSelectionList');
            if (!listContainer) return;

            if (databases.length === 0) {
                listContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px; color: var(--text-tertiary);">
                        <div style="font-size: 14px; margin-bottom: 8px;">No databases found</div>
                        <div style="font-size: 12px;">Try a different search term</div>
                    </div>
                `;
                return;
            }

            listContainer.innerHTML = databases.map(db => `
                <div class="database-option" onclick="selectDatabaseFromModal('${db}')" style="
                    padding: 12px 16px;
                    background: var(--bg-secondary);
                    border: 2px solid var(--border);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                " onmouseover="this.style.borderColor='var(--primary)'; this.style.background='rgba(139, 92, 246, 0.1)';"
                   onmouseout="this.style.borderColor='var(--border)'; this.style.background='var(--bg-secondary)';">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--primary);">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                    <div style="flex: 1;">
                        <div style="font-size: 14px; font-weight: 600; color: var(--text-primary);">${db}</div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Click to select this database</div>
                    </div>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--text-tertiary);">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                </div>
            `).join('');
        }

        // Filter database list based on search input
        function filterDatabaseList() {
            const searchInput = document.getElementById('databaseSearchInput');
            if (!searchInput) return;

            const searchTerm = searchInput.value.toLowerCase().trim();

            if (!searchTerm) {
                // Show all databases if search is empty
                renderDatabaseList(state.databases);
                return;
            }

            // Filter databases based on search term
            const filteredDatabases = state.databases.filter(db =>
                db.toLowerCase().includes(searchTerm)
            );

            renderDatabaseList(filteredDatabases);
        }

        // Select database from modal (v3.0.1)
        async function selectDatabaseFromModal(dbName) {
            const modal = document.getElementById('selectDatabaseModal');

            // Set the selected database
            state.currentDatabase = dbName;

            // Save selected database to localStorage
            localStorage.setItem('nexadb_selected_database', state.currentDatabase);

            // Update the button text
            const currentDbName = document.getElementById('currentDatabaseName');
            if (currentDbName) {
                currentDbName.textContent = dbName;
            }

            // Hide the modal
            if (modal) {
                modal.style.display = 'none';
            }

            // Show toast
            showToast('success', 'Database Selected', `Now using database: ${dbName}`);

            // Clear current collection selection and view state
            state.currentCollection = null;
            state.selectedCollection = null;
            state.currentPage = 1;
            state.currentFilter = {};
            state.currentSort = {};

            // Always switch to dashboard view when changing databases
            switchView('dashboard');

            // Load collections for the selected database
            await loadCollections();

            // Load dashboard for the selected database
            await loadEnhancedDashboard();
        }

        async function loadDatabases() {
            try {
                const response = await fetch('/api/databases');
                const data = await response.json();

                if (data.error) {
                    console.error('Error loading databases:', data.error);
                    return;
                }

                state.databases = data.databases || [];

                // Load from localStorage if not already set
                if (!state.currentDatabase) {
                    const savedDatabase = localStorage.getItem('nexadb_selected_database');
                    // Check if saved database exists in the list
                    if (savedDatabase && state.databases.includes(savedDatabase)) {
                        state.currentDatabase = savedDatabase;
                    } else if (state.databases.length > 0) {
                        // Default to first database if saved one doesn't exist
                        state.currentDatabase = state.databases[0];
                        localStorage.setItem('nexadb_selected_database', state.currentDatabase);
                    }
                }

                // Update button text
                const currentDbName = document.getElementById('currentDatabaseName');
                if (currentDbName) {
                    currentDbName.textContent = state.currentDatabase || 'Select Database';
                }

                // Show databases nav item for admin users
                if (state.currentUser && state.currentUser.role === 'admin') {
                    const databasesNavItem = document.getElementById('databasesNavItem');
                    if (databasesNavItem) {
                        databasesNavItem.style.display = 'flex';
                    }
                }

                // Load collections and dashboard for selected database
                if (state.currentDatabase) {
                    await loadCollections();
                    await loadEnhancedDashboard();
                }

            } catch (error) {
                console.error('Error loading databases:', error);
                showToast('error', 'Error', 'Failed to load databases');
            }
        }

        // Switch to different database (v3.0.0 Enterprise - Updated for Tree View)
        async function switchDatabase() {
            const selector = document.getElementById('databaseSelector');
            if (!selector) return;

            state.currentDatabase = selector.value;

            // Save selected database to localStorage
            localStorage.setItem('nexadb_selected_database', state.currentDatabase);

            showToast('info', 'Switching Database', `Switched to database: ${state.currentDatabase}`);

            // Clear current collection selection and view state
            state.currentCollection = null;
            state.selectedCollection = null;
            state.currentPage = 1;
            state.currentFilter = {};
            state.currentSort = {};

            // Always switch to dashboard view when changing databases
            switchView('dashboard');

            // Reload collections for new database
            await loadCollections();

            // Load dashboard for new database
            await loadEnhancedDashboard();
        }

        // Load databases list for management view
        async function loadDatabasesList() {
            try {
                const container = document.getElementById('databasesTableContainer');
                if (!container) return;

                // Show loading
                container.innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading databases...</p>
                    </div>
                `;

                const response = await fetch('/api/databases');
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">⚠️</div>
                            <h3>Error loading databases</h3>
                            <p>${data.error}</p>
                        </div>
                    `;
                    return;
                }

                const databases = data.databases || [];

                if (databases.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📦</div>
                            <h3>No databases yet</h3>
                            <p>Create your first database to get started</p>
                            <button class="btn btn-primary" onclick="showCreateDatabaseModal()">
                                <span>+</span>
                                <span>Create Database</span>
                            </button>
                        </div>
                    `;
                    return;
                }

                // Load stats for each database
                const databasesWithStats = await Promise.all(
                    databases.map(async (dbName) => {
                        try {
                            const statsResponse = await fetch(`/api/databases/${dbName}/stats`);
                            const statsData = await statsResponse.json();
                            return {
                                name: dbName,
                                stats: statsData.stats || {}
                            };
                        } catch (error) {
                            return {
                                name: dbName,
                                stats: {}
                            };
                        }
                    })
                );

                // Build table
                let html = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Database Name</th>
                                <th>Collections</th>
                                <th>Documents</th>
                                <th>Storage</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                databasesWithStats.forEach(db => {
                    const collectionsCount = db.stats.collections_count || 0;
                    const documentsCount = db.stats.documents_count || 0;
                    const storageBytes = db.stats.storage_bytes || 0;
                    const storageMB = (storageBytes / (1024 * 1024)).toFixed(2);

                    const isDefault = db.name === 'default';

                    html += `
                        <tr>
                            <td><strong>${db.name}</strong> ${isDefault ? '<span style="color: var(--primary); font-size: 11px;">(default)</span>' : ''}</td>
                            <td>${collectionsCount}</td>
                            <td>${documentsCount.toLocaleString()}</td>
                            <td>${storageMB} MB</td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="selectDatabaseAndView('${db.name}')" title="Switch to this database">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                        <circle cx="12" cy="12" r="3"/>
                                    </svg>
                                </button>
                                ${!isDefault ? `
                                    <button class="btn btn-sm btn-danger" onclick="showDropDatabaseModal('${db.name}')" title="Drop database">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <polyline points="3 6 5 6 21 6"/>
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                        </svg>
                                    </button>
                                ` : '<span style="color: var(--text-tertiary); font-size: 12px;">Cannot drop</span>'}
                            </td>
                        </tr>
                    `;
                });

                html += `
                        </tbody>
                    </table>
                `;

                container.innerHTML = html;

            } catch (error) {
                console.error('Error loading databases list:', error);
                showToast('error', 'Error', 'Failed to load databases list');
            }
        }

        // Select database and switch to collections view
        function selectDatabaseAndView(dbName) {
            const selector = document.getElementById('databaseSelector');
            if (selector) {
                selector.value = dbName;
                state.currentDatabase = dbName;
            }

            showToast('success', 'Database Selected', `Switched to database: ${dbName}`);
            switchView('collections');
            loadCollections();
        }

        // Show create database modal
        function showCreateDatabaseModal() {
            const modal = document.getElementById('createDatabaseModal');
            if (modal) {
                modal.classList.add('active');
                document.getElementById('newDatabaseName').value = '';
                document.getElementById('newDatabaseName').focus();
            }
        }

        // Create database
        async function createDatabase() {
            const nameInput = document.getElementById('newDatabaseName');
            const databaseName = nameInput.value.trim();

            if (!databaseName) {
                showToast('error', 'Validation Error', 'Database name is required');
                return;
            }

            // Validate database name
            if (!/^[a-z0-9_]+$/.test(databaseName)) {
                showToast('error', 'Validation Error', 'Database name must be lowercase alphanumeric with underscores');
                return;
            }

            try {
                const response = await fetch('/api/databases', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: databaseName })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showToast('success', 'Success', data.message || `Database "${databaseName}" created successfully`);
                    closeModal('createDatabaseModal');
                    await loadDatabases();
                    if (state.currentView === 'databases') {
                        await loadDatabasesList();
                    }
                } else {
                    showToast('error', 'Error', data.error || 'Failed to create database');
                }
            } catch (error) {
                console.error('Error creating database:', error);
                showToast('error', 'Error', 'Failed to create database');
            }
        }

        // Show drop database modal
        function showDropDatabaseModal(databaseName) {
            state.databaseToDelete = databaseName;

            const modal = document.getElementById('dropDatabaseModal');
            const nameEl = document.getElementById('dropDatabaseName');
            const confirmInput = document.getElementById('dropDatabaseConfirmInput');
            const dropBtn = document.getElementById('dropDatabaseBtn');

            if (modal && nameEl && confirmInput && dropBtn) {
                nameEl.textContent = databaseName;
                confirmInput.value = '';
                dropBtn.disabled = true;

                // Enable button when "DELETE" is typed
                confirmInput.oninput = () => {
                    dropBtn.disabled = confirmInput.value !== 'DELETE';
                };

                modal.classList.add('active');
                confirmInput.focus();
            }
        }

        // Confirm drop database
        async function confirmDropDatabase() {
            const databaseName = state.databaseToDelete;
            if (!databaseName) return;

            try {
                const response = await fetch(`/api/databases/${databaseName}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showToast('success', 'Success', data.message || `Database "${databaseName}" dropped successfully`);
                    closeModal('dropDatabaseModal');
                    clearDropDatabaseInput();

                    // If we just dropped the current database, switch to default
                    if (state.currentDatabase === databaseName) {
                        const selector = document.getElementById('databaseSelector');
                        if (selector) {
                            selector.value = 'default';
                            state.currentDatabase = 'default';
                        }
                    }

                    await loadDatabases();
                    if (state.currentView === 'databases') {
                        await loadDatabasesList();
                    }
                } else {
                    showToast('error', 'Error', data.error || 'Failed to drop database');
                }
            } catch (error) {
                console.error('Error dropping database:', error);
                showToast('error', 'Error', 'Failed to drop database');
            }
        }

        // Clear drop database input
        function clearDropDatabaseInput() {
            const confirmInput = document.getElementById('dropDatabaseConfirmInput');
            const dropBtn = document.getElementById('dropDatabaseBtn');

            if (confirmInput) confirmInput.value = '';
            if (dropBtn) dropBtn.disabled = true;

            state.databaseToDelete = null;
        }

        // ============================================================================
        // END DATABASE MANAGEMENT FUNCTIONS
        // ============================================================================

        // ============================================================================
        // USER DATABASE PERMISSIONS MANAGEMENT (v3.0.0)
        // ============================================================================

        // Show user database permissions modal
        async function showUserDatabasePermissions(username) {
            try {
                // Fetch user data with database permissions
                const response = await fetch(`/api/users/${username}`);
                const data = await response.json();

                if (data.error) {
                    showToast('error', 'Error', data.error);
                    return;
                }

                // Store current user for permissions management
                state.currentPermissionsUser = username;
                state.currentPermissionsData = data.database_permissions || {};

                // Populate modal
                const modal = document.getElementById('userDatabasePermissionsModal');
                const usernameEl = document.getElementById('permissionsUsername');
                const permissionsContainer = document.getElementById('databasePermissionsList');

                if (usernameEl) {
                    usernameEl.textContent = username;
                }

                // Build permissions list
                let html = '';
                const dbPerms = data.database_permissions || {};

                if (Object.keys(dbPerms).length === 0) {
                    html = `
                        <div class="empty-state" style="padding: 20px;">
                            <p>No database-specific permissions assigned</p>
                        </div>
                    `;
                } else {
                    html = '<div style="display: flex; flex-direction: column; gap: 8px;">';
                    for (const [dbName, permission] of Object.entries(dbPerms)) {
                        html += `
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--bg-secondary); border-radius: 8px;">
                                <div>
                                    <strong>${dbName}</strong>
                                    <span style="margin-left: 12px; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; background: ${getPermissionColor(permission)}15; color: ${getPermissionColor(permission)};">
                                        ${permission.toUpperCase()}
                                    </span>
                                </div>
                                <button class="btn btn-sm btn-danger" onclick='revokeDatabaseAccess("${username}", "${dbName}")'>
                                    Revoke
                                </button>
                            </div>
                        `;
                    }
                    html += '</div>';
                }

                if (permissionsContainer) {
                    permissionsContainer.innerHTML = html;
                }

                // Show modal
                if (modal) {
                    modal.classList.add('active');
                }

            } catch (error) {
                console.error('Error loading user permissions:', error);
                showToast('error', 'Error', 'Failed to load user permissions');
            }
        }

        // Get permission color
        function getPermissionColor(permission) {
            const colors = {
                'admin': '#8b5cf6',
                'write': '#6366f1',
                'read': '#10b981'
            };
            return colors[permission] || '#94a3b8';
        }

        // Show grant database access modal
        function showGrantDatabaseAccessModal() {
            const username = state.currentPermissionsUser;
            if (!username) return;

            const modal = document.getElementById('grantDatabaseAccessModal');
            const usernameEl = document.getElementById('grantAccessUsername');
            const databaseSelect = document.getElementById('grantAccessDatabase');

            if (usernameEl) {
                usernameEl.textContent = username;
            }

            // Populate database selector with available databases
            if (databaseSelect && state.databases) {
                databaseSelect.innerHTML = '<option value="">Select database...</option>' +
                    state.databases.map(db => `<option value="${db}">${db}</option>`).join('');
            }

            // Reset permission select
            const permissionSelect = document.getElementById('grantAccessPermission');
            if (permissionSelect) {
                permissionSelect.value = 'read';
            }

            if (modal) {
                modal.classList.add('active');
            }
        }

        // Grant database access
        async function grantDatabaseAccess() {
            const username = state.currentPermissionsUser;
            const database = document.getElementById('grantAccessDatabase').value;
            const permission = document.getElementById('grantAccessPermission').value;

            if (!database) {
                showToast('error', 'Validation Error', 'Please select a database');
                return;
            }

            if (!permission) {
                showToast('error', 'Validation Error', 'Please select a permission level');
                return;
            }

            try {
                const response = await fetch(`/api/users/${username}/database-access`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ database, permission })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showToast('success', 'Success', data.message || `Granted ${permission} access to ${database}`);
                    closeModal('grantDatabaseAccessModal');

                    // Refresh permissions display
                    await showUserDatabasePermissions(username);

                    // Refresh users list
                    if (state.currentView === 'users') {
                        await loadUsers();
                    }
                } else {
                    showToast('error', 'Error', data.error || 'Failed to grant access');
                }
            } catch (error) {
                console.error('Error granting database access:', error);
                showToast('error', 'Error', 'Failed to grant database access');
            }
        }

        // Revoke database access
        async function revokeDatabaseAccess(username, database) {
            if (!confirm(`Revoke access to database "${database}" for user "${username}"?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/users/${username}/database-access`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ database, permission: null })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showToast('success', 'Success', data.message || `Revoked access to ${database}`);

                    // Refresh permissions display
                    await showUserDatabasePermissions(username);

                    // Refresh users list
                    if (state.currentView === 'users') {
                        await loadUsers();
                    }
                } else {
                    showToast('error', 'Error', data.error || 'Failed to revoke access');
                }
            } catch (error) {
                console.error('Error revoking database access:', error);
                showToast('error', 'Error', 'Failed to revoke database access');
            }
        }

        // ============================================================================
        // END USER DATABASE PERMISSIONS MANAGEMENT
        // ============================================================================

        // Close modal on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove('active');
                }
            });
        });
