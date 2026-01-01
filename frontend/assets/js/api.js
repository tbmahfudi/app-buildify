const normalizeBase = (value) => {
  if (!value) return '/api/v1';
  return value.endsWith('/') ? value.replace(/\/+$/, '') : value;
};

const deriveApiBase = () => {
  if (typeof window !== 'undefined') {
    if (window.APP_CONFIG?.apiBase) {
      return normalizeBase(window.APP_CONFIG.apiBase);
    }
  }

  // Use relative URLs for all environments to match 'self' in CSP
  return '/api/v1';
};

let apiBase = deriveApiBase();
let tokens = { access: null, refresh: null };
let tenantId = null;

// SECURITY NOTE: Token storage in localStorage is vulnerable to XSS attacks.
// RECOMMENDED: Backend should implement httpOnly cookies for token storage.
// This would prevent JavaScript access to tokens entirely.
// Until then, we use localStorage with additional protections.

const withBase = (path) => {
  const safePath = path.startsWith('/') ? path : `/${path}`;
  return `${apiBase}${safePath}`;
};

function loadTokens() {
  try {
    const t = JSON.parse(localStorage.getItem("tokens"));
    if (t) {
      // Validate token structure before accepting
      if (t.access && typeof t.access === 'string' &&
          t.refresh && typeof t.refresh === 'string') {
        tokens = t;
        console.log('[API] Tokens loaded from localStorage');
      } else {
        // Invalid token structure, clear it
        console.warn('Invalid token structure detected, clearing tokens');
        clearTokens();
      }
    } else {
      console.warn('[API] No tokens found in localStorage');
    }
    tenantId = localStorage.getItem("tenantId") || null;
    if (tenantId) {
      console.log('[API] Tenant ID loaded:', tenantId);
    }
  } catch (error) {
    console.error('Error loading tokens:', error);
    clearTokens();
  }
}

function saveTokens() {
  if (!tokens.access || !tokens.refresh) {
    console.warn('Attempted to save invalid tokens');
    return;
  }
  try {
    localStorage.setItem("tokens", JSON.stringify(tokens));
  } catch (error) {
    console.error('Error saving tokens:', error);
  }
}

function clearTokens() {
  localStorage.removeItem("tokens");
  localStorage.removeItem("tenantId");
  tokens = { access: null, refresh: null };
  tenantId = null;
}
function setTenant(id) {
  tenantId = id || null;
  if (tenantId) localStorage.setItem("tenantId", tenantId);
  else localStorage.removeItem("tenantId");
}
async function apiFetch(path, opts = {}) {
  const headers = opts.headers ? { ...opts.headers } : {};
  if (tokens.access) {
    headers["Authorization"] = `Bearer ${tokens.access}`;
    console.log(`[API] Request to ${path} with auth token`);
  } else {
    console.warn(`[API] Request to ${path} WITHOUT auth token!`);
  }
  if (tenantId) headers["X-Tenant-Id"] = tenantId;

  // Automatically set Content-Type for requests with a body
  if (opts.body && typeof opts.body === 'string' && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(withBase(path), { ...opts, headers });

  if (res.status === 401 && tokens.refresh) {
    console.log('[API] Received 401, attempting token refresh...');
    const r = await fetch(withBase('/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refresh })
    });
    if (r.ok) {
      const j = await r.json();
      tokens.access = j.access_token;
      tokens.refresh = j.refresh_token;
      saveTokens();
      console.log('[API] Token refreshed successfully, retrying request');
      return apiFetch(path, opts); // retry
    } else {
      console.error('[API] Token refresh failed:', r.status, await r.text());
    }
  } else if (res.status === 401) {
    console.error('[API] Received 401 but no refresh token available');
  }

  return res;
}

function setApiBase(base) {
  apiBase = normalizeBase(base);
}
async function login(email, password, tenant) {
  const res = await fetch(withBase('/auth/login'), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(tenant ? {"X-Tenant-Id": tenant} : {}) },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }
  const j = await res.json();
  tokens.access = j.access_token;
  tokens.refresh = j.refresh_token;
  saveTokens();
  setTenant(tenant || null);
  return j;
}
function logout() {
  clearTokens();
}

/**
 * Get the current access token
 * @returns {string|null} The access token or null if not available
 */
function getAuthToken() {
  return tokens.access;
}

loadTokens();
export { apiFetch, login, logout, tokens, setTenant, tenantId, setApiBase, getAuthToken };
