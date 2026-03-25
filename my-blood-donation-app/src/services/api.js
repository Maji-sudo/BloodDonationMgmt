// Central API service for Smart Blood Bank
// All fetch calls go through here so the base URL is managed in one place.

const BASE_URL = 'http://localhost:8000';

async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 
    'Content-Type': 'application/json', 
    ...options.headers 
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await res.json();

  if (!res.ok) {
    // Throw the detail message from FastAPI if available
    throw new Error(data.detail || `Request failed: ${res.status}`);
  }

  return data;
}

// ── Auth ──────────────────────────────────────
export const authApi = {
  login: (payload) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  signup: (payload) =>
    request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ── Donors ────────────────────────────────────
export const donorApi = {
  register: (payload) =>
    request('/api/donors/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAll: (availableOnly = false) =>
    request(`/api/donors/?available_only=${availableOnly}`),

  searchByBloodType: (bloodType) =>
    request(`/api/donors/search?blood_type=${encodeURIComponent(bloodType)}`),

  getById: (id) => request(`/api/donors/${id}`),

  update: (id, payload) =>
    request(`/api/donors/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  delete: (id) => request(`/api/donors/${id}`, { method: 'DELETE' }),
};

// ── Recipients / Blood Requests ───────────────
export const recipientApi = {
  submitRequest: (payload) =>
    request('/api/recipients/request', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAll: (filters = {}) => {
    const params = new URLSearchParams(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== null)
    ).toString();
    return request(`/api/recipients/${params ? `?${params}` : ''}`);
  },

  getCritical: () => request('/api/recipients/critical'),

  getById: (id) => request(`/api/recipients/${id}`),

  update: (id, payload) =>
    request(`/api/recipients/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  fulfill: (id) =>
    request(`/api/recipients/${id}/fulfill`, { method: 'PATCH' }),

  delete: (id) =>
    request(`/api/recipients/${id}`, { method: 'DELETE' }),
};

// ── Blood Inventory ───────────────────────────
export const bloodApi = {
  getSummary: () => request('/api/blood/summary'),

  getAvailability: (bloodType) =>
    request(`/api/blood/availability/${encodeURIComponent(bloodType)}`),

  getAll: (filters = {}) => {
    const params = new URLSearchParams(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== null)
    ).toString();
    return request(`/api/blood/inventory${params ? `?${params}` : ''}`);
  },

  addEntry: (payload) =>
    request('/api/blood/inventory', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  addUnits: (id, units, reason) =>
    request(`/api/blood/inventory/${id}/add`, {
      method: 'PATCH',
      body: JSON.stringify({ units, reason }),
    }),

  consumeUnits: (id, units, reason) =>
    request(`/api/blood/inventory/${id}/consume`, {
      method: 'PATCH',
      body: JSON.stringify({ units, reason }),
    }),
};
