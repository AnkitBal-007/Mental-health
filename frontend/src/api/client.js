/**
 * API client for the Sahayak Backend.
 * Attaches the JWT token from localStorage automatically.
 */

// Reads configured backend URL or defaults to standard local dev
const rawUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL || '';
export const BASE_URL = rawUrl ? rawUrl.replace(/\/+$/, '') : (
  typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    ? '' // In production if unset, fallback to relative or warn
    : 'http://localhost:8000'
);

function getToken() {
  return localStorage.getItem('token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Check for HTTPS mixed content warning
  const effectiveBase = BASE_URL || (typeof window !== 'undefined' && window.location.origin.includes('localhost') ? 'http://localhost:8000' : '');
  
  if (!effectiveBase && typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    throw new Error('Backend URL is not configured. Please set VITE_BACKEND_URL in your Vercel project settings.');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for cold-start resilience

  try {
    const res = await fetch(`${effectiveBase}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // If 401 on login, throw credentials error
    if (res.status === 401) {
      if (path.includes('/auth/login')) {
        throw new Error('Incorrect username or password. Please verify credentials.');
      }
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please sign in again.');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `API error ${res.status}`);
    }

    // 204 No Content
    if (res.status === 204) return null;
    return res.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Connection timed out. If using free hosting (Render), the backend may take 30-50s to wake up from sleep. Please try again.');
    }
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Cannot connect to backend server. Please verify your Render backend is running and CORS is configured.');
    }
    throw err;
  }
}

// Auth
export const login = (username, password) =>
  request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

// Victims
export const fetchVictims = async (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  const data = await request(`/victims${qs ? `?${qs}` : ''}`);
  const victims = (data?.items || data?.victims || data || []).map((v) => ({
    ...v,
    score_trend: v.score_trend || v.current_trend,
    last_check_in: v.last_check_in || v.updated_at,
  }));
  return { ...data, victims, total: data?.total ?? victims.length };
};

export const fetchVictimById = (id) => request(`/victims/${id}`);

export const fetchVictimCheckIns = (id, limit = 30) =>
  request(`/victims/${id}/check-ins?limit=${limit}`);

export const fetchVictimRecommendations = (id) =>
  request(`/victims/${id}/recommendations`);

// Alerts
export const fetchAlerts = async (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  const data = await request(`/alerts${qs ? `?${qs}` : ''}`);
  const alerts = (data?.items || data?.alerts || data || []).map((a) => ({
    ...a,
    assigned_to: typeof a.assigned_to === 'number'
      ? `User #${a.assigned_to}`
      : a.assigned_to,
  }));
  return { ...data, alerts, total: data?.total ?? alerts.length };
};

export const updateAlert = (id, data) =>
  request(`/alerts/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const evaluateAlert = (victimId) =>
  request('/alerts/evaluate', {
    method: 'POST',
    body: JSON.stringify({ victim_id: victimId }),
  });

// Dashboard
export const fetchDashboardSummary = (scope, id) =>
  request(`/dashboard/summary?scope=${scope}&id=${id}`);
