const API_BASE_URL = '/api';
const ADMIN_API_TOKEN = import.meta.env.VITE_ADMIN_API_TOKEN ?? 'dashboard-service-token';
let sessionToken = '';
let sessionTokenExpiry = 0;
let pendingAuthentication = null;

function tokenIsValid() {
  return sessionToken && Date.now() < sessionTokenExpiry;
}

function resetSessionToken() {
  sessionToken = '';
  sessionTokenExpiry = 0;
}

async function authenticateWithStaticToken() {
  const response = await fetch(`${API_BASE_URL}/auth/mobile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify({ token: ADMIN_API_TOKEN })
  });

  if (!response.ok) {
    const error = new Error(`Authentication failed with status ${response.status}`);
    error.status = response.status;
    error.body = await response.text();
    throw error;
  }

  const payload = await response.json();
  sessionToken = payload.access_token;
  const expiresInMs = Number(payload.expires_in ?? 0) * 1000;
  const safetyWindow = 5000;
  sessionTokenExpiry = Date.now() + Math.max(expiresInMs - safetyWindow, 0);
  return sessionToken;
}

async function getSessionToken() {
  if (tokenIsValid()) {
    return sessionToken;
  }

  if (!pendingAuthentication) {
    pendingAuthentication = authenticateWithStaticToken()
      .catch((error) => {
        resetSessionToken();
        throw error;
      })
      .finally(() => {
        pendingAuthentication = null;
      });
  }

  return pendingAuthentication;
}

async function request(path, options = {}) {
  const { skipAuth = false, ...fetchOptions } = options;

  async function performRequest(withAuth) {
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(fetchOptions.headers ?? {})
    };

    if (withAuth) {
      const token = await getSessionToken();
      headers.Authorization = `Bearer ${token}`;
    }

    return fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      headers
    });
  }

  let response = await performRequest(!skipAuth);

  if (response.status === 401 && !skipAuth) {
    resetSessionToken();
    response = await performRequest(true);
  }

  if (!response.ok) {
    const error = new Error(`Request failed with status ${response.status}`);
    error.status = response.status;
    error.body = await response.text();
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export async function getHealth() {
  return request('/health', { skipAuth: true });
}

export async function getQueueJobs() {
  return request('/queue/jobs');
}

export async function listEncodingRules() {
  return request('/config/encoding/rules');
}

export async function getSmbConfiguration() {
  return request('/config/smb');
}

export async function updateSmbConfiguration(payload) {
  return request('/config/smb', {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export async function testSmbConfiguration(payload) {
  return request('/config/smb/test', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function listSmbPresets() {
  return request('/config/smb/presets');
}

export async function createSmbPreset(payload) {
  return request('/config/smb/presets', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function updateSmbPreset(id, payload) {
  return request(`/config/smb/presets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  });
}

export async function deleteSmbPreset(id) {
  return request(`/config/smb/presets/${id}`, {
    method: 'DELETE'
  });
}

export async function getDashboardOverview() {
  return request('/analytics/overview');
}

export async function listDashboardEvents() {
  return request('/analytics/events');
}

export async function listUsers() {
  return request('/users');
}

export async function createUser(payload) {
  return request('/users', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
