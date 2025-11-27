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
                    ? '/admin_panel/logo-light.svg'
                    : '/admin_panel/logo-dark.svg';
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
            baseUrl: 'http://localhost:6969',
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
            documentToDelete: null
        };

        // View Switching
        function switchView(viewName) {
            state.currentView = viewName;

            // Update nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            event.currentTarget.classList.add('active');

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
                'users': 'usersView'
            };

            document.getElementById(views[viewName]).classList.add('active');

            // Update header
            const titles = {
                'dashboard': 'Dashboard',
                'collections': 'Collections',
                'query': 'Query Editor',
                'search': 'Vector Search',
                'monitoring': 'Monitoring',
                'users': 'User Management'
            };

            const subtitles = {
                'dashboard': 'Overview of your database',
                'collections': 'Browse and manage your data',
                'query': 'Execute queries and view results',
                'search': 'Search with vector embeddings',
                'monitoring': 'Real-time performance metrics',
                'users': 'Manage users and permissions (Admin Only)'
            };

            document.getElementById('contentTitle').textContent = titles[viewName];
            document.getElementById('contentSubtitle').textContent = subtitles[viewName];

            // Show/hide sidebar collections
            if (viewName === 'collections') {
                document.getElementById('sidebarCollections').style.display = 'flex';
                document.getElementById('sidebarCollections').style.flexDirection = 'column';
                document.getElementById('sidebarCollections').style.flex = '1';
                loadCollections();
            } else {
                document.getElementById('sidebarCollections').style.display = 'none';
            }

            // Initialize view-specific content
            if (viewName === 'dashboard') {
                loadDashboard();
            } else if (viewName === 'query') {
                loadQueryEditor();
            } else if (viewName === 'search') {
                loadVectorSearch();
            } else if (viewName === 'monitoring') {
                loadMonitoring();
            } else if (viewName === 'users') {
                loadUsers();
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
                updateConnectionStatus(true, `Connected to ${status.database}`);
                loadCollections();
                loadDashboard();
                showToast('success', 'Connected', `Connected to ${status.database} v${status.version}`);
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

        // Dashboard Functions
        async function loadDashboard() {
            try {
                // Use admin server API endpoint (not REST API server)
                const response = await fetch('/api/collections');
                const result = await response.json();
                state.collections = result.collections || [];

                // Update metrics
                document.getElementById('totalCollections').textContent = state.collections.length;

                // Load document count
                let totalDocs = 0;
                let totalStorage = 0;

                for (const collection of state.collections) {
                    try {
                        const collResult = await apiCall('GET', `/collections/${collection}?query={}&limit=1`);
                        totalDocs += collResult.count || 0;
                        // Estimate storage (rough calculation)
                        totalStorage += (collResult.count || 0) * 0.5; // Assume 0.5KB per document
                    } catch (err) {
                        console.error(`Failed to load stats for ${collection}`);
                    }
                }

                document.getElementById('totalDocuments').textContent = totalDocs;
                document.getElementById('totalStorage').textContent = totalStorage.toFixed(2) + ' KB';
                document.getElementById('totalOperations').textContent = state.operationsCount;

                // Update operations chart
                updateOperationsChart();

                // Update recent collections list
                updateRecentCollections();

            } catch (error) {
                console.error('Failed to load dashboard:', error);
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

        function viewCollection(name) {
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
        async function loadCollections() {
            try {
                // Use admin server API endpoint (not REST API server)
                const response = await fetch('/api/collections');
                const result = await response.json();
                state.collections = result.collections || [];
                renderCollections();

                // Update query editor collection dropdown
                const select = document.getElementById('queryEditorCollection');
                if (select) {
                    select.innerHTML = '<option value="">Select collection...</option>' +
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
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="collection-count" id="count-${name}">0</span>
                        ${canDelete ? `
                        <button class="collection-delete-btn" onclick="event.stopPropagation(); deleteCollection('${name}')" title="Delete collection">
                            ×
                        </button>
                        ` : ''}
                    </div>
                </div>
            `).join('');

            state.collections.forEach(name => loadCollectionCount(name));
        }

        async function loadCollectionCount(name) {
            try {
                const result = await apiCall('GET', `/collections/${name}?query={}&limit=999999`);
                const countEl = document.getElementById(`count-${name}`);
                if (countEl) countEl.textContent = result.count;
            } catch (error) {
                console.error('Failed to load count for', name);
            }
        }

        function filterCollections() {
            const search = document.getElementById('collectionSearch').value.toLowerCase();
            const items = document.querySelectorAll('.collection-item');
            items.forEach(item => {
                const name = item.textContent.toLowerCase();
                item.style.display = name.includes(search) ? 'flex' : 'none';
            });
        }

        async function selectCollection(name) {
            state.currentCollection = name;
            state.currentPage = 1;
            renderCollections();
            loadDocuments();
        }

        async function loadDocuments() {
            const container = document.getElementById('tableContainer');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading documents...</p></div>';

            try {
                const skip = (state.currentPage - 1) * state.pageSize;
                const filterQuery = Object.keys(state.currentFilter).length > 0 ?
                    JSON.stringify(state.currentFilter) : '{}';

                // First, get the total count with a large limit to get the actual total
                let countUrl = `/collections/${state.currentCollection}?query=${encodeURIComponent(filterQuery)}&limit=999999`;
                const countResult = await apiCall('GET', countUrl);
                state.totalDocuments = countResult.count;

                // Then, get the actual page of documents
                let url = `/collections/${state.currentCollection}?query=${encodeURIComponent(filterQuery)}&limit=${state.pageSize}&skip=${skip}`;

                if (Object.keys(state.currentSort).length > 0) {
                    url += `&sort=${encodeURIComponent(JSON.stringify(state.currentSort))}`;
                }

                const result = await apiCall('GET', url);

                if (state.viewMode === 'json') {
                    renderDocumentsJSON(result.documents);
                } else {
                    renderDocumentsTable(result.documents);
                }
                updatePagination();
            } catch (error) {
                container.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${error.message}</p></div>`;
            }
        }

        function setViewMode(mode) {
            state.viewMode = mode;
            document.getElementById('jsonViewBtn').classList.toggle('active', mode === 'json');
            document.getElementById('tableViewBtn').classList.toggle('active', mode === 'table');

            // Hide columns button in JSON view
            const columnsBtn = document.getElementById('columnsBtn');
            columnsBtn.style.display = mode === 'table' ? 'inline-flex' : 'none';

            loadDocuments();
        }

        function renderDocumentsJSON(documents) {
            const container = document.getElementById('tableContainer');

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

            container.innerHTML = `
                <div style="padding: 20px;">
                    ${documents.map((doc, index) => `
                        <div style="margin-bottom: 16px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">
                            <div style="padding: 12px 20px; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-size: 14px; font-weight: 700; color: var(--text-secondary);">Document ${(state.currentPage - 1) * state.pageSize + index + 1}</div>
                                ${canWrite ? `
                                <div style="display: flex; gap: 8px;">
                                    <button class="icon-btn" onclick='editDocumentFromTable(${JSON.stringify(doc).replace(/'/g, "&apos;")})' title="Edit">✎</button>
                                    <button class="icon-btn" onclick='deleteDocument("${doc._id}")' title="Delete">×</button>
                                </div>
                                ` : ''}
                            </div>
                            <div style="padding: 20px; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.8; color: var(--text-secondary); overflow-x: auto;">
                                <pre style="margin: 0;">${syntaxHighlightJSON(doc)}</pre>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            document.getElementById('pagination').style.display = 'flex';
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

        function renderDocumentsTable(documents) {
            const container = document.getElementById('tableContainer');

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

                for (const docId of selectedIds) {
                    try {
                        await apiCall('DELETE', `/collections/${state.currentCollection}/${docId}`);
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
                    loadDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
            }
        }

        function updatePagination() {
            const totalPages = Math.ceil(state.totalDocuments / state.pageSize) || 1;
            const start = state.totalDocuments > 0 ? (state.currentPage - 1) * state.pageSize + 1 : 0;
            const end = Math.min(state.currentPage * state.pageSize, state.totalDocuments);

            // Update text
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
                // Create collection by inserting and deleting a dummy document
                const initDoc = {_init: true, _timestamp: Date.now()};
                await apiCall('POST', `/collections/${name}`, initDoc);

                // Verify collection was created and clean up init document
                const result = await apiCall('GET', `/collections/${name}?query={}`);
                if (result.documents && result.documents.length > 0) {
                    // Delete all init documents
                    for (const doc of result.documents) {
                        if (doc._init) {
                            await apiCall('DELETE', `/collections/${name}/${doc._id}`);
                        }
                    }
                }

                closeModal('createCollectionModal');
                showToast('success', 'Success', `Collection "${name}" created`);
                document.getElementById('newCollectionName').value = '';
                loadCollections();
                selectCollection(name);

                // Reload dashboard if visible
                if (state.currentView === 'dashboard') {
                    loadDashboard();
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
                await apiCall('DELETE', `/collections/${name}`);

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
                    loadDashboard();
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
                await apiCall('POST', `/collections/${state.currentCollection}`, data);
                closeModal('insertDocumentModal');
                showToast('success', 'Success', 'Document inserted');
                document.getElementById('insertDocumentData').value = '';
                loadDocuments();
                loadCollectionCount(state.currentCollection);

                if (state.currentView === 'dashboard') {
                    loadDashboard();
                }
            } catch (error) {
                showToast('error', 'Error', error.message);
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
                await apiCall('PUT', `/collections/${state.currentCollection}/${docId}`, updates);
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

                await apiCall('DELETE', `/collections/${state.currentCollection}/${docId}`);
                showToast('success', 'Success', 'Document deleted');
                loadDocuments();
                loadCollectionCount(state.currentCollection);

                if (state.currentView === 'dashboard') {
                    loadDashboard();
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

                // Check if it's an aggregation pipeline (array)
                if (Array.isArray(query)) {
                    result = await apiCall('POST', `/collections/${collection}/aggregate`, { pipeline: query });
                    result.documents = result.results;
                } else {
                    result = await apiCall('GET',
                        `/collections/${collection}?query=${encodeURIComponent(JSON.stringify(query))}&limit=100`);
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
                // Display JSON
                resultsContent.textContent = JSON.stringify(state.currentResultData.documents, null, 2);
                statsContainer.style.display = 'none';
            } else {
                // Display TOON - convert the current query results (not entire collection)
                try {
                    const toonData = convertJsonToToon(
                        state.currentResultData.collection,
                        state.currentResultData.documents
                    );

                    const jsonStr = JSON.stringify(state.currentResultData.documents);
                    const jsonSize = jsonStr.length;
                    const toonSize = toonData.length;
                    const reductionPercent = ((jsonSize - toonSize) / jsonSize * 100).toFixed(1);

                    resultsContent.textContent = toonData;

                    document.getElementById('editorJsonSize').textContent = jsonSize + ' bytes';
                    document.getElementById('editorReduction').textContent = reductionPercent + '%';
                    document.getElementById('editorSavings').textContent = '$' + (reductionPercent * 10).toFixed(2);
                    statsContainer.style.display = 'block';
                } catch (error) {
                    resultsContent.textContent = `Error converting to TOON: ${error.message}`;
                    statsContainer.style.display = 'none';
                }
            }
        }

        function convertJsonToToon(collectionName, documents) {
            if (!documents || documents.length === 0) {
                return `[0]:\ncount: 0`;
            }

            let output = `[${documents.length}]:\n`;

            documents.forEach((doc, idx) => {
                output += formatToonValue(doc, 1, true);  // Pass true for root document
                if (idx < documents.length - 1) {
                    output += '\n';
                }
            });

            return output;
        }

        function formatToonValue(value, indent = 0, isRootDoc = false) {
            const spaces = '  '.repeat(indent);

            if (value === null || value === undefined) {
                return 'null';
            }

            if (Array.isArray(value)) {
                if (value.length === 0) {
                    return '[]';
                }

                // Check if all elements are primitives
                const allPrimitives = value.every(v =>
                    v === null || typeof v !== 'object'
                );

                if (allPrimitives) {
                    // Inline array: [3]: val1,val2,val3
                    const items = value.map(v =>
                        v === null ? 'null' :
                        typeof v === 'string' ? v :
                        String(v)
                    );
                    return `[${value.length}]: ${items.join(',')}`;
                } else {
                    // Multi-line array with objects
                    let result = `[${value.length}]:\n`;
                    value.forEach((item, i) => {
                        result += spaces + '  - ';
                        if (typeof item === 'object' && item !== null) {
                            const lines = formatToonObject(item, indent + 2, false).split('\n');
                            result += lines[0] + '\n';
                            for (let j = 1; j < lines.length; j++) {
                                result += spaces + '    ' + lines[j];
                                if (j < lines.length - 1) result += '\n';
                            }
                        } else {
                            result += formatPrimitive(item);
                        }
                        if (i < value.length - 1) result += '\n';
                    });
                    return result;
                }
            }

            if (typeof value === 'object') {
                return formatToonObject(value, indent, isRootDoc);
            }

            return formatPrimitive(value);
        }

        function formatToonObject(obj, indent = 0, isRootDoc = false) {
            const spaces = '  '.repeat(indent);
            let result = '';
            const keys = Object.keys(obj);

            keys.forEach((key, i) => {
                const value = obj[key];

                // Only add '-' for root document, not for nested objects
                if (isRootDoc && i === 0) {
                    result += `${spaces}- ${key}: `;
                } else {
                    result += `${spaces}${key}: `;
                }

                if (value === null || value === undefined) {
                    result += 'null';
                } else if (Array.isArray(value)) {
                    if (value.length === 0) {
                        result += '[]';
                    } else {
                        const allPrimitives = value.every(v =>
                            v === null || typeof v !== 'object'
                        );

                        if (allPrimitives) {
                            const items = value.map(v =>
                                v === null ? 'null' :
                                typeof v === 'string' ? (v.includes(':') || v.includes(',') ? `"${v}"` : v) :
                                String(v)
                            );
                            result += `[${value.length}]: ${items.join(',')}`;
                        } else {
                            result += '\n';
                            value.forEach((item, idx) => {
                                result += spaces + '  - ';
                                if (typeof item === 'object' && item !== null) {
                                    // For array items, don't use dash prefix for nested keys
                                    const itemStr = formatToonObject(item, indent + 2, false);
                                    // Remove first dash if it exists
                                    const lines = itemStr.split('\n');
                                    result += lines[0].replace(/^\s*-\s*/, '');
                                    for (let j = 1; j < lines.length; j++) {
                                        result += '\n' + spaces + '    ' + lines[j];
                                    }
                                } else {
                                    result += formatPrimitive(item);
                                }
                                if (idx < value.length - 1) result += '\n';
                            });
                        }
                    }
                } else if (typeof value === 'object') {
                    result += '\n';
                    const nested = formatToonObject(value, indent + 1, false);
                    result += nested;
                } else {
                    result += formatPrimitive(value);
                }

                if (i < keys.length - 1) {
                    result += '\n';
                }
            });

            return result;
        }

        function formatPrimitive(value) {
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
                // Quote strings that contain special characters
                if (value.includes(':') || value.includes(',') || value.includes('\n') || value.includes('"')) {
                    return `"${value.replace(/"/g, '\\"')}"`;
                }
                return value;
            }
            return String(value);
        }

        function clearEditor() {
            document.getElementById('queryEditorTextarea').value = '{ }';
            document.getElementById('editorResults').style.display = 'none';
        }

        async function copyResults() {
            const resultsContent = document.getElementById('editorResultsContent');
            const text = resultsContent.textContent;

            if (!text) {
                showToast('error', 'Error', 'No results to copy');
                return;
            }

            try {
                await navigator.clipboard.writeText(text);
                showToast('success', 'Copied!', 'Results copied to clipboard');
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
                    showToast('success', 'Copied!', 'Results copied to clipboard');
                } catch (err) {
                    showToast('error', 'Error', 'Failed to copy results');
                }
                document.body.removeChild(textArea);
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
                const response = await fetch(`${state.baseUrl}/users`, {
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

                container.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Role</th>
                                <th>API Key</th>
                                <th>Created At</th>
                                <th>Last Login</th>
                                <th class="actions-cell">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(user => `
                                <tr>
                                    <td><span style="font-weight: 600;">${user.username}</span></td>
                                    <td>
                                        <span class="role-badge role-${user.role}" style="padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; background: ${getRoleColor(user.role)}15; color: ${getRoleColor(user.role)};">
                                            ${user.role.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <code style="font-size: 12px; background: var(--bg-tertiary); padding: 4px 8px; border-radius: 4px;">${user.api_key.substring(0, 20)}...</code>
                                    </td>
                                    <td>${new Date(user.created_at * 1000).toLocaleString()}</td>
                                    <td>${user.last_login ? new Date(user.last_login * 1000).toLocaleString() : 'Never'}</td>
                                    <td class="actions-cell">
                                        <button class="icon-btn" onclick='editUser(${JSON.stringify(user).replace(/'/g, "&apos;")})' title="${user.username === 'root' ? 'Change Password' : 'Edit User'}">✎</button>
                                        <button class="icon-btn" onclick='deleteUser("${user.username}")' title="Delete" ${user.username === 'root' ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>×</button>
                                    </td>
                                </tr>
                            `).join('')}
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

                // Show Users menu item only for admins
                if (state.currentUser.role === 'admin') {
                    const usersNavItem = document.getElementById('usersNavItem');
                    if (usersNavItem) {
                        usersNavItem.style.display = 'flex';
                    }
                }

                // Hide write/admin buttons for read-only users
                const canWrite = state.currentUser.role === 'write' || state.currentUser.role === 'admin';
                const canAdmin = state.currentUser.role === 'admin';

                if (!canWrite) {
                    // Hide insert/edit buttons
                    const addRecordBtn = document.getElementById('addRecordBtn');
                    if (addRecordBtn) addRecordBtn.style.display = 'none';
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
                        dimensions
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

            // Display results with similarity scores
            let html = '<div style="padding: 20px;">';

            results.forEach((result, index) => {
                const similarity = (result.similarity * 100).toFixed(2);
                const doc = result.document;

                html += `
                    <div style="margin-bottom: 16px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">
                        <div style="padding: 12px 20px; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 14px; font-weight: 700; color: var(--text-secondary);">Result #${index + 1}</span>
                                ${doc._id ? `<span style="font-size: 12px; color: var(--text-tertiary); margin-left: 12px;">ID: ${doc._id}</span>` : ''}
                            </div>
                            <div style="background: rgba(139, 92, 246, 0.15); color: var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 700;">
                                ${similarity}% match
                            </div>
                        </div>
                        <div style="padding: 20px; font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.8; color: var(--text-secondary); overflow-x: auto;">
                            <pre style="margin: 0;">${syntaxHighlightJSON(doc)}</pre>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            resultsContent.innerHTML = html;

            // Store results for copy functionality
            state.currentSearchResults = results;
        }

        function clearSearchEditor() {
            document.getElementById('searchVectorInput').value = '[]';
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('searchK').value = '10';
        }

        async function copySearchResults() {
            if (!state.currentSearchResults || state.currentSearchResults.length === 0) {
                showToast('error', 'Error', 'No results to copy');
                return;
            }

            try {
                const text = JSON.stringify(state.currentSearchResults, null, 2);
                await navigator.clipboard.writeText(text);
                showToast('success', 'Copied!', 'Search results copied to clipboard');
            } catch (error) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = JSON.stringify(state.currentSearchResults, null, 2);
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    showToast('success', 'Copied!', 'Search results copied to clipboard');
                } catch (err) {
                    showToast('error', 'Error', 'Failed to copy results');
                }
                document.body.removeChild(textArea);
            }
        }

        // Close modal on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove('active');
                }
            });
        });
