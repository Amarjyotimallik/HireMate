/**
 * Authentication Context Provider
 * 
 * Provides auth state and methods across the application.
 * Handles login, logout, and auto-redirect after login.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    getAuthToken,
    getUser,
    setUser,
    setAuthTokens,
    clearAuth,
    apiUrl
} from '../api/client';

const AuthContext = createContext(null);

// Token storage key - must match client.js
const TOKEN_KEY = 'hiremate_access_token';

/**
 * Check if user is authenticated (has a real JWT token)
 */
function checkIsAuthenticated() {
    const token = localStorage.getItem(TOKEN_KEY);
    return !!token;
}

export function AuthProvider({ children }) {
    const [user, setUserState] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [redirectPath, setRedirectPath] = useState('/dashboard');

    // Initialize auth state on mount
    useEffect(() => {
        const authenticated = checkIsAuthenticated();
        setIsAuthenticated(authenticated);

        if (authenticated) {
            const storedUser = getUser();
            setUserState(storedUser);
        }

        setIsLoading(false);
    }, []);

    /**
     * Login with email and password
     */
    const login = async (email, password) => {
        const url = apiUrl('/auth/login');
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Invalid email or password');
        }

        const tokens = await res.json();
        setAuthTokens(tokens.access_token, tokens.refresh_token);

        // Fetch user info
        const userRes = await fetch(apiUrl('/auth/me'), {
            headers: { 'Authorization': `Bearer ${tokens.access_token}` },
        });

        if (userRes.ok) {
            const userData = await userRes.json();
            setUser(userData);
            setUserState(userData);
        }

        setIsAuthenticated(true);
        return redirectPath;
    };

    /**
     * Register a new user
     */
    const register = async (userData) => {
        const url = apiUrl('/auth/register');
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: userData.email,
                full_name: userData.full_name,
                password: userData.password,
                role: 'recruiter',
            }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Registration failed');
        }

        // Auto-login after registration
        return await login(userData.email, userData.password);
    };

    /**
     * Logout and clear auth state
     */
    const logout = () => {
        clearAuth();
        setUserState(null);
        setIsAuthenticated(false);
    };

    /**
     * Set path to redirect to after login
     */
    const setRedirectAfterLogin = (path) => {
        setRedirectPath(path);
    };

    const value = {
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        redirectPath,
        setRedirectAfterLogin,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to access auth context
 */
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
