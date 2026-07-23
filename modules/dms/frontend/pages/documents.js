/**
 * DMS — Documents page (Phase 0).
 *
 * Minimal, dependency-free UI proving the storage vertical slice: upload a file,
 * list documents for the tenant, and download via a presigned URL. Later phases
 * (versioning, folders, ACLs, search) build on this.
 */

const API = '/api/v1/dms/documents';

function authHeaders() {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function fmtBytes(n) {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(1)} ${u[i]}`;
}

export class DocumentsPage {
    static async render(container) {
        container.innerHTML = `
            <div style="padding:1.5rem;max-width:900px;margin:0 auto;">
              <h2 style="margin-bottom:1rem;">Documents</h2>
              <div style="border:1px dashed var(--border-color,#cbd5e1);border-radius:8px;padding:1rem;margin-bottom:1.5rem;">
                <input type="file" id="dms-file" />
                <button id="dms-upload" style="margin-left:.5rem;">Upload</button>
                <span id="dms-status" style="margin-left:.75rem;color:#64748b;"></span>
              </div>
              <table style="width:100%;border-collapse:collapse;" id="dms-table">
                <thead>
                  <tr style="text-align:left;border-bottom:1px solid #e2e8f0;">
                    <th style="padding:.5rem;">Name</th>
                    <th style="padding:.5rem;">Size</th>
                    <th style="padding:.5rem;">Version</th>
                    <th style="padding:.5rem;">Uploaded</th>
                    <th style="padding:.5rem;"></th>
                  </tr>
                </thead>
                <tbody id="dms-rows"><tr><td colspan="5" style="padding:.75rem;color:#64748b;">Loading…</td></tr></tbody>
              </table>
            </div>`;

        const statusEl = container.querySelector('#dms-status');
        const setStatus = (t) => { statusEl.textContent = t; };

        async function refresh() {
            const rows = container.querySelector('#dms-rows');
            try {
                const res = await fetch(`${API}?page=1&page_size=100`, { headers: authHeaders() });
                if (!res.ok) throw new Error(`List failed (${res.status})`);
                const data = await res.json();
                if (!data.documents.length) {
                    rows.innerHTML = `<tr><td colspan="5" style="padding:.75rem;color:#64748b;">No documents yet.</td></tr>`;
                    return;
                }
                rows.innerHTML = data.documents.map((d) => `
                    <tr style="border-bottom:1px solid #f1f5f9;">
                      <td style="padding:.5rem;">${escapeHtml(d.filename)}</td>
                      <td style="padding:.5rem;">${fmtBytes(d.size_bytes)}</td>
                      <td style="padding:.5rem;">v${d.current_version}</td>
                      <td style="padding:.5rem;">${new Date(d.created_at).toLocaleString()}</td>
                      <td style="padding:.5rem;"><a href="#" data-id="${d.id}" class="dms-dl">Download</a></td>
                    </tr>`).join('');
                rows.querySelectorAll('.dms-dl').forEach((a) =>
                    a.addEventListener('click', (e) => { e.preventDefault(); download(a.dataset.id); }));
            } catch (err) {
                rows.innerHTML = `<tr><td colspan="5" style="padding:.75rem;color:#dc2626;">${escapeHtml(err.message)}</td></tr>`;
            }
        }

        async function download(id) {
            const res = await fetch(`${API}/${id}/download`, { headers: authHeaders() });
            if (!res.ok) { setStatus('Download failed'); return; }
            const { url } = await res.json();
            window.open(url, '_blank');
        }

        container.querySelector('#dms-upload').addEventListener('click', async () => {
            const input = container.querySelector('#dms-file');
            if (!input.files.length) { setStatus('Pick a file first'); return; }
            setStatus('Uploading…');
            const fd = new FormData();
            fd.append('file', input.files[0]);
            try {
                const res = await fetch(API, { method: 'POST', headers: authHeaders(), body: fd });
                if (!res.ok) throw new Error(`Upload failed (${res.status})`);
                setStatus('Uploaded ✓');
                input.value = '';
                await refresh();
            } catch (err) {
                setStatus(err.message);
            }
        });

        await refresh();
    }
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}
