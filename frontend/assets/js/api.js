const API_BASE = "/api";
let tokens = { access: null, refresh: null };
let tenantId = null;

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
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (res.status === 401 && tokens.refresh) {
    const r = await fetch(`${API_BASE}/auth/refresh`, {
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
  const res = await fetch(`${API_BASE}/auth/login`, {
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
