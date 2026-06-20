/**
 * TEMPLATE module frontend entry point.
 *
 * The platform mounts your module at #/modules/TEMPLATE — do NOT register
 * routes yourself. The platform calls init() when the module is activated.
 *
 * Rules:
 *  - Use CSS variables from /assets/css/variables.css for all styles
 *  - Call only /api/v1/modules/TEMPLATE/ endpoints
 *  - Use Flex components from the platform component library
 */

const MODULE_API = "/api/v1/modules/TEMPLATE";

export async function init(container) {
  // TODO: replace with your module initialisation logic
  container.innerHTML = `<p>TEMPLATE module loaded. Replace this.</p>`;
  await loadItems(container);
}

async function loadItems(container) {
  try {
    const res = await fetch(`${MODULE_API}/items`, {
      headers: { Authorization: `Bearer ${window.__platform?.token}` },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderItems(container, data.items);
  } catch (err) {
    console.error("[TEMPLATE] Failed to load items:", err);
  }
}

function renderItems(container, items) {
  // TODO: render your items using Flex components
  container.querySelector("p").textContent =
    `Loaded ${items.length} items.`;
}
