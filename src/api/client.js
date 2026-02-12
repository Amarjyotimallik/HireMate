/**
 * API client for HireMate backend.
 * Base URL: VITE_API_URL in .env or http://localhost:8000
 * Supports JWT authentication with fallback to demo token.
 */
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Token storage keys
const TOKEN_KEY = 'hiremate_access_token';
const REFRESH_TOKEN_KEY = 'hiremate_refresh_token';
const USER_KEY = 'hiremate_user';

/**
 * Store authentication tokens after login/register.
 */
export function setAuthTokens(accessToken, refreshToken) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Get the current access token from storage.
 * Returns null if not logged in.
 */
export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get the refresh token from storage.
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store user info after successful authentication.
 */
export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get stored user info.
 */
export function getUser() {
  const stored = localStorage.getItem(USER_KEY);
  return stored ? JSON.parse(stored) : null;
}

/**
 * Clear all auth data (logout).
 */
export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated() {
  const token = localStorage.getItem(TOKEN_KEY);
  return !!token;
}

function authHeaders(extra = {}) {
  return {
    Authorization: `Bearer ${getAuthToken()}`,
    ...extra,
  };
}

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  const suffix = p.startsWith('/api') ? p : `/api/v1${p}`;
  return `${API_BASE.replace(/\/$/, '')}${suffix}`;
}

export async function apiGet(path, options = {}) {
  try {
    const url = path.startsWith('http') ? path : apiUrl(path);
    const res = await fetch(url, {
      ...options,
      headers: authHeaders(options.headers),
    });

    if (!res.ok) {
      const err = new Error(res.statusText || 'Request failed');
      err.status = res.status;
      err.body = await res.text();
      try {
        err.json = JSON.parse(err.body);
        // Provide user-friendly error message
        err.message = err.json.detail || err.json.message || res.statusText || 'Request failed';
      } catch (_) {
        err.message = res.statusText || 'Request failed';
      }

      // Handle specific status codes
      if (res.status === 401) {
        err.message = 'Session expired. Please log in again.';
        clearAuth();
      } else if (res.status === 403) {
        err.message = err.json?.detail || 'Access denied.';
      } else if (res.status === 404) {
        err.message = err.json?.detail || 'Resource not found.';
      } else if (res.status >= 500) {
        err.message = 'Server error. Please try again later.';
      } else if (res.status === 0 || !navigator.onLine) {
        err.message = 'No internet connection. Please check your network.';
      }

      throw err;
    }
    return res.json();
  } catch (err) {
    // Handle network errors
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const networkErr = new Error('Network error. Please check your internet connection.');
      networkErr.status = 0;
      throw networkErr;
    }
    throw err;
  }
}

export async function apiPost(path, body, options = {}) {
  try {
    const url = path.startsWith('http') ? path : apiUrl(path);
    const res = await fetch(url, {
      method: 'POST',
      headers: authHeaders({
        'Content-Type': 'application/json',
        ...options.headers,
      }),
      body: typeof body === 'string' ? body : JSON.stringify(body),
      ...options,
    });

    if (!res.ok) {
      const err = new Error(res.statusText || 'Request failed');
      err.status = res.status;
      err.body = await res.text();
      try {
        err.json = JSON.parse(err.body);
        err.message = err.json.detail || err.json.message || res.statusText || 'Request failed';
      } catch (_) {
        err.message = res.statusText || 'Request failed';
      }

      // Handle specific status codes
      if (res.status === 401) {
        err.message = 'Session expired. Please log in again.';
        clearAuth();
      } else if (res.status === 403) {
        err.message = err.json?.detail || 'Access denied.';
      } else if (res.status === 404) {
        err.message = err.json?.detail || 'Resource not found.';
      } else if (res.status >= 500) {
        err.message = 'Server error. Please try again later.';
      } else if (res.status === 0 || !navigator.onLine) {
        err.message = 'No internet connection. Please check your network.';
      }

      throw err;
    }
    return res.json();
  } catch (err) {
    // Handle network errors
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const networkErr = new Error('Network error. Please check your internet connection.');
      networkErr.status = 0;
      throw networkErr;
    }
    throw err;
  }
}

export async function apiDelete(path, options = {}) {
  try {
    const url = path.startsWith('http') ? path : apiUrl(path);
    const res = await fetch(url, {
      ...options,
      method: 'DELETE',
      headers: authHeaders(options.headers),
    });

    if (!res.ok) {
      const err = new Error(res.statusText || 'Request failed');
      err.status = res.status;
      err.body = await res.text();
      try {
        err.json = JSON.parse(err.body);
        err.message = err.json.detail || err.json.message || res.statusText || 'Request failed';
      } catch (_) {
        err.message = res.statusText || 'Request failed';
      }

      if (res.status === 401) {
        err.message = 'Session expired. Please log in again.';
        clearAuth();
      } else if (res.status === 403) {
        err.message = err.json?.detail || 'Access denied.';
      } else if (res.status === 404) {
        err.message = err.json?.detail || 'Resource not found.';
      }

      throw err;
    }
    return res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const networkErr = new Error('Network error. Please check your internet connection.');
      networkErr.status = 0;
      throw networkErr;
    }
    throw err;
  }
}

/**
 * Login user and store tokens.
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<{user: object, tokens: object}>}
 */
export async function login(email, password) {
  const url = apiUrl('/auth/login');
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = new Error('Login failed');
    err.status = res.status;
    try {
      const data = await res.json();
      err.message = data.detail || 'Invalid email or password';
    } catch (_) { }
    throw err;
  }

  const tokens = await res.json();
  setAuthTokens(tokens.access_token, tokens.refresh_token);

  // Fetch user info
  const user = await apiGet('/auth/me');
  setUser(user);

  return { user, tokens };
}

/**
 * Register new user and auto-login.
 * @param {object} userData - { email, full_name, password }
 * @returns {Promise<{user: object, tokens: object}>}
 */
export async function register(userData) {
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
    const err = new Error('Registration failed');
    err.status = res.status;
    try {
      const data = await res.json();
      err.message = data.detail || 'Registration failed';
    } catch (_) { }
    throw err;
  }

  // Auto-login after registration
  return await login(userData.email, userData.password);
}

/**
 * Logout and clear auth data.
 */
export function logout() {
  clearAuth();
}

/**
 * Build assessment link for current app origin (localhost:5173 in dev or your deployed URL).
 */
export function assessmentLinkUrl(token) {
  return `${window.location.origin}/assessment/${token}`;
}
