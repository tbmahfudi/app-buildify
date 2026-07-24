/**
 * DMS — Search page (E2).
 *
 * Full-text search over document filename/tags/metadata with filters (tag,
 * type, sort) and highlighted snippets. Results are ACL-filtered server-side.
 * Follows MODULE_FRONTEND_CONTRACT §4a (default export, instance render() into
 * #app-content).
 */

const SEARCH = '/api/v1/dms/search';
const SAVED = '/api/v1/dms/search/saved';
const DOCS = '/api/v1/dms/documents';

function authHeaders() {
    let token = null;
    try { token = (JSON.parse(localStorage.getItem('tokens') || 'null') || {}).access || null; } catch { /* */ }
    if (!token) token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

// Escape the snippet, then re-enable only our own <mark> tags (server-inserted).
function safeSnippet(s) {
    return esc(s).replace(/&lt;mark&gt;/g, '<mark>').replace(/&lt;\/mark&gt;/g, '</mark>');
}

function fmtBytes(n) {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(1)} ${u[i]}`;
}

export default class SearchPage {
    constructor() { this.name = 'dms-search'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        container.innerHTML = `
          <div style="padding:1.25rem 1.5rem;max-width:1000px;margin:0 auto;">
            <h2 style="margin:0 0 1rem;">Search documents</h2>
            <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-bottom:.5rem;">
              <input id="dms-q" placeholder="Search filename, tags, metadata…" style="flex:1;min-width:260px;padding:.5rem .7rem;border:1px solid var(--border-color,#cbd5e1);border-radius:6px;font:inherit;" />
              <button id="dms-go" style="padding:.5rem .9rem;border:1px solid #2563eb;background:#2563eb;color:#fff;border-radius:6px;cursor:pointer;">Search</button>
            </div>
            <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-bottom:1rem;font-size:.85rem;color:#475569;">
              <label>Tag <input id="dms-f-tag" style="padding:.3rem .5rem;border:1px solid #cbd5e1;border-radius:6px;width:120px;" /></label>
              <label>Type
                <select id="dms-f-type" style="padding:.3rem;border:1px solid #cbd5e1;border-radius:6px;">
                  <option value="">any</option>
                  <option value="application/pdf">PDF</option>
                  <option value="image/">Images</option>
                  <option value="text/">Text</option>
                  <option value="application/vnd">Office</option>
                </select></label>
              <label>Sort
                <select id="dms-f-sort" style="padding:.3rem;border:1px solid #cbd5e1;border-radius:6px;">
                  <option value="relevance">Relevance</option>
                  <option value="date">Newest</option>
                  <option value="name">Name</option>
                  <option value="size">Size</option>
                </select></label>
              <span style="flex:1;"></span>
              <button id="dms-save" title="Save current search" style="padding:.3rem .6rem;border:1px solid #cbd5e1;background:#fff;border-radius:6px;cursor:pointer;">☆ Save search</button>
            </div>
            <div id="dms-saved-list" style="margin-bottom:1rem;display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;"></div>
            <div id="dms-sr-status" style="color:#64748b;font-size:.85rem;margin-bottom:.5rem;"></div>
            <div id="dms-sr"></div>
          </div>
          <style>
            .dms-hit{border:1px solid #e2e8f0;border-radius:8px;padding:.7rem .9rem;margin-bottom:.6rem;}
            .dms-hit h4{margin:0 0 .25rem;font-size:.98rem;}
            .dms-hit mark{background:#fde68a;padding:0 .1rem;}
            .dms-hit .meta{color:#94a3b8;font-size:.78rem;margin-top:.3rem;}
            .dms-tag{display:inline-block;background:#eef2ff;color:#4338ca;border-radius:10px;padding:.05rem .5rem;margin:0 .2rem .2rem 0;font-size:.72rem;}
            .dms-slink{color:#2563eb;cursor:pointer;text-decoration:none;}
            .dms-slink:hover{text-decoration:underline;}
          </style>`;

        const el = (id) => container.querySelector(id);
        const statusEl = el('#dms-sr-status');
        const resultsEl = el('#dms-sr');

        // Current form state as a plain object (what we save / restore).
        function currentParams() {
            const p = {};
            const q = el('#dms-q').value.trim(); if (q) p.q = q;
            const tag = el('#dms-f-tag').value.trim(); if (tag) p.tag = tag;
            const type = el('#dms-f-type').value; if (type) p.type = type;
            p.sort = el('#dms-f-sort').value;
            return p;
        }

        function applyParams(p) {
            el('#dms-q').value = p.q || '';
            el('#dms-f-tag').value = p.tag || '';
            el('#dms-f-type').value = p.type || '';
            el('#dms-f-sort').value = p.sort || 'relevance';
        }

        async function runSearch() {
            const p = currentParams();
            const params = new URLSearchParams();
            Object.entries(p).forEach(([k, v]) => params.set(k, v));
            params.set('page_size', '50');

            statusEl.textContent = 'Searching…';
            resultsEl.innerHTML = '';
            try {
                const res = await fetch(`${SEARCH}?${params.toString()}`, { headers: authHeaders() });
                if (!res.ok) throw new Error(`Search failed (${res.status})`);
                const data = await res.json();
                statusEl.textContent = `${data.total} result${data.total === 1 ? '' : 's'}`;
                if (!data.results.length) {
                    resultsEl.innerHTML = '<p style="color:#64748b;">No matching documents.</p>';
                    return;
                }
                resultsEl.innerHTML = data.results.map((r) => {
                    const tags = (r.tags || []).map((t) => `<span class="dms-tag">${esc(t)}</span>`).join('');
                    const snip = r.snippet ? `<div style="font-size:.85rem;color:#475569;">${safeSnippet(r.snippet)}</div>` : '';
                    const lock = r.is_private ? ' 🔒' : '';
                    return `<div class="dms-hit">
                        <h4>📄 ${esc(r.filename)}${lock} <span class="dms-slink" data-dl="${r.id}" style="font-size:.8rem;font-weight:400;">Download</span></h4>
                        ${snip}
                        <div>${tags}</div>
                        <div class="meta">${esc(r.content_type)} · ${fmtBytes(r.size_bytes)} · v${r.current_version} · ${new Date(r.updated_at || r.created_at).toLocaleDateString()}</div>
                    </div>`;
                }).join('');
                resultsEl.querySelectorAll('[data-dl]').forEach((a) =>
                    a.addEventListener('click', async () => {
                        try {
                            const dr = await fetch(`${DOCS}/${a.dataset.dl}/download`, { headers: authHeaders() });
                            if (!dr.ok) throw new Error(`Download failed (${dr.status})`);
                            const { url } = await dr.json();
                            window.open(url, '_blank');
                        } catch (err) { statusEl.textContent = err.message; }
                    }));
            } catch (err) {
                statusEl.textContent = err.message;
            }
        }

        el('#dms-go').addEventListener('click', runSearch);
        el('#dms-q').addEventListener('keydown', (e) => { if (e.key === 'Enter') runSearch(); });
        ['#dms-f-tag', '#dms-f-type', '#dms-f-sort'].forEach((id) =>
            el(id).addEventListener('change', runSearch));

        // ---- saved searches (chips; a <select> would be swallowed by the
        // shell's FlexSelect auto-upgrade, so we render clickable chips instead) --
        const savedListEl = el('#dms-saved-list');
        async function loadSaved() {
            try {
                const res = await fetch(SAVED, { headers: authHeaders() });
                if (!res.ok) return;
                const { saved } = await res.json();
                if (!saved.length) { savedListEl.innerHTML = ''; return; }
                savedListEl.innerHTML = '<span style="color:#94a3b8;font-size:.8rem;">Saved:</span>' +
                    saved.map((s) => `
                        <span style="display:inline-flex;align-items:center;gap:.3rem;background:#f1f5f9;border-radius:14px;padding:.15rem .55rem;font-size:.8rem;">
                          <span class="dms-slink" data-load='${encodeURIComponent(JSON.stringify(s.params || {}))}'>${esc(s.name)}</span>
                          <span class="dms-slink" data-del="${s.id}" style="color:#dc2626;" title="Delete">✕</span>
                        </span>`).join('');
                savedListEl.querySelectorAll('[data-load]').forEach((c) =>
                    c.addEventListener('click', () => {
                        applyParams(JSON.parse(decodeURIComponent(c.dataset.load)));
                        runSearch();
                    }));
                savedListEl.querySelectorAll('[data-del]').forEach((c) =>
                    c.addEventListener('click', async () => {
                        try { await fetch(`${SAVED}/${c.dataset.del}`, { method: 'DELETE', headers: authHeaders() }); loadSaved(); }
                        catch (err) { statusEl.textContent = err.message; }
                    }));
            } catch { /* non-fatal */ }
        }
        el('#dms-save').addEventListener('click', async () => {
            const name = prompt('Name this search:');
            if (!name) return;
            try {
                await fetch(SAVED, {
                    method: 'POST',
                    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, params: currentParams() }),
                });
                await loadSaved();
                statusEl.textContent = `Saved “${name}” ✓`;
            } catch (err) { statusEl.textContent = err.message; }
        });

        await loadSaved();
        el('#dms-q').focus();
    }
}
