/**
 * Auth Service - Singleton service for authentication operations
 *
 * Provides token management and authentication utilities
 */

class AuthService {
    constructor() {
        if (AuthService.instance) {
            return AuthService.instance;
        }
        AuthService.instance = this;
    }

    /**
     * Get the current access token
     */
    getToken() {
        try {
            const tokensStr = localStorage.getItem('tokens');
            if (!tokensStr) return null;

            const tokens = JSON.parse(tokensStr);
            return tokens?.access || null;
        } catch (error) {
            console.error('Error getting token:', error);
            return null;
        }
    }

    /**
     * Get the current refresh token
     */
    getRefreshToken() {
        try {
            const tokensStr = localStorage.getItem('tokens');
            if (!tokensStr) return null;

            const tokens = JSON.parse(tokensStr);
            return tokens?.refresh || null;
        } catch (error) {
            console.error('Error getting refresh token:', error);
            return null;
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * Get tenant ID
     */
    getTenantId() {
        return localStorage.getItem('tenantId') || null;
    }

    /**
     * Get current user from localStorage
     */
    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) return null;

            return JSON.parse(userStr);
        } catch (error) {
            console.error('Error getting user:', error);
            return null;
        }
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        localStorage.removeItem('tokens');
        localStorage.removeItem('tenantId');
        localStorage.removeItem('user');
    }

    /**
     * Logout
     */
    logout() {
        this.clearAuth();
        window.location.href = '/assets/templates/login.html';
    }
}

// Create and export singleton instance
export const authService = new AuthService();
