/**
 * T-HC-025 — Clinic public profile page
 * Route: /clinics/:slug
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

// ── slug from URL path ────────────────────────────────────────────────────────

function getSlug() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  return parts[parts.length - 1] || '';
}

// ── utils ─────────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function stars(rating, max = 5) {
  const n = Math.round(rating || 0);
  return '★'.repeat(n) + '☆'.repeat(max - n);
}

// ── render hero ───────────────────────────────────────────────────────────────

function renderHero(clinic) {
  const hero = document.getElementById('hero-content');
  hero.innerHTML = `
    <div>
      <div class="hc-hero__name">${escHtml(clinic.name)}</div>
      <div class="hc-hero__tags">
        ${(clinic.specialties || []).map((s) => `<span class="hc-tag">${escHtml(s)}</span>`).join('')}
      </div>
      <div class="hc-hero__meta">${escHtml(clinic.city || '')}</div>
      <div class="hc-hero__rating">${stars(clinic.rating)} ${(clinic.rating || 0).toFixed(1)}</div>
    </div>
    <div>
      <a class="hc-hero__cta" href="/book?clinic=${escHtml(clinic.slug)}">${t('clinicProfile.bookNow')}</a>
    </div>
  `;
}

// ── render tab panels ─────────────────────────────────────────────────────────

function renderInfo(clinic) {
  const panel = document.getElementById('tab-info');
  panel.innerHTML = `
    <div class="hc-info-section">
      <h3>${t('clinicProfile.info.description')}</h3>
      <p>${escHtml(clinic.description || '')}</p>
    </div>
    <div class="hc-info-section">
      <h3>${t('clinicProfile.info.hours')}</h3>
      <p>${escHtml(clinic.operating_hours || '')}</p>
    </div>
    <div class="hc-info-section">
      <h3>${t('clinicProfile.info.contact')}</h3>
      <p>${escHtml(clinic.phone || '')} ${clinic.email ? `&bull; ${escHtml(clinic.email)}` : ''}</p>
    </div>
  `;
}

function renderBranches(branches) {
  const panel = document.getElementById('tab-branches');
  if (!branches || branches.length === 0) {
    panel.innerHTML = `<p style="color:var(--color-text-secondary)">${t('clinicProfile.branches.empty')}</p>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'hc-branch-grid';

  branches.forEach((b) => {
    const card = document.createElement('div');
    card.className = 'hc-branch-card';
    card.innerHTML = `
      <div class="hc-branch-card__name">${escHtml(b.name)}</div>
      <div class="hc-branch-card__meta">${escHtml(b.address || '')}</div>
      <div class="hc-branch-card__meta">${escHtml(b.hours || '')}</div>
      ${b.online_booking ? `<span class="hc-online-badge">${t('clinicProfile.branches.onlineBooking')}</span>` : ''}
    `;
    grid.appendChild(card);
  });

  panel.innerHTML = '';
  panel.appendChild(grid);
}

function renderDoctors(doctors) {
  const panel = document.getElementById('tab-doctors');
  if (!doctors || doctors.length === 0) {
    panel.innerHTML = `<p style="color:var(--color-text-secondary)">${t('clinicProfile.doctors.empty')}</p>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'hc-doctor-grid';

  doctors.forEach((doc) => {
    const card = document.createElement('div');
    card.className = 'hc-doctor-card';
    // Only show name + specialty — no license per spec
    card.innerHTML = `
      <div class="hc-doctor-card__name">${escHtml(doc.name)}</div>
      <div class="hc-doctor-card__specialty">${escHtml(doc.specialty || '')}</div>
    `;
    grid.appendChild(card);
  });

  panel.innerHTML = '';
  panel.appendChild(grid);
}

function renderReviews(reviewData) {
  const panel = document.getElementById('tab-reviews');
  panel.innerHTML = '';

  // Star distribution
  if (reviewData.distribution) {
    const distEl = document.createElement('div');
    distEl.className = 'hc-star-dist';
    for (let star = 5; star >= 1; star--) {
      const count = reviewData.distribution[star] || 0;
      const pct   = reviewData.total ? Math.round((count / reviewData.total) * 100) : 0;
      const row   = document.createElement('div');
      row.className = 'hc-star-row';
      row.innerHTML = `
        <span>${star}★</span>
        <div class="hc-star-bar-bg"><div class="hc-star-bar-fill" style="width:${pct}%"></div></div>
        <span>${count}</span>
      `;
      distEl.appendChild(row);
    }
    panel.appendChild(distEl);
  }

  // Review list
  const list = document.createElement('div');
  list.className = 'hc-review-list';

  (reviewData.reviews || []).forEach((r) => {
    const rev = document.createElement('div');
    rev.className = 'hc-review';
    rev.innerHTML = `
      <div class="hc-review__header">
        <span class="hc-review__author">${escHtml(r.author || t('clinicProfile.reviews.anonymous'))}</span>
        <span class="hc-review__stars">${stars(r.rating)}</span>
      </div>
      <div class="hc-review__body">${escHtml(r.body || '')}</div>
    `;
    list.appendChild(rev);
  });

  if (list.children.length === 0) {
    list.innerHTML = `<p style="color:var(--color-text-secondary)">${t('clinicProfile.reviews.empty')}</p>`;
  }

  panel.appendChild(list);
}

// ── tabs ──────────────────────────────────────────────────────────────────────

function initTabs() {
  document.querySelectorAll('.hc-tab-nav__btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.hc-tab-nav__btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.hc-tab-panel').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
  });
}

// ── fetch ─────────────────────────────────────────────────────────────────────

async function fetchProfile() {
  const slug = getSlug();
  if (!slug) return;

  try {
    const data = await window.apiFetch('GET', `/api/v1/clinics/${slug}`);
    renderHero(data);
    renderInfo(data);
    renderBranches(data.branches || []);
    renderDoctors(data.doctors || []);
    renderReviews(data.reviews || {});
  } catch (err) {
    document.getElementById('hero-content').innerHTML =
      `<p style="color:var(--color-text-secondary)">${t('error.fetchFailed')}</p>`;
    console.error('Clinic profile fetch failed', err);
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n();
  translateDOM(document);
  initTabs();
  fetchProfile();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
