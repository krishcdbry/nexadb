// Authentication Module for NexaDB Admin Panel
class AuthManager {
    constructor() {
        this.ADMIN_BASE = window.location.origin;   // Admin server with session auth
        this.API_BASE = window.location.origin;     // Use same origin (admin server proxies to binary)
        this.session = this.loadSession();
    }

    loadSession() {
        const sessionData = localStorage.getItem('nexadb_session');
        if (sessionData) {
            try {
                return JSON.parse(sessionData);
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    saveSession(username, apiKey, role) {
        const session = {
            username,
            apiKey,
            role,
            loginTime: Date.now()
        };
        localStorage.setItem('nexadb_session', JSON.stringify(session));
        this.session = session;
    }

    clearSession() {
        localStorage.removeItem('nexadb_session');
        this.session = null;
    }

    isLoggedIn() {
        return this.session !== null;
    }

    getCurrentUser() {
        return this.session;
    }

    isAdmin() {
        return this.session && this.session.role === 'admin';
    }

    hasPermission(permission) {
        if (!this.session) return false;

        const rolePermissions = {
            'admin': ['read', 'write', 'admin'],
            'write': ['read', 'write'],
            'read': ['read'],
            'guest': ['read']
        };

        return rolePermissions[this.session.role]?.includes(permission) || false;
    }

    async login(username, password) {
        try {
            // Login via admin server - sets session cookie
            const response = await fetch(`${this.ADMIN_BASE}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',  // Important: include cookies
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Login failed');
            }

            const data = await response.json();
            // Save to localStorage for convenience (username, role display)
            this.saveSession(data.username, data.api_key, data.role);
            return data;
        } catch (error) {
            throw error;
        }
    }

    async logout() {
        try {
            // Call logout endpoint to clear server-side session
            await fetch(`${this.ADMIN_BASE}/api/auth/logout`, {
                method: 'GET',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        }

        // Clear local session
        this.clearSession();
        window.location.href = '/admin_panel/login.html';
    }

    async apiRequest(endpoint, options = {}) {
        if (!this.session) {
            throw new Error('Not authenticated');
        }

        const headers = {
            'X-API-Key': this.session.apiKey,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(`${this.API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401 || response.status === 403) {
            this.clearSession();
            window.location.href = '/admin_panel/login.html';
            throw new Error('Session expired');
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Request failed');
        }

        return response.json();
    }

    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = '/admin_panel/login.html';
        }
    }

    requireAdmin() {
        this.requireAuth();
        if (!this.isAdmin()) {
            alert('Access denied. Admin role required.');
            window.location.href = '/admin_panel/index.html';
        }
    }
}

// Create global auth instance
const auth = new AuthManager();
