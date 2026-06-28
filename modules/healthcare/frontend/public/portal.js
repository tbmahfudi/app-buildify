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
      const res = await fetch(`${API_BASE}/api/v1/clinics/${tenantCode}`);
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
      const res = await fetch(`${API_BASE}/api/v1/clinics/${tenantCode}/branches/${branchCode}`);
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
        fetch(`${API_BASE}/api/v1/patients/me/records`, { headers }),
      ]);
      if (profileRes.status === 401 || profileRes.status === 403) {
        logout(); return;
      }
      const profile = await profileRes.json();
      document.getElementById('patient-profile-info').innerHTML = `<p class="small mb-1">📞 ${profile.phone}</p>`;

      loadAppointments();

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

﻿  // -- Appointment booking --------------------------------------------------

  let selectedSlot = null;
  let selectedBranchCode = null;

  window.showBookingPage = async function () {
    if (!patientToken) { showPage('login'); return; }
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
        `<option value="${b.code || b.id}">${b.name}</option>`
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
      const slots = data.slots || [];

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

  // ── Init ──────────────────────────────────────────────────────────────────────
  updateNavAuth();
  if (patientToken) {
    showPage('dashboard');
  } else {
    loadClinicInfo();
  }

})();
