/**
 * T-HC-025 — Clinic discovery / search page
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

let currentPage = 1;
let totalPages  = 1;

// ── render ────────────────────────────────────────────────────────────────────

function renderSkeletons(count = 4) {
  const grid = document.getElementById('clinic-grid');
  grid.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const div = document.createElement('div');
    div.className = 'hc-skeleton hc-skeleton-card';
    grid.appendChild(div);
  }
}

function renderResults(clinics) {
  const grid = document.getElementById('clinic-grid');
  grid.innerHTML = '';

  if (!clinics || clinics.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'hc-empty';
    empty.textContent = t('clinics.empty');
    grid.appendChild(empty);
    return;
  }

  clinics.forEach((clinic) => {
    const card = document.createElement('article');
    card.className = 'hc-clinic-card';

    const stars = '★'.repeat(Math.round(clinic.rating || 0)) + '☆'.repeat(5 - Math.round(clinic.rating || 0));

    card.innerHTML = `
      <div class="hc-clinic-card__name">${escHtml(clinic.name)}</div>
      <div class="hc-clinic-card__tags">${(clinic.specialties || []).map((s) => `<span class="hc-tag">${escHtml(s)}</span>`).join('')}</div>
      <div class="hc-clinic-card__meta">${escHtml(clinic.city || '')}</div>
      <div class="hc-clinic-card__rating">${stars} <span>${(clinic.rating || 0).toFixed(1)}</span></div>
      <div class="hc-clinic-card__footer">
        <a class="hc-clinic-card__book" href="/clinics/${escHtml(clinic.slug)}">${t('clinics.card.book')}</a>
      </div>
    `;

    grid.appendChild(card);
  });
}

function renderPagination() {
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) { pag.style.display = 'none'; return; }
  pag.style.display = 'flex';
  document.getElementById('btn-prev').disabled = currentPage <= 1;
  document.getElementById('btn-next').disabled = currentPage >= totalPages;
  document.getElementById('page-label').textContent =
    t('common.pageOf', { current: currentPage, total: totalPages });
}

// ── fetch ─────────────────────────────────────────────────────────────────────

async function fetchClinics(page = 1) {
  const q         = document.getElementById('q').value.trim();
  const specialty = document.getElementById('specialty-filter').value;
  const city      = document.getElementById('city-filter').value.trim();

  renderSkeletons();
  document.getElementById('pagination').style.display = 'none';

  const params = new URLSearchParams({ page, limit: 10 });
  if (q)         params.set('q', q);
  if (specialty) params.set('specialty', specialty);
  if (city)      params.set('city', city);

  try {
    const data = await window.apiFetch('GET', `/api/v1/clinics/search?${params}`);
    currentPage = data.page  || 1;
    totalPages  = data.pages || 1;
    renderResults(data.clinics || []);
    renderPagination();
  } catch (err) {
    document.getElementById('clinic-grid').innerHTML =
      `<div class="hc-empty">${t('error.fetchFailed')}</div>`;
    console.error('Clinic search failed', err);
  }
}

// ── utils ─────────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n();
  translateDOM(document);

  // Set placeholders after translations loaded
  document.getElementById('q').placeholder               = t('clinics.search.placeholder');
  document.getElementById('city-filter').placeholder     = t('clinics.search.cityPlaceholder');

  document.getElementById('search-form').addEventListener('submit', (e) => {
    e.preventDefault();
    currentPage = 1;
    fetchClinics(1);
  });

  document.getElementById('btn-prev').addEventListener('click', () => {
    if (currentPage > 1) fetchClinics(currentPage - 1);
  });

  document.getElementById('btn-next').addEventListener('click', () => {
    if (currentPage < totalPages) fetchClinics(currentPage + 1);
  });

  // Initial load
  fetchClinics(1);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
