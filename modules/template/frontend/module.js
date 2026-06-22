/**
 * TEMPLATE module frontend entry point.
 *
 * Platform mounts this at #/modules/TEMPLATE.
 * Rules:
 *   - Use window.apiFetch for all API calls (handles auth + tenant headers)
 *   - Use Flex components from the platform component library
 *   - Use CSS variables from /assets/css/variables.css — never hardcode
 */

const MODULE_API = "/api/v1/modules/TEMPLATE";

export async function init(container) {
  renderShell(container);
  await loadItems(container);
}

function renderShell(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1 class="page-title">TEMPLATE</h1>
      <flex-button id="btn-create" variant="primary" icon="ph-plus">
        New Item
      </flex-button>
    </div>
    <div id="grid-container"></div>
    <div id="empty-state" class="empty-state" style="display:none">
      <p>No items yet.</p>
      <flex-button variant="secondary" icon="ph-plus" onclick="document.getElementById('btn-create').click()">
        Create your first item
      </flex-button>
    </div>
  `;

  container.querySelector("#btn-create").addEventListener("click", () => openCreateModal(container));
}

async function loadItems(container) {
  try {
    const data = await window.apiFetch(`${MODULE_API}/items`);
    renderGrid(container, data.items);
  } catch (err) {
    console.error("[TEMPLATE] Failed to load items:", err);
    showError(container, err.message);
  }
}

function renderGrid(container, items) {
  const gridContainer = container.querySelector("#grid-container");
  const emptyState = container.querySelector("#empty-state");

  if (!items.length) {
    emptyState.style.display = "";
    return;
  }

  emptyState.style.display = "none";

  const grid = document.createElement("flex-datagrid");
  grid.setAttribute("columns", JSON.stringify([
    { field: "name",        header: "Name",        sortable: true },
    { field: "description", header: "Description" },
    { field: "is_active",   header: "Active",      type: "boolean" },
    { field: "created_at",  header: "Created",     type: "datetime" },
  ]));
  grid.setAttribute("rows", JSON.stringify(items));
  grid.setAttribute("page-size", "25");

  grid.addEventListener("row-action", async (e) => {
    const { action, row } = e.detail;
    if (action === "delete") await deleteItem(container, row.id);
  });

  gridContainer.innerHTML = "";
  gridContainer.appendChild(grid);
}

async function openCreateModal(container) {
  // TODO: replace with a FlexModal + FlexForm when available
  const name = prompt("Item name:");
  if (!name) return;

  try {
    await window.apiFetch(`${MODULE_API}/items`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await loadItems(container);
  } catch (err) {
    console.error("[TEMPLATE] Create failed:", err);
  }
}

async function deleteItem(container, itemId) {
  if (!confirm("Delete this item?")) return;
  try {
    await window.apiFetch(`${MODULE_API}/items/${itemId}`, { method: "DELETE" });
    await loadItems(container);
  } catch (err) {
    console.error("[TEMPLATE] Delete failed:", err);
  }
}

function showError(container, message) {
  container.innerHTML += `<div class="alert alert-error">${message}</div>`;
}
