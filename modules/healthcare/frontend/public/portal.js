// Healthcare Public Portal — SPA Logic
(function () {
  'use strict';

  // ── Config ──────────────────────────────────────────────────────────────────
  const API_BASE = '';  // same origin
  const CONSENT_VERSION = '1.0';
  const CONSENT_TEXT = 'I agree to allow this clinic to store and process my personal health information in accordance with applicable data protection laws.';

  // Password is the primary patient login (ADR-HC-009). OTP is optional and OFF
  // by default — mirror of the backend HC_PATIENT_OTP_ENABLED flag. The server
  // enforces (OTP endpoints 403 when disabled); this only hides the OTP UI.
  const OTP_LOGIN_ENABLED = false;

  // Derive the clinic (Company) slug from ?company=X (ADR-HC-010 D6) or legacy ?clinic=X.
  // No hardcoded default — a logged-out visitor with no selection gets the clinic chooser
  // (epic-20 20.4) instead of an arbitrary single clinic.
  const params = new URLSearchParams(window.location.search);
  let tenantCode = params.get('company') || params.get('clinic') || null;

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
    if (name === 'household') loadHouseholdPage();
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

  // ── Clinic chooser (logged-out landing, epic-20 20.4) ───────────────────────
  function escHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  let _chooserClinics = [];

  async function loadChooser() {
    showPage('chooser');
    const el = document.getElementById('chooser-list');
    el.innerHTML = '<p class="text-muted">Loading clinics…</p>';
    try {
      const res = await fetch(`${API_BASE}/api/v1/clinics`);
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      _chooserClinics = data.clinics || [];
      renderChooser(_chooserClinics);
    } catch (e) {
      el.innerHTML = '<p class="text-danger">Could not load clinics. Please try again later.</p>';
    }
  }

  function renderChooser(clinics) {
    const el = document.getElementById('chooser-list');
    if (!clinics.length) {
      el.innerHTML = '<p class="text-muted">No clinics are listed yet.</p>';
      return;
    }
    el.innerHTML = clinics.map(c => `
      <div class="col-md-4">
        <div class="card clinic-card h-100" style="cursor:pointer" onclick="selectClinic('${escHtml(c.slug)}')">
          <div class="card-body">
            <h5 class="card-title mb-1">${escHtml(c.clinic_name)}</h5>
            <p class="text-muted small mb-2">${escHtml(c.city || '')}</p>
            <p class="mb-0 small">${(c.branches || []).length} site(s)</p>
          </div>
        </div>
      </div>`).join('');
  }

  window.filterChooser = function () {
    const q = (document.getElementById('chooser-search').value || '').toLowerCase();
    renderChooser(_chooserClinics.filter(c =>
      (c.clinic_name || '').toLowerCase().includes(q) || (c.city || '').toLowerCase().includes(q)));
  };

  // Enter the selected clinic's portal by pinning ?company=<slug> and reloading.
  window.selectClinic = function (slug) {
    const u = new URL(window.location.href);
    u.searchParams.set('company', slug);
    u.searchParams.delete('clinic');
    window.location.href = u.toString();
  };

  // ── Clinic info ──────────────────────────────────────────────────────────────
  async function loadClinicInfo() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/clinics/${tenantCode}`);
      if (!res.ok) throw new Error('Clinic not found');
      const data = await res.json();
      document.getElementById('clinic-name').textContent = data.clinic_name || data.name || 'Clinic';
      document.getElementById('clinic-code').textContent = data.city ? data.city : '';
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
        <div class="card clinic-card h-100" style="cursor:pointer" onclick="showBranch('${b.branch_id || b.code || b.id}')">
          <div class="card-body">
            <h6 class="card-title">${b.branch_name || b.name || ''}</h6>
            <p class="card-text small text-muted">${b.address_city || b.city || ''}</p>
            <p class="card-text small">${b.address_street || b.address || ''}</p>
            ${b.online_booking ? '<span class="badge bg-success">Online Booking</span>' : ''}
          </div>
        </div>
      </div>
    `).join('');
  }

  window.showBranch = async function (branchCode) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/clinics/${tenantCode}/branches/${branchCode}`);
      if (!res.ok) throw new Error('Branch not found');
      const b = await res.json();
      document.getElementById('branch-detail').innerHTML = `
        <h3>${b.branch_name || b.name || ''}</h3>
        <p class="text-muted">${b.address_city || b.city || ''} ${b.address_street || b.address || ''}</p>
        ${(b.contact_phone || b.phone) ? `<p>📞 ${b.contact_phone || b.phone}</p>` : ''}
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
      const res = await fetch(`${API_BASE}/api/v1/patients/auth/otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
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
      const res = await fetch(`${API_BASE}/api/v1/patients/auth/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Invalid OTP', 'error'); return; }
      otpTokenCache[flow] = true;
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
    if (!otpTokenCache['register']) { toast('Please verify your OTP first', 'error'); return; }
    const phone = document.getElementById('reg-phone').value.trim();
    const full_name = document.getElementById('reg-name').value.trim();
    if (!full_name) { toast('Please enter your full name', 'error'); return; }
    if (!document.getElementById('reg-consent').checked) { toast('Please accept the consent terms', 'error'); return; }

    const body = {
      phone,
      full_name,
      date_of_birth: document.getElementById('reg-dob').value || '',
      gender: document.getElementById('reg-gender').value || '',
      consent_accepted: true,
      consent_version: CONSENT_VERSION,
    };

    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/register`, {
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

    // Phone + OTP -> patient access token in one call
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
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
      const [profileRes, recRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/patients/me/profile`, { headers }),
        fetch(`${API_BASE}/api/v1/patients/me/encounters`, { headers }),
      ]);
      if (profileRes.status === 401 || profileRes.status === 403) {
        logout(); return;
      }
      const profile = await profileRes.json();
      const name = profile.full_name ? `<span class="fw-semibold">${profile.full_name}</span><br>` : '';
      document.getElementById('patient-profile-info').innerHTML =
        `<p class="small mb-1">${name}📞 ${profile.masked_phone || '—'}</p>`;

      loadAppointments();
      loadHouseholdSummary();

      const rec = await recRes.json();
      const items = (rec && rec.items) || [];
      document.getElementById('patient-records').innerHTML = items.length
        ? items.map(r => {
            const d = new Date(r.encounter_date).toLocaleDateString();
            return `<p class="small mb-1">${d} — ${r.summary || r.encounter_type || 'Visit'}</p>`;
          }).join('')
        : `<p class="text-muted small">No records</p>`;
    } catch (e) {
      toast('Could not load dashboard', 'error');
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────────
  window.logout = function () {
    // Clear the portal (patient) session AND the platform session that bridged
    // the patient in. Patients authenticate via the staff login and are exchanged
    // into a patient token; if the platform token is left behind, returning to the
    // app root silently re-logs them in via the platform→patient bridge, so logout
    // appears not to work.
    localStorage.removeItem('hc_patient_token');
    localStorage.removeItem('tokens');
    localStorage.removeItem('user');
    patientToken = null;
    otpTokenCache = {};
    // Hard-navigate to a clean portal home so no in-memory state (or a re-entrant
    // bridge) survives the logout.
    window.location.href = '/portal/healthcare/';
  };

  // ── SHA-256 helper ────────────────────────────────────────────────────────────
  async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

﻿  // -- Appointment booking --------------------------------------------------

  let selectedSlot = null;
  let selectedBranchCode = null;

  // Point clinic-facing views at the logged-in patient's OWN clinic (their
  // tenant), overriding the ?clinic= URL default (which is not clinic-specific
  // for a bridged/password login).
  async function ensurePatientClinic() {
    if (!patientToken) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/clinic`, {
        headers: { 'Authorization': `Bearer ${patientToken}` },
      });
      if (res.ok) {
        const d = await res.json();
        if (d && d.slug) tenantCode = d.slug;
      }
    } catch (e) { /* keep existing tenantCode */ }
  }

  window.showBookingPage = async function () {
    if (!patientToken) { showPage('login'); return; }
    await ensurePatientClinic();
    showPage('book');
    await populateBranchDropdown();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('book-date').value = tomorrow.toISOString().split('T')[0];
    loadSlots();
  };

  async function populateBranchDropdown() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/clinics/${tenantCode}`);
      const data = await res.json();
      const sel = document.getElementById('book-branch');
      sel.innerHTML = (data.branches || []).map(b =>
        `<option value="${b.branch_id || b.code || b.id}">${b.branch_name || b.name || ''}</option>`
      ).join('');
      selectedBranchCode = sel.value;
    } catch (e) {
      toast('Could not load branches', 'error');
    }
  }

  window.loadSlots = async function () {
    const branchCode = document.getElementById('book-branch').value;
    const date = document.getElementById('book-date').value;
    selectedBranchCode = branchCode;
    if (!branchCode || !date) return;

    const container = document.getElementById('slots-container');
    container.innerHTML = '<p class="text-muted small">Loading slots...</p>';
    document.getElementById('booking-confirm').style.display = 'none';
    selectedSlot = null;

    try {
      const res = await fetch(
        `${API_BASE}/api/v1/public/clinics/${tenantCode}/branches/${branchCode}/slots?date=${date}`
      );
      if (!res.ok) throw new Error('Could not load slots');
      const data = await res.json();
      const slots = Array.isArray(data) ? data : (data.slots || []);

      if (!slots.length) {
        container.innerHTML = '<p class="text-muted">No available slots for this date.</p>';
        return;
      }

      container.innerHTML = slots.map(s => `
        <div class="col-6 col-md-3">
          <div class="card slot-card ${s.available ? '' : 'opacity-50'} clinic-card"
               style="cursor:${s.available ? 'pointer' : 'default'}"
               onclick="${s.available ? `selectSlot('${s.id}','${s.time}','${s.provider_name}','${s.provider_specialty}')` : ''}">
            <div class="card-body p-2 text-center">
              <div class="fw-bold">${s.time}</div>
              <div class="small text-muted">${s.provider_name}</div>
              <div class="small text-muted fst-italic">${s.provider_specialty || ''}</div>
              ${s.available ? '' : '<span class="badge bg-secondary mt-1">Booked</span>'}
            </div>
          </div>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = '<p class="text-danger small">Failed to load slots. Please try again.</p>';
    }
  };

  window.selectSlot = function (slotId, time, providerName, specialty) {
    selectedSlot = { id: slotId, time, providerName, specialty };
    document.getElementById('booking-summary').innerHTML =
      `<strong>${time}</strong> with ${providerName} (${specialty || 'General'})`;
    document.getElementById('booking-confirm').style.display = 'block';
    document.querySelectorAll('.slot-card').forEach(c => c.classList.remove('border-primary'));
    event.currentTarget.classList.add('border-primary');
  };

  window.cancelBookingSelection = function () {
    selectedSlot = null;
    document.getElementById('booking-confirm').style.display = 'none';
  };

  window.confirmBooking = async function () {
    if (!selectedSlot) return;
    const notes = document.getElementById('booking-notes').value.trim();
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${patientToken}`,
        },
        body: JSON.stringify({
          slot_id: selectedSlot.id,
          branch_code: selectedBranchCode,
          notes,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast(data.detail || 'Booking failed', 'error');
        return;
      }
      toast('Appointment booked!', 'success');
      selectedSlot = null;
      showPage('dashboard');
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  // -- Enhanced appointment list in dashboard --------------------------------

  async function loadAppointments() {
    if (!patientToken) return;
    const el = document.getElementById('patient-appointments');
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/appointments`, {
        headers: { 'Authorization': `Bearer ${patientToken}` },
      });
      const data = await res.json();
      const appts = data.appointments || [];
      if (!appts.length) {
        el.innerHTML = `<p class="text-muted small">No appointments yet.</p>
          <button class="btn btn-sm btn-outline-primary mt-1" onclick="showBookingPage()">Book Now</button>`;
        return;
      }
      el.innerHTML = appts.map(a => `
        <div class="d-flex justify-content-between align-items-start mb-2 border-bottom pb-1">
          <div>
            <div class="small fw-semibold">${new Date(a.slot_time).toLocaleString()}</div>
            <div class="small text-muted">${a.provider_name} &middot; ${a.branch_name}</div>
            <span class="badge ${a.status === 'confirmed' ? 'bg-success' : 'bg-secondary'}">${a.status}</span>
          </div>
          ${a.status === 'confirmed'
            ? `<button class="btn btn-outline-danger btn-sm" onclick="cancelAppointment('${a.id}')">Cancel</button>`
            : ''}
        </div>
      `).join('') + `<button class="btn btn-sm btn-outline-primary mt-2" onclick="showBookingPage()">Book Another</button>`;
    } catch (e) {
      el.innerHTML = '<p class="text-muted small">Could not load appointments.</p>';
    }
  }

  window.cancelAppointment = async function (id) {
    if (!confirm('Cancel this appointment?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/appointments/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${patientToken}` },
      });
      if (res.ok || res.status === 204) {
        toast('Appointment cancelled', 'info');
        loadDashboard();
      } else {
        toast('Could not cancel', 'error');
      }
    } catch (e) {
      toast('Network error', 'error');
    }
  };

  // ── Email/username + password login (ADR-HC-009) ─────────────────────────────
  // Authenticate against the platform, then exchange the platform token for a
  // patient portal session at the from-platform bridge.
  window.submitPasswordLogin = async function () {
    const identifier = document.getElementById('login-identifier').value.trim();
    const password = document.getElementById('login-password').value;
    if (!identifier || !password) { toast('Enter your email/username and password', 'error'); return; }
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: identifier, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        const d = data.detail;
        // ADR-HC-009 D7: a legacy/backfilled account must set a password first.
        if (d && typeof d === 'object' && d.code === 'must_set_password') {
          await startPasswordClaim(identifier);
          return;
        }
        toast((d && (d.message || (typeof d === 'string' ? d : null))) || 'Login failed', 'error');
        return;
      }
      const br = await fetch(`${API_BASE}/api/v1/patients/auth/from-platform`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${data.access_token}` },
      });
      const bdata = await br.json();
      if (!br.ok) { toast(bdata.detail || 'No patient profile is linked to this account.', 'error'); return; }
      localStorage.setItem('hc_patient_token', bdata.access_token);
      patientToken = bdata.access_token;
      toast('Welcome back!', 'success');
      updateNavAuth();
      showPage('dashboard');
    } catch (e) { toast('Network error', 'error'); }
  };

  // ── Household / Family ────────────────────────────────────────────────────────
  const REL_LABEL = { self: 'You', spouse: 'Spouse', child: 'Child', parent: 'Parent', other: 'Family' };
  const REL_BASIS = { child: 'parental_guardian', spouse: 'spousal', parent: 'delegated_adult', other: 'delegated_adult' };

  async function fetchHousehold() {
    const res = await fetch(`${API_BASE}/api/v1/patients/me/household`, {
      headers: { 'Authorization': `Bearer ${patientToken}` },
    });
    return { ok: res.ok, status: res.status, data: await res.json().catch(() => ({})) };
  }

  async function loadHouseholdSummary() {
    const el = document.getElementById('patient-household');
    if (!el) return;
    try {
      const r = await fetchHousehold();
      if (!r.ok) { el.innerHTML = '<p class="text-muted small">Log in with an account to manage family members.</p>'; return; }
      const members = r.data.members || [];
      const active = members.find(m => m.is_active);
      const onBehalf = active && active.relationship && active.relationship !== 'self';
      el.innerHTML =
        (onBehalf ? `<p class="small mb-1"><span class="badge bg-warning text-dark">Acting for</span> ${active.full_name}</p>` : '') +
        `<p class="small text-muted mb-0">${members.length} member${members.length === 1 ? '' : 's'} in your household</p>`;
    } catch (e) { el.innerHTML = '<p class="text-muted small">Could not load family.</p>'; }
  }

  async function loadHouseholdPage() {
    if (!patientToken) { showPage('login'); return; }
    const box = document.getElementById('household-members');
    try {
      const r = await fetchHousehold();
      if (!r.ok) {
        box.innerHTML = `<div class="col"><div class="alert alert-info small mb-0">${r.data.detail || 'Family management requires an account login (email/username + password).'}</div></div>`;
        return;
      }
      const members = r.data.members || [];
      box.innerHTML = members.map(m => {
        const rel = REL_LABEL[m.relationship] || m.relationship;
        const badge = m.is_active ? '<span class="badge bg-primary ms-1">Active</span>' : '';
        const btn = m.is_active ? ''
          : `<button class="btn btn-sm btn-outline-primary" onclick="switchPatient('${m.patient_id}')">Switch to</button>`;
        return `<div class="col-md-6"><div class="card clinic-card h-100"><div class="card-body d-flex justify-content-between align-items-center">
            <div><div class="fw-semibold">${m.full_name || ''}${badge}</div><div class="small text-muted">${rel}</div></div>${btn}
          </div></div></div>`;
      }).join('') || '<div class="col"><p class="text-muted small">No family members yet.</p></div>';
    } catch (e) { box.innerHTML = '<div class="col"><p class="text-danger small">Could not load family.</p></div>'; }
  }

  window.switchPatient = async function (patientId) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/auth/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${patientToken}` },
        body: JSON.stringify({ patient_id: patientId }),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Could not switch', 'error'); return; }
      localStorage.setItem('hc_patient_token', data.access_token);
      patientToken = data.access_token;
      toast('Switched patient.', 'success');
      showPage('dashboard');
    } catch (e) { toast('Network error', 'error'); }
  };

  window.addDependent = async function () {
    const relationship = document.getElementById('dep-rel').value;
    const body = {
      full_name: document.getElementById('dep-name').value.trim(),
      date_of_birth: document.getElementById('dep-dob').value,
      phone: document.getElementById('dep-phone').value.trim(),
      gender: document.getElementById('dep-gender').value,
      relationship: relationship,
      basis: REL_BASIS[relationship] || 'delegated_adult',
      consent_version: CONSENT_VERSION,
      consent_accepted: document.getElementById('dep-consent').checked,
    };
    if (!body.full_name || !body.date_of_birth || !body.phone) { toast('Please fill name, date of birth and phone', 'error'); return; }
    if (!body.consent_accepted) { toast('Please accept the consent', 'error'); return; }
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/household/dependents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${patientToken}` },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Could not register', 'error'); return; }
      toast('Family member registered.', 'success');
      ['dep-name', 'dep-dob', 'dep-phone'].forEach(id => document.getElementById(id).value = '');
      document.getElementById('dep-consent').checked = false;
      loadHouseholdPage();
    } catch (e) { toast('Network error', 'error'); }
  };

  window.requestLink = async function () {
    const relationship = document.getElementById('link-rel').value;
    const body = {
      patient_id: document.getElementById('link-pid').value.trim(),
      branch_id: document.getElementById('link-branch').value.trim(),
      relationship: relationship,
      basis: REL_BASIS[relationship] || 'delegated_adult',
    };
    if (!body.patient_id || !body.branch_id) { toast('Enter the patient ID and clinic ID', 'error'); return; }
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/me/household/link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${patientToken}` },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { toast(data.detail || 'Could not send request', 'error'); return; }
      toast(data.message || 'Link request submitted for clinic approval.', 'success');
      ['link-pid', 'link-branch'].forEach(id => document.getElementById(id).value = '');
    } catch (e) { toast('Network error', 'error'); }
  };

  // ── Password claim (ADR-HC-009 D7) ────────────────────────────────────────────
  // A legacy/backfilled patient has a placeholder credential and must set a real
  // password before signing in. With OTP off, the claim runs through the platform
  // email password-reset. Phone-only accounts (no email) are directed to staff.
  async function startPasswordClaim(identifier) {
    if (identifier.includes('@')) {
      try {
        await fetch(`${API_BASE}/api/v1/auth/reset-password-request`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: identifier }),
        });
      } catch (_e) { /* non-fatal: response is intentionally uniform to avoid enumeration */ }
      toast('Set your password: check your email for a link to finish claiming your account.', 'info');
    } else {
      toast('This account still needs a password. Please claim it using your email address, or contact your clinic.', 'info');
    }
  }

  // Hide the OTP login UI unless OTP is enabled (server enforces regardless).
  function applyOtpVisibility() {
    if (OTP_LOGIN_ENABLED) return;
    ['login-step-phone', 'login-otp-divider'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────────────
  applyOtpVisibility();
  updateNavAuth();
  if (patientToken) {
    showPage('dashboard');
  } else if (tenantCode) {
    // A specific clinic was chosen via ?company= / ?clinic= — show its portal home.
    loadClinicInfo();
  } else {
    // Logged out with no clinic selected → the clinic chooser (epic-20 20.4),
    // instead of defaulting to an arbitrary single clinic.
    loadChooser();
  }

})();
