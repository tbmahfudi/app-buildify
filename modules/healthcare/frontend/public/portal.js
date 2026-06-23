// Healthcare Public Portal — SPA Logic
(function () {
  'use strict';

  // ── Config ──────────────────────────────────────────────────────────────────
  const API_BASE = '';  // same origin
  const CONSENT_VERSION = '1.0';
  const CONSENT_TEXT = 'I agree to allow this clinic to store and process my personal health information in accordance with applicable data protection laws.';

  // Derive tenant code from query param ?clinic=X or default to 'medcare'
  const params = new URLSearchParams(window.location.search);
  let tenantCode = params.get('clinic') || 'medcare';

  // ── State ───────────────────────────────────────────────────────────────────
  let patientToken = localStorage.getItem('hc_patient_token');
  let otpTokenCache = {};  // { 'register': '<uuid>', 'login': '<uuid>' }

  // ── Toast ───────────────────────────────────────────────────────────────────
  function toast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast align-items-center text-bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0 show mb-2`;
    el.setAttribute('role', 'alert');
    el.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  // ── Page router ─────────────────────────────────────────────────────────────
  window.showPage = function (name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const page = document.getElementById('page-' + name);
    if (page) page.classList.add('active');
    if (name === 'dashboard') loadDashboard();
    if (name === 'home') loadClinicInfo();
  };

  // ── Nav auth area ────────────────────────────────────────────────────────────
  function updateNavAuth() {
    const area = document.getElementById('nav-auth-area');
    if (patientToken) {
      area.innerHTML = `<span class="text-muted small me-2">Logged in</span><button class="btn btn-outline-secondary btn-sm" onclick="logout()">Logout</button><button class="btn btn-primary btn-sm ms-1" onclick="showPage('dashboard')">My Account</button>`;
    } else {
      area.innerHTML = `<button class="btn btn-outline-primary btn-sm" onclick="showPage('login')">Login</button><button class="btn btn-primary btn-sm ms-1" onclick="showPage('register')">Register</button>`;
    }
  }

  // ── Clinic info ──────────────────────────────────────────────────────────────
  async function loadClinicInfo() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/public/clinics/${tenantCode}`);
      if (!res.ok) throw new Error('Clinic not found');
      const data = await res.json();
      document.getElementById('clinic-name').textContent = data.name;
      document.getElementById('clinic-code').textContent = `Clinic code: ${data.code}`;
      renderBranches(data.branches || []);
    } catch (e) {
      toast('Could not load clinic info: ' + e.message, 'error');
    }
  }

  function renderBranches(branches) {
    const el = document.getElementById('branch-list');
    if (!branches.length) {
      el.innerHTML = '<p class="text-muted">No branches listed.</p>';
      return;
    }
    el.innerHTML = branches.map(b => `
      <div class="col-md-4">
        <div class="card clinic-card h-100" style="cursor:pointer" onclick="showBranch('${b.code || b.id}')">
          <div class="card-body">
            <h6 class="card-title">${b.name}</h6>
            <p class="card-text small text-muted">${b.city || ''}</p>
            <p class="card-text small">${b.address || ''}</p>
            ${b.online_booking ? '<span class="badge bg-success">Online Booking</span>' : ''}
          </div>
        </div>
      </div>
    `).join('');
  }

  window.showBranch = async function (branchCode) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/public/clinics/${tenantCode}/branches/${branchCode}`);
      if (!res.ok) throw new Error('Branch not found');
      const b = await res.json();
      document.getElementById('branch-detail').innerHTML = `
        <h3>${b.name}</h3>
        <p class="text-muted">${b.city || ''} ${b.address || ''}</p>
        ${b.phone ? `<p>📞 ${b.phone}</p>` : ''}
        ${b.online_booking ? '<span class="badge bg-success mb-3">Online Booking Available</span>' : ''}
        <div class="mt-3">
          <button class="btn btn-primary me-2" onclick="showPage('register')">Register as Patient</button>
          <button class="btn btn-outline-primary" onclick="showPage('login')">Login</button>
        </div>
      `;
      showPage('branch');
    } catch (e) {
      toast('Could not load branch: ' + e.message, 'error');
    }
  };

  // ── OTP flow ─────────────────────────────────────────────────────────────────
  window.sendOtp = async function (flow) {
    const phoneEl = document.getElementById(flow === 'register' ? 'reg-phone' : 'login-phone');
    const phone = phoneEl.value.trim();
    if (!phone) { toast('Please enter your phone number', 'error'); return; }
    try {
      const res = await fetch(`${API_BASE}/api/v1/otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, purpose: flow === 'register' ? 'patient_registration' : 'patient_login', tenant_code: tenantCode }),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Failed to send OTP', 'error'); return; }
      toast('OTP sent! Check your phone.', 'success');
      if (flow === 'register') {
        document.getElementById('reg-phone-display').textContent = phone;
        document.getElementById('register-step-phone').style.display = 'none';
        document.getElementById('register-step-otp').style.display = 'block';
      } else {
        document.getElementById('login-phone-display').textContent = phone;
        document.getElementById('login-step-phone').style.display = 'none';
        document.getElementById('login-step-otp').style.display = 'block';
      }
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  window.verifyOtp = async function (flow) {
    const phoneEl = document.getElementById(flow === 'register' ? 'reg-phone' : 'login-phone');
    const otpEl = document.getElementById(flow === 'register' ? 'reg-otp' : 'login-otp');
    const phone = phoneEl.value.trim();
    const code = otpEl.value.trim();
    if (code.length !== 6) { toast('Enter the 6-digit code', 'error'); return; }
    try {
      const res = await fetch(`${API_BASE}/api/v1/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, purpose: flow === 'register' ? 'patient_registration' : 'patient_login', tenant_code: tenantCode, code }),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Invalid OTP', 'error'); return; }
      otpTokenCache[flow] = data.otp_token;
      toast('Phone verified!', 'success');
      if (flow === 'register') {
        document.getElementById('register-step-details').style.display = 'block';
        document.getElementById('register-form-actions').style.display = 'block';
      }
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  // ── Registration ─────────────────────────────────────────────────────────────
  window.submitRegister = async function () {
    const otp_token = otpTokenCache['register'];
    if (!otp_token) { toast('Please verify your OTP first', 'error'); return; }
    const full_name = document.getElementById('reg-name').value.trim();
    if (!full_name) { toast('Please enter your full name', 'error'); return; }
    if (!document.getElementById('reg-consent').checked) { toast('Please accept the consent terms', 'error'); return; }

    const consent_text_hash = await sha256(CONSENT_TEXT);
    const body = {
      otp_token,
      full_name,
      consent_version: CONSENT_VERSION,
      consent_text_hash,
      locale: navigator.language || 'id-ID',
      date_of_birth: document.getElementById('reg-dob').value || null,
      gender: document.getElementById('reg-gender').value || null,
    };

    try {
      const res = await fetch(`${API_BASE}/api/v1/public/clinics/${tenantCode}/patients/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Registration failed', 'error'); return; }
      localStorage.setItem('hc_patient_token', data.access_token);
      patientToken = data.access_token;
      toast('Welcome! Account created.', 'success');
      updateNavAuth();
      showPage('dashboard');
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  // ── Login ────────────────────────────────────────────────────────────────────
  window.submitLogin = async function () {
    const phone = document.getElementById('login-phone').value.trim();
    const code = document.getElementById('login-otp').value.trim();
    if (code.length !== 6) { toast('Enter the 6-digit code', 'error'); return; }

    // Verify OTP first to get token
    try {
      const verifyRes = await fetch(`${API_BASE}/api/v1/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, purpose: 'patient_login', tenant_code: tenantCode, code }),
      });
      const verifyData = await verifyRes.json();
      if (!verifyRes.ok) { toast(verifyData.detail || 'Invalid OTP', 'error'); return; }

      const res = await fetch(`${API_BASE}/api/v1/public/clinics/${tenantCode}/patients/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ otp_token: verifyData.otp_token }),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Login failed', 'error'); return; }
      localStorage.setItem('hc_patient_token', data.access_token);
      patientToken = data.access_token;
      toast('Welcome back!', 'success');
      updateNavAuth();
      showPage('dashboard');
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  // ── Dashboard ─────────────────────────────────────────────────────────────────
  async function loadDashboard() {
    if (!patientToken) { showPage('login'); return; }
    const headers = { 'Authorization': `Bearer ${patientToken}` };
    try {
      const [profileRes, apptRes, recRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/patients/me/profile`, { headers }),
        fetch(`${API_BASE}/api/v1/patients/me/appointments`, { headers }),
        fetch(`${API_BASE}/api/v1/patients/me/records`, { headers }),
      ]);
      if (profileRes.status === 401 || profileRes.status === 403) {
        logout(); return;
      }
      const profile = await profileRes.json();
      document.getElementById('patient-profile-info').innerHTML = `<p class="small mb-1">📞 ${profile.phone}</p>`;

      const appt = await apptRes.json();
      document.getElementById('patient-appointments').innerHTML = appt.appointments?.length
        ? appt.appointments.map(a => `<p class="small">${a.date} — ${a.type}</p>`).join('')
        : `<p class="text-muted small">${appt.note || 'No appointments'}</p>`;

      const rec = await recRes.json();
      document.getElementById('patient-records').innerHTML = rec.records?.length
        ? rec.records.map(r => `<p class="small">${r.date} — ${r.summary}</p>`).join('')
        : `<p class="text-muted small">${rec.note || 'No records'}</p>`;
    } catch (e) {
      toast('Could not load dashboard', 'error');
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────────
  window.logout = function () {
    localStorage.removeItem('hc_patient_token');
    patientToken = null;
    updateNavAuth();
    showPage('home');
    toast('Logged out', 'info');
  };

  // ── SHA-256 helper ────────────────────────────────────────────────────────────
  async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // ── Init ──────────────────────────────────────────────────────────────────────
  updateNavAuth();
  if (patientToken) {
    showPage('dashboard');
  } else {
    loadClinicInfo();
  }

})();
