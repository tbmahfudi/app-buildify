/**
 * No-Code Module Management
 * Handles module CRUD operations, wizard navigation, and validation
 */

import { apiFetch } from './api.js';

const API_BASE = '/modules';
let currentStep = 1;
let allModules = [];
let selectedModule = null;

// Phosphor icon options for modules
const ICON_OPTIONS = [
    'package', 'users', 'briefcase', 'chart-line', 'wallet',
    'shopping-cart', 'headset', 'wrench', 'file-text', 'calendar',
    'chart-bar', 'buildings', 'truck', 'gear', 'clipboard-text'
];

// Color options for modules
const COLOR_OPTIONS = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#14b8a6',
    '#6366f1', '#a855f7', '#64748b', '#0ea5e9', '#22c55e'
];

// Initialize when route is loaded
document.addEventListener('route:loaded', async (event) => {
    if (event.detail.route === 'modules') {
        setTimeout(async () => {
            await loadModules();
            initializeIconPicker();
            initializeColorPicker();
        }, 0);
    }
});

/**
 * Load all modules from API
 */
async function loadModules() {
    try {
        const response = await apiFetch(API_BASE);

        if (response.ok) {
            const data = await response.json();
            // Handle both array and object responses
            allModules = Array.isArray(data) ? data : (data.modules || []);
            displayModules(allModules);
        } else if (response.status === 401) {
            window.location.href = '/';
        } else {
            showNotification('Failed to load modules', 'error');
        }
    } catch (error) {
        console.error('Error loading modules:', error);
        showNotification('Error loading modules', 'error');
    }
}

/**
 * Display modules in grid
 */
function displayModules(modules) {
    const moduleList = document.getElementById('moduleList');
    const emptyState = document.getElementById('emptyState');

    if (!moduleList || !emptyState) return;

    if (modules.length === 0) {
        moduleList.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    moduleList.innerHTML = modules.map(module => createModuleCard(module)).join('');
}

/**
 * Create HTML for a module card
 */
function createModuleCard(module) {
    const statusClass = `status-${module.status}`;
    const iconColor = module.color || '#3b82f6';

    return `
        <div class="module-card bg-white rounded-lg shadow-sm border border-gray-200 p-6 cursor-pointer"
             onclick="showModuleDetail('${module.id}')">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="text-3xl" style="color: ${iconColor}">
                        <i class="ph-fill ph-${module.icon || 'package'}"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900">${module.display_name}</h3>
                        <p class="text-sm text-gray-500">${module.name}</p>
                    </div>
                </div>
                <span class="status-badge ${statusClass}">${module.status}</span>
            </div>

            <p class="text-sm text-gray-600 mb-4 line-clamp-2">
                ${module.description || 'No description provided'}
            </p>

            <div class="flex items-center justify-between text-sm">
                <div class="flex items-center gap-2 text-gray-500">
                    <i class="ph ph-tag"></i>
                    <span>${module.category || 'Uncategorized'}</span>
                </div>
                <div class="flex items-center gap-2 text-gray-500">
                    <i class="ph ph-code"></i>
                    <span class="font-mono text-xs">${module.table_prefix}</span>
                </div>
            </div>

            <div class="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                <span>v${module.version}</span>
                <span>${formatDate(module.created_at)}</span>
            </div>
        </div>
    `;
}

/**
 * Filter modules based on search and filters
 */
window.filterModules = function() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;

    const filtered = allModules.filter(module => {
        const matchesSearch =
            module.name.toLowerCase().includes(searchTerm) ||
            module.display_name.toLowerCase().includes(searchTerm) ||
            (module.description && module.description.toLowerCase().includes(searchTerm));

        const matchesStatus = !statusFilter || module.status === statusFilter;
        const matchesCategory = !categoryFilter || module.category === categoryFilter;

        return matchesSearch && matchesStatus && matchesCategory;
    });

    displayModules(filtered);
}

/**
 * Show create module wizard
 */
window.showCreateModuleWizard = function() {
    document.getElementById('createModuleModal').classList.remove('hidden');
    document.getElementById('createModuleModal').classList.add('flex');
    currentStep = 1;
    updateWizardUI();
    resetForm();
}

/**
 * Close create module wizard
 */
window.closeCreateModuleWizard = function() {
    document.getElementById('createModuleModal').classList.add('hidden');
    document.getElementById('createModuleModal').classList.remove('flex');
    resetForm();
}

/**
 * Navigate to next wizard step
 */
window.nextStep = function() {
    if (!validateCurrentStep()) {
        return;
    }

    if (currentStep < 4) {
        currentStep++;
        updateWizardUI();
    }
}

/**
 * Navigate to previous wizard step
 */
window.previousStep = function() {
    if (currentStep > 1) {
        currentStep--;
        updateWizardUI();
    }
}

/**
 * Update wizard UI based on current step
 */
function updateWizardUI() {
    // Update step indicators
    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum === currentStep) {
            item.classList.add('active');
        } else if (stepNum < currentStep) {
            item.classList.add('completed');
        }
    });

    // Show/hide wizard steps
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.toggle('active', index + 1 === currentStep);
    });

    // Update buttons
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const createButton = document.getElementById('createButton');

    prevButton.style.display = currentStep > 1 ? 'block' : 'none';
    nextButton.classList.toggle('hidden', currentStep === 4);
    createButton.classList.toggle('hidden', currentStep !== 4);

    // Update review step if on step 4
    if (currentStep === 4) {
        updateReviewStep();
    }
}

/**
 * Validate current wizard step
 */
function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            const name = document.getElementById('moduleName').value.trim();
            const displayName = document.getElementById('moduleDisplayName').value.trim();
            const category = document.getElementById('moduleCategory').value;

            if (!name) {
                showNotification('Module name is required', 'error');
                return false;
            }
            if (!displayName) {
                showNotification('Display name is required', 'error');
                return false;
            }
            if (!category) {
                showNotification('Category is required', 'error');
                return false;
            }
            return true;

        case 2:
            const prefix = document.getElementById('tablePrefix').value.trim();
            if (!prefix) {
                showNotification('Table prefix is required', 'error');
                return false;
            }
            if (!/^[a-z0-9]{1,10}$/.test(prefix)) {
                showNotification('Invalid table prefix format', 'error');
                return false;
            }
            return true;

        case 3:
            return true; // Visual config is optional

        default:
            return true;
    }
}

/**
 * Update review step with form data
 */
function updateReviewStep() {
    const formData = getFormData();

    document.getElementById('reviewName').textContent = formData.name;
    document.getElementById('reviewDisplayName').textContent = formData.display_name;
    document.getElementById('reviewCategory').textContent = formData.category;
    document.getElementById('reviewPrefix').textContent = formData.table_prefix;
    document.getElementById('reviewDescription').textContent = formData.description || 'No description';
    document.getElementById('reviewTags').textContent = formData.tags.length > 0 ? formData.tags.join(', ') : 'No tags';
}

/**
 * Get form data
 */
function getFormData() {
    const tagsInput = document.getElementById('moduleTags').value;
    const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(t => t) : [];

    return {
        name: document.getElementById('moduleName').value.trim(),
        display_name: document.getElementById('moduleDisplayName').value.trim(),
        description: document.getElementById('moduleDescription').value.trim(),
        category: document.getElementById('moduleCategory').value,
        table_prefix: document.getElementById('tablePrefix').value.trim(),
        icon: document.getElementById('moduleIcon').value,
        color: document.getElementById('moduleColor').value,
        tags: tags
    };
}

/**
 * Create module
 */
window.createModule = async function() {
    try {
        const formData = getFormData();

        const response = await apiFetch(API_BASE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const module = await response.json();
            showNotification('Module created successfully', 'success');
            closeCreateModuleWizard();
            await loadModules();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create module', 'error');
        }
    } catch (error) {
        console.error('Error creating module:', error);
        showNotification('Error creating module', 'error');
    }
}

/**
 * Validate table prefix
 */
let prefixValidationTimeout;
window.validatePrefix = async function(prefix) {
    clearTimeout(prefixValidationTimeout);

    const validation = document.getElementById('prefixValidation');
    const exampleNames = document.getElementById('exampleTableNames');

    if (!prefix) {
        validation.innerHTML = '';
        return;
    }

    // Update example table names
    exampleNames.innerHTML = `
        <li>• <code class="bg-white px-2 py-1 rounded">${prefix}_employees</code></li>
        <li>• <code class="bg-white px-2 py-1 rounded">${prefix}_departments</code></li>
        <li>• <code class="bg-white px-2 py-1 rounded">${prefix}_positions</code></li>
    `;

    // Check format
    if (!/^[a-z0-9]{1,10}$/.test(prefix)) {
        validation.innerHTML = `
            <div class="flex items-center gap-2 text-red-600">
                <i class="ph-bold ph-x-circle"></i>
                <span>Invalid format. Use lowercase letters and numbers only (max 10 chars).</span>
            </div>
        `;
        return;
    }

    // Check uniqueness (debounced)
    validation.innerHTML = `
        <div class="flex items-center gap-2 text-gray-600">
            <i class="ph-bold ph-circle-notch animate-spin"></i>
            <span>Checking availability...</span>
        </div>
    `;

    prefixValidationTimeout = setTimeout(async () => {
        try {
            const response = await apiFetch(`${API_BASE}/validate/prefix?table_prefix=${encodeURIComponent(prefix)}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.is_valid) {
                validation.innerHTML = `
                    <div class="flex items-center gap-2 text-green-600">
                        <i class="ph-bold ph-check-circle"></i>
                        <span>Prefix is available!</span>
                    </div>
                `;
            } else {
                validation.innerHTML = `
                    <div class="flex items-center gap-2 text-red-600">
                        <i class="ph-bold ph-x-circle"></i>
                        <span>${result.message}</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error validating prefix:', error);
        }
    }, 500);
}

/**
 * Initialize icon picker
 */
function initializeIconPicker() {
    const iconPicker = document.getElementById('iconPicker');
    if (!iconPicker) return;

    iconPicker.innerHTML = ICON_OPTIONS.map(icon => `
        <div class="icon-picker-option ${icon === 'package' ? 'selected' : ''}"
             onclick="selectIcon('${icon}')" data-icon="${icon}">
            <i class="ph-fill ph-${icon}"></i>
        </div>
    `).join('');
}

/**
 * Select icon
 */
window.selectIcon = function(icon) {
    document.querySelectorAll('.icon-picker-option').forEach(el => {
        el.classList.remove('selected');
    });

    document.querySelector(`[data-icon="${icon}"]`).classList.add('selected');
    document.getElementById('moduleIcon').value = icon;

    // Update preview
    updatePreview();
}

/**
 * Initialize color picker
 */
function initializeColorPicker() {
    const colorPicker = document.getElementById('colorPicker');
    if (!colorPicker) return;

    colorPicker.innerHTML = COLOR_OPTIONS.map(color => `
        <div class="color-picker-option ${color === '#3b82f6' ? 'selected' : ''}"
             style="background-color: ${color}"
             onclick="selectColor('${color}')"
             data-color="${color}">
        </div>
    `).join('');
}

/**
 * Select color
 */
window.selectColor = function(color) {
    document.querySelectorAll('.color-picker-option').forEach(el => {
        el.classList.remove('selected');
    });

    document.querySelector(`[data-color="${color}"]`).classList.add('selected');
    document.getElementById('moduleColor').value = color;

    // Update preview
    updatePreview();
}

/**
 * Update module preview
 */
function updatePreview() {
    const displayName = document.getElementById('moduleDisplayName').value || 'Module Name';
    const category = document.getElementById('moduleCategory').value || 'Category';
    const icon = document.getElementById('moduleIcon').value || 'package';
    const color = document.getElementById('moduleColor').value || '#3b82f6';

    document.getElementById('previewName').textContent = displayName;
    document.getElementById('previewCategory').textContent = category;
    document.getElementById('previewIcon').innerHTML = `<i class="ph-fill ph-${icon}"></i>`;
    document.getElementById('previewIcon').style.color = color;
}

// Update preview when inputs change
document.addEventListener('DOMContentLoaded', () => {
    const displayNameInput = document.getElementById('moduleDisplayName');
    const categoryInput = document.getElementById('moduleCategory');

    if (displayNameInput) {
        displayNameInput.addEventListener('input', updatePreview);
    }
    if (categoryInput) {
        categoryInput.addEventListener('change', updatePreview);
    }
});

/**
 * Show module detail
 */
window.showModuleDetail = async function(moduleId) {
    try {
        const response = await apiFetch(`${API_BASE}/${moduleId}`);

        if (response.ok) {
            selectedModule = await response.json();
            displayModuleDetail(selectedModule);
            document.getElementById('moduleDetailModal').classList.remove('hidden');
            document.getElementById('moduleDetailModal').classList.add('flex');
            // Load components asynchronously after modal is shown
            loadModuleComponents(moduleId);
        } else {
            showNotification('Failed to load module details', 'error');
        }
    } catch (error) {
        console.error('Error loading module:', error);
        showNotification('Error loading module details', 'error');
    }
}

/**
 * Display module detail
 */
function displayModuleDetail(module) {
    document.getElementById('detailModuleName').textContent = module.display_name;

    const content = document.getElementById('moduleDetailContent');
    const statusClass = `status-${module.status}`;
    const iconColor = module.color || '#3b82f6';

    content.innerHTML = `
        <div class="space-y-6">
            <!-- Header -->
            <div class="flex items-start gap-4">
                <div class="text-5xl" style="color: ${iconColor}">
                    <i class="ph-fill ph-${module.icon || 'package'}"></i>
                </div>
                <div class="flex-1">
                    <h3 class="text-2xl font-bold text-gray-900">${module.display_name}</h3>
                    <p class="text-gray-600 mt-1">${module.name}</p>
                    <div class="flex items-center gap-3 mt-2">
                        <span class="status-badge ${statusClass}">${module.status}</span>
                        <span class="text-sm text-gray-500">v${module.version}</span>
                    </div>
                </div>
                <div class="flex gap-2">
                    ${module.status === 'draft' ? `
                        <button onclick="publishModule('${module.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
                            <i class="ph-bold ph-upload-simple mr-2"></i>Publish
                        </button>
                    ` : ''}
                    <button onclick="editModule('${module.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                        <i class="ph-bold ph-pencil mr-2"></i>Edit
                        </button>
                    <button onclick="deleteModule('${module.id}')" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
                        <i class="ph-bold ph-trash mr-2"></i>Delete
                    </button>
                </div>
            </div>

            <!-- Description -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 class="font-semibold text-gray-900 mb-2">Description</h4>
                <p class="text-gray-700">${module.description || 'No description provided'}</p>
            </div>

            <!-- Details Grid -->
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-2">Category</h4>
                    <p class="text-gray-700">${module.category || 'Uncategorized'}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-2">Table Prefix</h4>
                    <p class="text-gray-700 font-mono">${module.table_prefix}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-2">Created</h4>
                    <p class="text-gray-700">${formatDateTime(module.created_at)}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-2">Updated</h4>
                    <p class="text-gray-700">${formatDateTime(module.updated_at)}</p>
                </div>
            </div>

            <!-- Tags -->
            ${module.tags && module.tags.length > 0 ? `
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h4 class="font-semibold text-gray-900 mb-2">Tags</h4>
                    <div class="flex flex-wrap gap-2">
                        ${module.tags.map(tag => `
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">${tag}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- Components Section -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="font-semibold text-gray-900">Module Components</h4>
                    <button onclick="refreshComponents('${module.id}')" class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1">
                        <i class="ph ph-arrows-clockwise"></i> Refresh
                    </button>
                </div>
                <div id="moduleComponentsContainer">
                    <div class="text-center py-6 text-gray-500">
                        <i class="ph-bold ph-circle-notch animate-spin text-2xl"></i>
                        <p class="mt-2 text-sm">Loading components...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Load module components from API
 */
async function loadModuleComponents(moduleId) {
    const container = document.getElementById('moduleComponentsContainer');
    if (!container) return;

    try {
        const response = await apiFetch(`${API_BASE}/${moduleId}/components`);

        if (response.ok) {
            const data = await response.json();
            renderComponents(container, data);
        } else {
            container.innerHTML = `
                <div class="text-center py-6 text-red-500">
                    <i class="ph-bold ph-warning text-2xl"></i>
                    <p class="mt-2 text-sm">Failed to load components</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading components:', error);
        container.innerHTML = `
            <div class="text-center py-6 text-red-500">
                <i class="ph-bold ph-warning text-2xl"></i>
                <p class="mt-2 text-sm">Error loading components</p>
            </div>
        `;
    }
}

/**
 * Render components in the container
 */
function renderComponents(container, data) {
    const counts = data.component_counts || {};
    const components = data.components || {};
    const totalCount = Object.values(counts).reduce((sum, c) => sum + c, 0);

    if (totalCount === 0) {
        container.innerHTML = `
            <div class="text-center py-6 text-gray-500">
                <i class="ph-bold ph-cube text-3xl"></i>
                <p class="mt-2 text-sm">No components yet</p>
                <p class="text-xs text-gray-400 mt-1">Create entities, workflows, and more to build this module</p>
            </div>
        `;
        return;
    }

    const componentTypes = [
        { key: 'entities', label: 'Entities', icon: 'table', color: 'blue' },
        { key: 'workflows', label: 'Workflows', icon: 'git-branch', color: 'purple' },
        { key: 'automations', label: 'Automations', icon: 'lightning', color: 'amber' },
        { key: 'lookups', label: 'Lookups', icon: 'list-magnifying-glass', color: 'teal' },
        { key: 'reports', label: 'Reports', icon: 'chart-bar', color: 'green' },
        { key: 'dashboards', label: 'Dashboards', icon: 'squares-four', color: 'rose' }
    ];

    const colorMap = {
        blue: { bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800', icon: 'text-blue-500' },
        purple: { bg: 'bg-purple-50', text: 'text-purple-700', badge: 'bg-purple-100 text-purple-800', icon: 'text-purple-500' },
        amber: { bg: 'bg-amber-50', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-800', icon: 'text-amber-500' },
        teal: { bg: 'bg-teal-50', text: 'text-teal-700', badge: 'bg-teal-100 text-teal-800', icon: 'text-teal-500' },
        green: { bg: 'bg-green-50', text: 'text-green-700', badge: 'bg-green-100 text-green-800', icon: 'text-green-500' },
        rose: { bg: 'bg-rose-50', text: 'text-rose-700', badge: 'bg-rose-100 text-rose-800', icon: 'text-rose-500' }
    };

    let html = `<div class="grid grid-cols-3 gap-3 mb-4">`;
    for (const type of componentTypes) {
        const count = counts[type.key] || 0;
        const colors = colorMap[type.color];
        html += `
            <div class="${colors.bg} rounded-lg p-3 text-center">
                <i class="ph ph-${type.icon} text-xl ${colors.icon}"></i>
                <div class="text-lg font-bold ${colors.text}">${count}</div>
                <div class="text-xs ${colors.text}">${type.label}</div>
            </div>
        `;
    }
    html += `</div>`;

    // List components with items
    const typesWithItems = componentTypes.filter(t => (counts[t.key] || 0) > 0);
    if (typesWithItems.length > 0) {
        html += `<div class="space-y-3">`;
        for (const type of typesWithItems) {
            const items = components[type.key] || [];
            const colors = colorMap[type.color];
            html += `
                <div>
                    <h5 class="text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                        <i class="ph ph-${type.icon} ${colors.icon}"></i> ${type.label}
                    </h5>
                    <div class="flex flex-wrap gap-2">
                        ${items.map(item => `
                            <span class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${colors.badge}">
                                ${item.name}
                            </span>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        html += `</div>`;
    }

    container.innerHTML = html;
}

/**
 * Refresh components for a module
 */
window.refreshComponents = function(moduleId) {
    const container = document.getElementById('moduleComponentsContainer');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-6 text-gray-500">
                <i class="ph-bold ph-circle-notch animate-spin text-2xl"></i>
                <p class="mt-2 text-sm">Loading components...</p>
            </div>
        `;
    }
    loadModuleComponents(moduleId);
}

/**
 * Close module detail modal
 */
window.closeModuleDetail = function() {
    document.getElementById('moduleDetailModal').classList.add('hidden');
    document.getElementById('moduleDetailModal').classList.remove('flex');
    selectedModule = null;
}

/**
 * Publish module
 */
window.publishModule = async function(moduleId) {
    if (!confirm('Are you sure you want to publish this module? It will become active and available for use.')) {
        return;
    }

    try {
        const response = await apiFetch(`${API_BASE}/${moduleId}/publish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Module published successfully', 'success');
            closeModuleDetail();
            await loadModules();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to publish module', 'error');
        }
    } catch (error) {
        console.error('Error publishing module:', error);
        showNotification('Error publishing module', 'error');
    }
}

/**
 * Edit module - open edit modal pre-filled with current data
 */
window.editModule = function(moduleId) {
    const module = selectedModule || allModules.find(m => m.id === moduleId);
    if (!module) {
        showNotification('Module not found', 'error');
        return;
    }

    // Populate form fields
    document.getElementById('editModuleId').value = module.id;
    document.getElementById('editDisplayName').value = module.display_name || '';
    document.getElementById('editDescription').value = module.description || '';
    document.getElementById('editCategory').value = module.category || '';

    // Initialize icon picker for edit modal
    const editIconPicker = document.getElementById('editIconPicker');
    const currentIcon = module.icon || 'package';
    editIconPicker.innerHTML = ICON_OPTIONS.map(icon => `
        <div class="icon-picker-option ${icon === currentIcon ? 'selected' : ''}"
             onclick="selectEditIcon('${icon}')" data-edit-icon="${icon}">
            <i class="ph-fill ph-${icon}"></i>
        </div>
    `).join('');
    document.getElementById('editModuleIcon').value = currentIcon;

    // Initialize color picker for edit modal
    const editColorPicker = document.getElementById('editColorPicker');
    const currentColor = module.color || '#3b82f6';
    editColorPicker.innerHTML = COLOR_OPTIONS.map(color => `
        <div class="color-picker-option ${color === currentColor ? 'selected' : ''}"
             style="background-color: ${color}"
             onclick="selectEditColor('${color}')"
             data-edit-color="${color}">
        </div>
    `).join('');
    document.getElementById('editModuleColor').value = currentColor;

    // Show edit modal
    document.getElementById('editModuleModal').classList.remove('hidden');
    document.getElementById('editModuleModal').classList.add('flex');
}

/**
 * Select icon in edit modal
 */
window.selectEditIcon = function(icon) {
    document.querySelectorAll('[data-edit-icon]').forEach(el => el.classList.remove('selected'));
    document.querySelector(`[data-edit-icon="${icon}"]`).classList.add('selected');
    document.getElementById('editModuleIcon').value = icon;
}

/**
 * Select color in edit modal
 */
window.selectEditColor = function(color) {
    document.querySelectorAll('[data-edit-color]').forEach(el => el.classList.remove('selected'));
    document.querySelector(`[data-edit-color="${color}"]`).classList.add('selected');
    document.getElementById('editModuleColor').value = color;
}

/**
 * Close edit module modal
 */
window.closeEditModule = function() {
    document.getElementById('editModuleModal').classList.add('hidden');
    document.getElementById('editModuleModal').classList.remove('flex');
}

/**
 * Save module changes
 */
window.saveModule = async function() {
    const moduleId = document.getElementById('editModuleId').value;
    const payload = {
        display_name: document.getElementById('editDisplayName').value.trim(),
        description: document.getElementById('editDescription').value.trim(),
        category: document.getElementById('editCategory').value,
        icon: document.getElementById('editModuleIcon').value,
        color: document.getElementById('editModuleColor').value
    };

    if (!payload.display_name) {
        showNotification('Display name is required', 'error');
        return;
    }

    try {
        const response = await apiFetch(`${API_BASE}/${moduleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showNotification('Module updated successfully', 'success');
            closeEditModule();
            closeModuleDetail();
            await loadModules();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update module', 'error');
        }
    } catch (error) {
        console.error('Error updating module:', error);
        showNotification('Error updating module', 'error');
    }
}

/**
 * Delete module
 */
window.deleteModule = async function(moduleId) {
    if (!confirm('Are you sure you want to delete this module? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await apiFetch(`${API_BASE}/${moduleId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Module deleted successfully', 'success');
            closeModuleDetail();
            await loadModules();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to delete module', 'error');
        }
    } catch (error) {
        console.error('Error deleting module:', error);
        showNotification('Error deleting module', 'error');
    }
}

/**
 * Reset form
 */
function resetForm() {
    document.getElementById('createModuleForm').reset();
    document.getElementById('prefixValidation').innerHTML = '';
    currentStep = 1;

    // Reset icon and color to defaults
    selectIcon('package');
    selectColor('#3b82f6');
    updatePreview();
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced with toast notifications
    alert(message);
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}
