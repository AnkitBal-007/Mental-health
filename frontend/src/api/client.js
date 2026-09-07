/**
 * API client for the backend at http://localhost:8000.
 * Attaches the JWT token from localStorage automatically.
 */

const BASE_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
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
  // Normalize: backend returns { total, items } — map current_trend → score_trend
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
    // assigned_to can be a user ID integer — convert to string for display
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
