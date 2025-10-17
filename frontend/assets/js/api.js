const normalizeBase = (value) => {
  if (!value) return '/api';
  return value.endsWith('/') ? value.replace(/\/+$/, '') : value;
};

const deriveApiBase = () => {
  if (typeof window !== 'undefined') {
    if (window.APP_CONFIG?.apiBase) {
      return normalizeBase(window.APP_CONFIG.apiBase);
    }

    const metaBase = document.querySelector('meta[name="api-base"]')?.content;
    if (metaBase) {
      return normalizeBase(metaBase);
    }

    const { protocol, hostname } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:8000/api`;
    }
  }

  return '/api';
};

const API_BASE = deriveApiBase();
let tokens = { access: null, refresh: null };
let tenantId = null;

const withBase = (path) => {
  const safePath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${safePath}`;
};

function loadTokens() {
  try {
    const t = JSON.parse(localStorage.getItem("tokens"));
    if (t) tokens = t;
    tenantId = localStorage.getItem("tenantId") || null;
  } catch {}
}
function saveTokens() {
  localStorage.setItem("tokens", JSON.stringify(tokens));
}
function setTenant(id) {
  tenantId = id || null;
  if (tenantId) localStorage.setItem("tenantId", tenantId);
  else localStorage.removeItem("tenantId");
}
async function apiFetch(path, opts = {}) {
  const headers = opts.headers ? { ...opts.headers } : {};
  if (tokens.access) headers["Authorization"] = `Bearer ${tokens.access}`;
  if (tenantId) headers["X-Tenant-Id"] = tenantId;
  const res = await fetch(withBase(path), { ...opts, headers });
  if (res.status === 401 && tokens.refresh) {
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
      return apiFetch(path, opts); // retry
    }
  }
  return res;
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
  tokens = { access: null, refresh: null };
  saveTokens();
}
loadTokens();
export { apiFetch, login, logout, tokens, setTenant, tenantId };
