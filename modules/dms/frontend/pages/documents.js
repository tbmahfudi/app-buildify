/**
 * DMS — Documents workspace (E1).
 *
 * A dependency-free file-explorer over the DMS API: browse folders via a
 * breadcrumb, create folders / apply workspace templates, upload one or many
 * files into the current folder, and per document manage versions, tags and
 * metadata, move and delete. Folders can be renamed, moved, downloaded as a
 * zip, and deleted (when empty). Auth token comes from localStorage (platform
 * shell). Later phases add ACLs (E3), search (E2) and workflow (E4).
 */

const DOCS = '/api/v1/dms/documents';
const FOLDERS = '/api/v1/dms/folders';
const SHARES = '/api/v1/dms/shares';
const ACLS = '/api/v1/dms/acls';
const AUDIT = '/api/v1/dms/audit';

function authHeaders() {
    // The platform shell stores its JWT as JSON under "tokens" ({access, refresh});
    // fall back to the legacy flat "token" key for older shells.
    let token = null;
    try {
        const t = JSON.parse(localStorage.getItem('tokens') || 'null');
        token = (t && t.access) || null;
    } catch { /* ignore malformed */ }
    if (!token) token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function fmtBytes(n) {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(1)} ${u[i]}`;
}

function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

async function api(url, opts = {}) {
    const res = await fetch(url, {
        ...opts,
        headers: { ...authHeaders(), ...(opts.headers || {}) },
    });
    if (res.status === 204) return null;
    let body = null;
    try { body = await res.json(); } catch { /* non-json (e.g. blob endpoints) */ }
    if (!res.ok) {
        const msg = (body && (body.detail || body.message)) || `Request failed (${res.status})`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return body;
}

export default class DocumentsPage {
    constructor() {
        this.name = 'dms-documents';
    }

    async render() {
        // The shell mounts module pages into #app-content (MODULE_FRONTEND_CONTRACT §4a).
        const container = document.getElementById('app-content');
        if (!container) return;

        // --- navigation state: root is represented by id=null -----------------
        // `path` is the breadcrumb trail of {id, name} from root to current.
        const state = { path: [] };
        const currentId = () => (state.path.length ? state.path[state.path.length - 1].id : null);

        container.innerHTML = `
          <div class="dms-wrap" style="padding:1.25rem 1.5rem;max-width:1100px;margin:0 auto;">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;">
              <h2 style="margin:0;">Documents</h2>
              <div style="display:flex;gap:.5rem;flex-wrap:wrap;">
                <button id="dms-new-folder" class="dms-btn">＋ New folder</button>
                <select id="dms-template" class="dms-btn"><option value="">Apply template…</option></select>
                <button id="dms-zip" class="dms-btn" title="Download this folder as a zip">⤓ Folder zip</button>
                <button id="dms-activity" class="dms-btn" title="Recent activity (audit trail)">🕘 Activity</button>
              </div>
            </div>

            <div id="dms-crumbs" style="margin:.75rem 0;font-size:.9rem;color:#475569;"></div>

            <div style="border:1px dashed var(--border-color,#cbd5e1);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;">
              <input type="file" id="dms-file" multiple />
              <button id="dms-upload" class="dms-btn dms-btn-primary">Upload</button>
              <span id="dms-status" style="color:#64748b;font-size:.9rem;"></span>
            </div>

            <table style="width:100%;border-collapse:collapse;font-size:.92rem;">
              <thead>
                <tr style="text-align:left;border-bottom:1px solid #e2e8f0;color:#64748b;">
                  <th style="padding:.5rem;">Name</th>
                  <th style="padding:.5rem;">Tags</th>
                  <th style="padding:.5rem;white-space:nowrap;">Size</th>
                  <th style="padding:.5rem;">Ver</th>
                  <th style="padding:.5rem;white-space:nowrap;">Modified</th>
                  <th style="padding:.5rem;text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="dms-rows"><tr><td colspan="6" style="padding:.75rem;color:#64748b;">Loading…</td></tr></tbody>
            </table>
          </div>

          <div id="dms-modal-root"></div>

          <style>
            .dms-btn{padding:.4rem .7rem;border:1px solid var(--border-color,#cbd5e1);background:var(--surface,#fff);border-radius:6px;cursor:pointer;font-size:.85rem;color:inherit;}
            .dms-btn:hover{background:#f1f5f9;}
            .dms-btn-primary{background:#2563eb;border-color:#2563eb;color:#fff;}
            .dms-btn-primary:hover{background:#1d4ed8;}
            .dms-link{color:#2563eb;cursor:pointer;text-decoration:none;}
            .dms-link:hover{text-decoration:underline;}
            .dms-tag{display:inline-block;background:#eef2ff;color:#4338ca;border-radius:10px;padding:.05rem .5rem;margin:0 .2rem .2rem 0;font-size:.75rem;}
            .dms-row:hover{background:#f8fafc;}
            .dms-overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;z-index:1000;}
            .dms-dialog{background:var(--surface,#fff);color:inherit;border-radius:10px;max-width:520px;width:90%;max-height:80vh;overflow:auto;padding:1.25rem 1.4rem;box-shadow:0 10px 40px rgba(0,0,0,.2);}
            .dms-dialog h3{margin:0 0 .75rem;}
            .dms-in{width:100%;padding:.45rem .6rem;border:1px solid var(--border-color,#cbd5e1);border-radius:6px;box-sizing:border-box;font:inherit;}
          </style>`;

        const els = {
            status: container.querySelector('#dms-status'),
            crumbs: container.querySelector('#dms-crumbs'),
            rows: container.querySelector('#dms-rows'),
            file: container.querySelector('#dms-file'),
            template: container.querySelector('#dms-template'),
            modalRoot: container.querySelector('#dms-modal-root'),
        };
        const setStatus = (t, err = false) => {
            els.status.textContent = t;
            els.status.style.color = err ? '#dc2626' : '#64748b';
        };

        // ---- modal helper ----------------------------------------------------
        function modal(title, bodyHtml, onMount) {
            const overlay = document.createElement('div');
            overlay.className = 'dms-overlay';
            overlay.innerHTML = `<div class="dms-dialog"><h3>${esc(title)}</h3>${bodyHtml}</div>`;
            const close = () => overlay.remove();
            overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
            els.modalRoot.appendChild(overlay);
            if (onMount) onMount(overlay.querySelector('.dms-dialog'), close);
            return close;
        }

        // ---- breadcrumb ------------------------------------------------------
        function renderCrumbs() {
            const parts = [`<span class="dms-link" data-depth="0">🏠 Home</span>`];
            state.path.forEach((f, i) => {
                parts.push('<span style="color:#94a3b8;"> / </span>');
                parts.push(`<span class="dms-link" data-depth="${i + 1}">${esc(f.name)}</span>`);
            });
            els.crumbs.innerHTML = parts.join('');
            els.crumbs.querySelectorAll('.dms-link').forEach((el) =>
                el.addEventListener('click', () => {
                    state.path = state.path.slice(0, Number(el.dataset.depth));
                    refresh();
                }));
        }

        // ---- data load -------------------------------------------------------
        async function loadTemplates() {
            try {
                const { templates } = await api(`${FOLDERS}/templates`);
                els.template.innerHTML = '<option value="">Apply template…</option>' +
                    Object.keys(templates).map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join('');
            } catch { /* non-fatal */ }
        }

        async function refresh() {
            renderCrumbs();
            els.rows.innerHTML = `<tr><td colspan="6" style="padding:.75rem;color:#64748b;">Loading…</td></tr>`;
            const cid = currentId();
            try {
                const folderQ = cid ? `?parent_id=${cid}` : '';
                const docQ = cid ? `?folder_id=${cid}&root_only=false` : `?root_only=true`;
                const [foldersRes, docsRes] = await Promise.all([
                    api(`${FOLDERS}${folderQ}`),
                    api(`${DOCS}${docQ ? docQ + '&' : '?'}page=1&page_size=100`),
                ]);
                const folders = foldersRes.folders || [];
                const docs = docsRes.documents || [];
                if (!folders.length && !docs.length) {
                    els.rows.innerHTML = `<tr><td colspan="6" style="padding:.75rem;color:#64748b;">This folder is empty.</td></tr>`;
                    return;
                }
                els.rows.innerHTML =
                    folders.map(folderRow).join('') + docs.map(docRow).join('');
                wireRows(folders, docs);
            } catch (err) {
                els.rows.innerHTML = `<tr><td colspan="6" style="padding:.75rem;color:#dc2626;">${esc(err.message)}</td></tr>`;
            }
        }

        function lock(isPrivate) {
            return isPrivate ? ' <span title="Private" style="font-size:.8rem;">🔒</span>' : '';
        }

        function folderRow(f) {
            return `<tr class="dms-row" style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:.5rem;"><span class="dms-link" data-fopen="${f.id}">📁 ${esc(f.name)}</span>${lock(f.is_private)}</td>
                <td style="padding:.5rem;"></td>
                <td style="padding:.5rem;color:#94a3b8;">—</td>
                <td style="padding:.5rem;color:#94a3b8;">—</td>
                <td style="padding:.5rem;color:#94a3b8;">${new Date(f.created_at).toLocaleDateString()}</td>
                <td style="padding:.5rem;text-align:right;white-space:nowrap;">
                  <span class="dms-link" data-frename="${f.id}" data-name="${esc(f.name)}">Rename</span> ·
                  <span class="dms-link" data-fmove="${f.id}">Move</span> ·
                  <span class="dms-link" data-fperm="${f.id}" data-name="${esc(f.name)}" data-priv="${f.is_private ? 1 : ''}">Permissions</span> ·
                  <span class="dms-link" data-fzip="${f.id}" data-name="${esc(f.name)}">Zip</span> ·
                  <span class="dms-link" data-fdel="${f.id}" data-name="${esc(f.name)}" style="color:#dc2626;">Delete</span>
                </td></tr>`;
        }

        function docRow(d) {
            const tags = (d.tags || []).map((t) => `<span class="dms-tag">${esc(t)}</span>`).join('') || '';
            return `<tr class="dms-row" style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:.5rem;">📄 ${esc(d.filename)}${lock(d.is_private)}</td>
                <td style="padding:.5rem;">${tags}</td>
                <td style="padding:.5rem;white-space:nowrap;">${fmtBytes(d.size_bytes)}</td>
                <td style="padding:.5rem;">v${d.current_version}</td>
                <td style="padding:.5rem;white-space:nowrap;">${new Date(d.updated_at || d.created_at).toLocaleDateString()}</td>
                <td style="padding:.5rem;text-align:right;white-space:nowrap;">
                  <span class="dms-link" data-dl="${d.id}">Download</span> ·
                  <span class="dms-link" data-vers="${d.id}" data-name="${esc(d.filename)}">Versions</span> ·
                  <span class="dms-link" data-tags="${d.id}" data-name="${esc(d.filename)}">Tags</span> ·
                  <span class="dms-link" data-share="${d.id}" data-name="${esc(d.filename)}">Share</span> ·
                  <span class="dms-link" data-appr="${d.id}" data-name="${esc(d.filename)}">Approvals</span> ·
                  <span class="dms-link" data-dperm="${d.id}" data-name="${esc(d.filename)}" data-priv="${d.is_private ? 1 : ''}">Permissions</span> ·
                  <span class="dms-link" data-dmove="${d.id}">Move</span> ·
                  <span class="dms-link" data-ddel="${d.id}" data-name="${esc(d.filename)}" style="color:#dc2626;">Delete</span>
                </td></tr>`;
        }

        function wireRows(folders, docs) {
            const q = (sel) => els.rows.querySelectorAll(sel);
            q('[data-fopen]').forEach((el) => el.addEventListener('click', () => {
                const f = folders.find((x) => x.id === el.dataset.fopen);
                state.path.push({ id: f.id, name: f.name });
                refresh();
            }));
            q('[data-frename]').forEach((el) => el.addEventListener('click', () => renameFolder(el.dataset.frename, el.dataset.name)));
            q('[data-fmove]').forEach((el) => el.addEventListener('click', () => moveNode(el.dataset.fmove, 'folder')));
            q('[data-fperm]').forEach((el) => el.addEventListener('click', () => permissionsDialog('folder', el.dataset.fperm, el.dataset.name, !!el.dataset.priv)));
            q('[data-fzip]').forEach((el) => el.addEventListener('click', () => downloadFolderZip(el.dataset.fzip, el.dataset.name)));
            q('[data-fdel]').forEach((el) => el.addEventListener('click', () => deleteFolder(el.dataset.fdel, el.dataset.name)));
            q('[data-dl]').forEach((el) => el.addEventListener('click', () => downloadDoc(el.dataset.dl)));
            q('[data-vers]').forEach((el) => el.addEventListener('click', () => showVersions(el.dataset.vers, el.dataset.name)));
            q('[data-tags]').forEach((el) => el.addEventListener('click', () => editTags(el.dataset.tags, el.dataset.name)));
            q('[data-share]').forEach((el) => el.addEventListener('click', () => shareDialog(el.dataset.share, el.dataset.name)));
            q('[data-appr]').forEach((el) => el.addEventListener('click', () => approvalsDialog(el.dataset.appr, el.dataset.name)));
            q('[data-dperm]').forEach((el) => el.addEventListener('click', () => permissionsDialog('document', el.dataset.dperm, el.dataset.name, !!el.dataset.priv)));
            q('[data-dmove]').forEach((el) => el.addEventListener('click', () => moveNode(el.dataset.dmove, 'doc')));
            q('[data-ddel]').forEach((el) => el.addEventListener('click', () => deleteDoc(el.dataset.ddel, el.dataset.name)));
        }

        // ---- documents -------------------------------------------------------
        async function downloadDoc(id, versionNo) {
            try {
                const q = versionNo ? `?version=${versionNo}` : '';
                const { url } = await api(`${DOCS}/${id}/download${q}`);
                window.open(url, '_blank');
            } catch (err) { setStatus(err.message, true); }
        }

        async function deleteDoc(id, name) {
            if (!confirm(`Delete "${name}"? This cannot be undone from the UI.`)) return;
            try {
                await api(`${DOCS}/${id}`, { method: 'DELETE' });
                setStatus('Deleted ✓');
                refresh();
            } catch (err) { setStatus(err.message, true); }
        }

        async function showVersions(id, name) {
            let versions = [];
            try { versions = await api(`${DOCS}/${id}/versions`); }
            catch (err) { setStatus(err.message, true); return; }
            const rows = versions.map((v) => `
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:.4rem;">v${v.version_no}</td>
                  <td style="padding:.4rem;">${fmtBytes(v.size_bytes)}</td>
                  <td style="padding:.4rem;color:#64748b;">${esc(v.change_comment || '')}</td>
                  <td style="padding:.4rem;color:#94a3b8;white-space:nowrap;">${new Date(v.created_at).toLocaleString()}</td>
                  <td style="padding:.4rem;text-align:right;white-space:nowrap;">
                    <span class="dms-link" data-vdl="${v.version_no}">Download</span>
                    ${v.version_no !== versions[0].version_no ? ` · <span class="dms-link" data-vrestore="${v.version_no}">Restore</span>` : ''}
                  </td></tr>`).join('');
            modal(`Versions — ${name}`, `
                <table style="width:100%;border-collapse:collapse;font-size:.85rem;">
                  <thead><tr style="text-align:left;color:#64748b;"><th style="padding:.4rem;">Ver</th><th>Size</th><th>Comment</th><th>When</th><th></th></tr></thead>
                  <tbody>${rows}</tbody>
                </table>`, (dialog) => {
                dialog.querySelectorAll('[data-vdl]').forEach((el) =>
                    el.addEventListener('click', () => downloadDoc(id, el.dataset.vdl)));
                dialog.querySelectorAll('[data-vrestore]').forEach((el) =>
                    el.addEventListener('click', async () => {
                        try {
                            await api(`${DOCS}/${id}/versions/${el.dataset.vrestore}/restore`, { method: 'POST' });
                            setStatus(`Restored v${el.dataset.vrestore} ✓`);
                            dialog.closest('.dms-overlay').remove();
                            refresh();
                        } catch (err) { setStatus(err.message, true); }
                    }));
            });
        }

        async function editTags(id, name) {
            let doc;
            try { doc = await api(`${DOCS}/${id}`); }
            catch (err) { setStatus(err.message, true); return; }
            const tagStr = (doc.tags || []).join(', ');
            const metaStr = JSON.stringify(doc.metadata || {}, null, 2);
            modal(`Tags & metadata — ${name}`, `
                <label style="font-size:.85rem;color:#475569;">Tags (comma-separated)</label>
                <input id="dms-tag-in" class="dms-in" style="margin:.25rem 0 .9rem;" value="${esc(tagStr)}" />
                <label style="font-size:.85rem;color:#475569;">Metadata (JSON)</label>
                <textarea id="dms-meta-in" class="dms-in" rows="5" style="margin:.25rem 0 1rem;font-family:monospace;">${esc(metaStr)}</textarea>
                <div id="dms-meta-err" style="color:#dc2626;font-size:.8rem;margin-bottom:.6rem;"></div>
                <div style="text-align:right;"><button id="dms-tag-save" class="dms-btn dms-btn-primary">Save</button></div>`,
                (dialog, close) => {
                    dialog.querySelector('#dms-tag-save').addEventListener('click', async () => {
                        const tags = dialog.querySelector('#dms-tag-in').value.split(',').map((t) => t.trim()).filter(Boolean);
                        let metadata;
                        try { metadata = JSON.parse(dialog.querySelector('#dms-meta-in').value || '{}'); }
                        catch { dialog.querySelector('#dms-meta-err').textContent = 'Metadata must be valid JSON.'; return; }
                        try {
                            await api(`${DOCS}/${id}/metadata`, {
                                method: 'PATCH',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ tags, metadata }),
                            });
                            setStatus('Metadata saved ✓');
                            close();
                            refresh();
                        } catch (err) { dialog.querySelector('#dms-meta-err').textContent = err.message; }
                    });
                });
        }

        // ---- move (folder or doc) into a chosen folder -----------------------
        async function moveNode(id, kind) {
            // Offer root + all folders as targets (small tenants → a flat picker is fine).
            let all = [];
            try { all = await collectFolders(); }
            catch (err) { setStatus(err.message, true); return; }
            const opts = ['<option value="">🏠 Home (root)</option>']
                .concat(all.filter((f) => f.id !== id).map((f) => `<option value="${f.id}">${esc(f.label)}</option>`))
                .join('');
            modal(`Move ${kind}`, `
                <label style="font-size:.85rem;color:#475569;">Destination folder</label>
                <select id="dms-move-sel" class="dms-in" style="margin:.35rem 0 1rem;">${opts}</select>
                <div id="dms-move-err" style="color:#dc2626;font-size:.8rem;margin-bottom:.6rem;"></div>
                <div style="text-align:right;"><button id="dms-move-go" class="dms-btn dms-btn-primary">Move</button></div>`,
                (dialog, close) => {
                    dialog.querySelector('#dms-move-go').addEventListener('click', async () => {
                        const dest = dialog.querySelector('#dms-move-sel').value || null;
                        const url = kind === 'doc' ? `${DOCS}/${id}/move` : `${FOLDERS}/${id}/move`;
                        try {
                            await api(url, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ [kind === 'doc' ? 'folder_id' : 'parent_id']: dest }),
                            });
                            setStatus('Moved ✓');
                            close();
                            refresh();
                        } catch (err) { dialog.querySelector('#dms-move-err').textContent = err.message; }
                    });
                });
        }

        // Flatten the folder tree into {id, label(indented path)} for pickers.
        async function collectFolders() {
            const out = [];
            async function walk(parentId, prefix) {
                const q = parentId ? `?parent_id=${parentId}` : '';
                const { folders } = await api(`${FOLDERS}${q}`);
                for (const f of folders) {
                    out.push({ id: f.id, label: prefix + f.name });
                    await walk(f.id, prefix + f.name + ' / ');
                }
            }
            await walk(null, '');
            return out;
        }

        // ---- folder ops ------------------------------------------------------
        async function renameFolder(id, name) {
            const next = prompt('Rename folder:', name);
            if (!next || next === name) return;
            try {
                await api(`${FOLDERS}/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: next }),
                });
                setStatus('Renamed ✓');
                refresh();
            } catch (err) { setStatus(err.message, true); }
        }

        async function deleteFolder(id, name) {
            if (!confirm(`Delete folder "${name}"? It must be empty.`)) return;
            try {
                await api(`${FOLDERS}/${id}`, { method: 'DELETE' });
                setStatus('Folder deleted ✓');
                refresh();
            } catch (err) { setStatus(err.message, true); }
        }

        async function downloadFolderZip(id, name) {
            setStatus('Preparing zip…');
            try {
                const res = await fetch(`${FOLDERS}/${id}/download`, { headers: authHeaders() });
                if (!res.ok) throw new Error(`Zip failed (${res.status})`);
                const blob = await res.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `${name}.zip`;
                a.click();
                URL.revokeObjectURL(a.href);
                setStatus('Zip downloaded ✓');
            } catch (err) { setStatus(err.message, true); }
        }

        // ---- share links -----------------------------------------------------
        async function shareDialog(docId, name) {
            const body = `
                <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:flex-end;margin-bottom:.9rem;">
                  <label style="font-size:.8rem;color:#475569;">Expiry (hours, blank = none)
                    <input id="dms-sh-exp" class="dms-in" type="number" min="1" style="width:120px;margin-top:.2rem;" /></label>
                  <label style="font-size:.8rem;color:#475569;">Max downloads (blank = ∞)
                    <input id="dms-sh-max" class="dms-in" type="number" min="1" style="width:120px;margin-top:.2rem;" /></label>
                  <button id="dms-sh-create" class="dms-btn dms-btn-primary">Create link</button>
                </div>
                <div id="dms-sh-list" style="font-size:.85rem;">Loading…</div>`;
            modal(`Share — ${name}`, body, (dialog) => {
                const listEl = dialog.querySelector('#dms-sh-list');
                async function refreshShares() {
                    try {
                        const { shares } = await api(`${SHARES}?document_id=${docId}`);
                        if (!shares.length) { listEl.innerHTML = '<span style="color:#64748b;">No links yet.</span>'; return; }
                        listEl.innerHTML = shares.map((s) => {
                            const url = window.location.origin + s.public_path;
                            const status = s.is_revoked ? '<span style="color:#dc2626;">revoked</span>'
                                : `${s.download_count}${s.max_downloads ? '/' + s.max_downloads : ''} dl`;
                            const exp = s.expires_at ? new Date(s.expires_at).toLocaleString() : 'no expiry';
                            return `<div style="border-bottom:1px solid #f1f5f9;padding:.4rem 0;">
                                <input class="dms-in" style="font-family:monospace;font-size:.75rem;" readonly value="${esc(url)}" onclick="this.select()" />
                                <div style="display:flex;justify-content:space-between;margin-top:.25rem;color:#64748b;">
                                  <span>${status} · ${esc(exp)}</span>
                                  ${s.is_revoked ? '' : `<span class="dms-link" data-revoke="${s.id}" style="color:#dc2626;">Revoke</span>`}
                                </div></div>`;
                        }).join('');
                        listEl.querySelectorAll('[data-revoke]').forEach((el) =>
                            el.addEventListener('click', async () => {
                                try { await api(`${SHARES}/${el.dataset.revoke}`, { method: 'DELETE' }); refreshShares(); }
                                catch (err) { setStatus(err.message, true); }
                            }));
                    } catch (err) { listEl.innerHTML = `<span style="color:#dc2626;">${esc(err.message)}</span>`; }
                }
                dialog.querySelector('#dms-sh-create').addEventListener('click', async () => {
                    const exp = dialog.querySelector('#dms-sh-exp').value;
                    const max = dialog.querySelector('#dms-sh-max').value;
                    const payload = { document_id: docId };
                    if (exp) payload.expires_in_hours = Number(exp);
                    if (max) payload.max_downloads = Number(max);
                    try {
                        await api(SHARES, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                        refreshShares();
                    } catch (err) { setStatus(err.message, true); }
                });
                refreshShares();
            });
        }

        // ---- privacy + ACL grants -------------------------------------------
        async function permissionsDialog(resourceType, resourceId, name, isPrivate = false) {
            const body = `
                <label style="display:flex;align-items:center;gap:.5rem;margin-bottom:1rem;font-size:.9rem;">
                  <input type="checkbox" id="dms-priv" /> Private (only owner, admins and granted users/groups)
                </label>
                <div style="font-size:.85rem;color:#475569;margin-bottom:.3rem;font-weight:600;">Grants</div>
                <div id="dms-acl-list" style="font-size:.85rem;margin-bottom:.8rem;">Loading…</div>
                <div style="border-top:1px solid #e2e8f0;padding-top:.7rem;">
                  <div style="font-size:.8rem;color:#475569;margin-bottom:.35rem;">Add grant (user/group ID)</div>
                  <div style="display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;">
                    <select id="dms-acl-ptype" class="dms-in" style="width:90px;"><option value="user">user</option><option value="group">group</option></select>
                    <input id="dms-acl-pid" class="dms-in" style="flex:1;min-width:200px;" placeholder="principal UUID" />
                    <select id="dms-acl-cap" class="dms-in" style="width:100px;"><option value="view">view</option><option value="edit">edit</option><option value="manage">manage</option></select>
                    <button id="dms-acl-add" class="dms-btn dms-btn-primary">Grant</button>
                  </div>
                  <div id="dms-acl-err" style="color:#dc2626;font-size:.8rem;margin-top:.4rem;"></div>
                </div>`;
            modal(`Permissions — ${name}`, body, (dialog) => {
                const errEl = dialog.querySelector('#dms-acl-err');
                const privEl = dialog.querySelector('#dms-priv');
                privEl.checked = isPrivate;  // reflect current state; toggling PUTs live
                privEl.addEventListener('change', async () => {
                    try {
                        await api(`${ACLS}/${resourceType}/${resourceId}/privacy`, {
                            method: 'PUT', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ is_private: privEl.checked }),
                        });
                        setStatus(`Marked ${privEl.checked ? 'private' : 'public'} ✓`);
                        refresh();
                    } catch (err) { errEl.textContent = err.message; privEl.checked = !privEl.checked; }
                });
                const listEl = dialog.querySelector('#dms-acl-list');
                async function refreshGrants() {
                    try {
                        const { acls } = await api(`${ACLS}/${resourceType}/${resourceId}/grants`);
                        listEl.innerHTML = acls.length ? acls.map((a) => `
                            <div style="display:flex;justify-content:space-between;border-bottom:1px solid #f1f5f9;padding:.3rem 0;">
                              <span>${esc(a.principal_type)} <code style="font-size:.75rem;">${esc(String(a.principal_id).slice(0, 8))}…</code> — <b>${esc(a.capability)}</b></span>
                              <span class="dms-link" data-revacl="${a.id}" style="color:#dc2626;">Remove</span></div>`).join('')
                            : '<span style="color:#64748b;">No grants.</span>';
                        listEl.querySelectorAll('[data-revacl]').forEach((el) =>
                            el.addEventListener('click', async () => {
                                try { await api(`${ACLS}/grants/${el.dataset.revacl}`, { method: 'DELETE' }); refreshGrants(); }
                                catch (err) { errEl.textContent = err.message; }
                            }));
                    } catch (err) { listEl.innerHTML = `<span style="color:#dc2626;">${esc(err.message)}</span>`; }
                }
                dialog.querySelector('#dms-acl-add').addEventListener('click', async () => {
                    errEl.textContent = '';
                    const payload = {
                        principal_type: dialog.querySelector('#dms-acl-ptype').value,
                        principal_id: dialog.querySelector('#dms-acl-pid').value.trim(),
                        capability: dialog.querySelector('#dms-acl-cap').value,
                    };
                    if (!payload.principal_id) { errEl.textContent = 'Enter a principal UUID.'; return; }
                    try {
                        await api(`${ACLS}/${resourceType}/${resourceId}/grants`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
                        });
                        dialog.querySelector('#dms-acl-pid').value = '';
                        refreshGrants();
                    } catch (err) { errEl.textContent = err.message; }
                });
                refreshGrants();
            });
        }

        // ---- approvals (platform workflow engine) ---------------------------
        const APPROVALS = '/api/v1/dms/approvals';
        async function approvalsDialog(docId, name) {
            const body = `
                <div id="dms-appr-current" style="font-size:.85rem;margin-bottom:1rem;">Loading…</div>
                <div style="border-top:1px solid #e2e8f0;padding-top:.7rem;">
                  <div style="font-size:.8rem;color:#475569;margin-bottom:.35rem;">Start an approval</div>
                  <div style="display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;">
                    <select id="dms-appr-wf" class="dms-in" style="flex:1;min-width:200px;"><option value="">Select a workflow…</option></select>
                    <button id="dms-appr-start" class="dms-btn dms-btn-primary">Start</button>
                  </div>
                  <div id="dms-appr-err" style="color:#dc2626;font-size:.8rem;margin-top:.4rem;"></div>
                </div>`;
            modal(`Approvals — ${name}`, body, (dialog) => {
                const errEl = dialog.querySelector('#dms-appr-err');
                const curEl = dialog.querySelector('#dms-appr-current');

                async function refreshInstances() {
                    try {
                        const instances = await api(`${APPROVALS}/documents/${docId}`);
                        if (!instances.length) {
                            curEl.innerHTML = '<span style="color:#64748b;">No approvals started yet.</span>';
                            return;
                        }
                        curEl.innerHTML = instances.map((inst, i) => {
                            const done = inst.status !== 'active';
                            const color = inst.status === 'completed' ? '#16a34a' : (done ? '#dc2626' : '#2563eb');
                            return `<div style="border:1px solid #e2e8f0;border-radius:8px;padding:.55rem .7rem;margin-bottom:.5rem;" data-inst="${inst.id}">
                                <div style="display:flex;justify-content:space-between;">
                                  <span>Approval #${i + 1}</span>
                                  <span style="color:${color};font-weight:600;text-transform:capitalize;">${esc(inst.status)}</span>
                                </div>
                                <div class="dms-appr-actions" style="margin-top:.4rem;"></div>
                              </div>`;
                        }).join('');
                        // Load available transitions for each active instance.
                        for (const inst of instances) {
                            if (inst.status !== 'active') continue;
                            const holder = curEl.querySelector(`[data-inst="${inst.id}"] .dms-appr-actions`);
                            try {
                                const trans = await api(`${APPROVALS}/instances/${inst.id}/transitions`);
                                if (!trans.length) { holder.innerHTML = '<span style="color:#94a3b8;font-size:.8rem;">Awaiting configuration…</span>'; continue; }
                                holder.innerHTML = trans.map((t) =>
                                    `<button class="dms-btn" data-exec="${t.id}" data-inst="${inst.id}" style="margin:0 .3rem .3rem 0;">${esc(t.button_label || t.name)}</button>`).join('');
                                holder.querySelectorAll('[data-exec]').forEach((btn) =>
                                    btn.addEventListener('click', async () => {
                                        const comment = prompt('Comment (optional):') || '';
                                        try {
                                            await api(`${APPROVALS}/instances/${btn.dataset.inst}/execute`, {
                                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({ transition_id: btn.dataset.exec, comment }),
                                            });
                                            setStatus('Approval updated ✓');
                                            refreshInstances();
                                        } catch (err) { errEl.textContent = err.message; }
                                    }));
                            } catch (err) { holder.innerHTML = `<span style="color:#dc2626;font-size:.8rem;">${esc(err.message)}</span>`; }
                        }
                    } catch (err) { curEl.innerHTML = `<span style="color:#dc2626;">${esc(err.message)}</span>`; }
                }

                // Populate workflow picker.
                api(`${APPROVALS}/workflows`).then((wfs) => {
                    dialog.querySelector('#dms-appr-wf').innerHTML = '<option value="">Select a workflow…</option>' +
                        wfs.map((w) => `<option value="${w.id}">${esc(w.name)}</option>`).join('');
                }).catch((err) => { errEl.textContent = err.message; });

                dialog.querySelector('#dms-appr-start').addEventListener('click', async () => {
                    errEl.textContent = '';
                    const wf = dialog.querySelector('#dms-appr-wf').value;
                    if (!wf) { errEl.textContent = 'Pick a workflow first.'; return; }
                    try {
                        await api(`${APPROVALS}/documents/${docId}/start`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ workflow_id: wf }),
                        });
                        setStatus('Approval started ✓');
                        refreshInstances();
                    } catch (err) { errEl.textContent = err.message; }
                });

                refreshInstances();
            });
        }

        // ---- activity (audit trail) -----------------------------------------
        async function activityDialog() {
            modal('Recent activity', '<div id="dms-audit" style="font-size:.82rem;">Loading…</div>', (dialog) => {
                const el = dialog.querySelector('#dms-audit');
                api(`${AUDIT}?page_size=60`).then(({ entries, total }) => {
                    if (!entries.length) { el.innerHTML = '<span style="color:#64748b;">No activity yet.</span>'; return; }
                    const rows = entries.map((e) => `
                        <tr style="border-bottom:1px solid #f1f5f9;">
                          <td style="padding:.3rem;white-space:nowrap;color:#94a3b8;">${new Date(e.created_at).toLocaleString()}</td>
                          <td style="padding:.3rem;"><b>${esc(e.action)}</b></td>
                          <td style="padding:.3rem;color:#64748b;">${esc(e.entity_type)}</td>
                          <td style="padding:.3rem;color:#64748b;">${esc(Object.entries(e.detail || {}).map(([k, v]) => `${k}=${v}`).join(', '))}</td>
                        </tr>`).join('');
                    el.innerHTML = `
                        <div style="margin-bottom:.5rem;"><a class="dms-link" id="dms-audit-csv">⤓ Export CSV</a> · ${total} events</div>
                        <table style="width:100%;border-collapse:collapse;">
                          <thead><tr style="text-align:left;color:#64748b;"><th style="padding:.3rem;">When</th><th>Action</th><th>Type</th><th>Detail</th></tr></thead>
                          <tbody>${rows}</tbody></table>`;
                    dialog.querySelector('#dms-audit-csv').addEventListener('click', async () => {
                        try {
                            const res = await fetch(`${AUDIT}/export.csv`, { headers: authHeaders() });
                            if (!res.ok) throw new Error(`Export failed (${res.status})`);
                            const blob = await res.blob();
                            const a = document.createElement('a');
                            a.href = URL.createObjectURL(blob); a.download = 'dms-audit.csv'; a.click();
                            URL.revokeObjectURL(a.href);
                        } catch (err) { setStatus(err.message, true); }
                    });
                }).catch((err) => { el.innerHTML = `<span style="color:#dc2626;">${esc(err.message)}</span>`; });
            });
        }

        // ---- toolbar ---------------------------------------------------------
        container.querySelector('#dms-activity').addEventListener('click', activityDialog);

        container.querySelector('#dms-new-folder').addEventListener('click', () => {
            const name = prompt('New folder name:');
            if (!name) return;
            const cid = currentId();
            api(FOLDERS, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, parent_id: cid }),
            }).then(() => { setStatus('Folder created ✓'); refresh(); })
              .catch((err) => setStatus(err.message, true));
        });

        els.template.addEventListener('change', async () => {
            const name = els.template.value;
            els.template.value = '';
            if (!name) return;
            try {
                await api(`${FOLDERS}/templates/${encodeURIComponent(name)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_id: currentId() }),
                });
                setStatus(`Template "${name}" applied ✓`);
                refresh();
            } catch (err) { setStatus(err.message, true); }
        });

        container.querySelector('#dms-zip').addEventListener('click', () => {
            const cid = currentId();
            if (!cid) { setStatus('Open a folder to download it as a zip.', true); return; }
            const name = state.path[state.path.length - 1].name;
            downloadFolderZip(cid, name);
        });

        container.querySelector('#dms-upload').addEventListener('click', async () => {
            const files = [...els.file.files];
            if (!files.length) { setStatus('Pick one or more files first', true); return; }
            const cid = currentId();
            let done = 0;
            for (const file of files) {
                setStatus(`Uploading ${++done}/${files.length}: ${file.name}…`);
                const fd = new FormData();
                fd.append('file', file);
                if (cid) fd.append('folder_id', cid);
                try {
                    await api(DOCS, { method: 'POST', body: fd });
                } catch (err) { setStatus(`${file.name}: ${err.message}`, true); return; }
            }
            setStatus(`Uploaded ${files.length} file(s) ✓`);
            els.file.value = '';
            refresh();
        });

        await loadTemplates();
        await refresh();
    }
}
