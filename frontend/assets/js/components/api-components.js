/**
 * API-Enabled Components for GrapeJS
 *
 * Components that can interact with backend APIs
 */

/**
 * Register API-enabled components with GrapeJS editor
 */
export function registerAPIComponents(editor) {
    console.log('Registering API-enabled components...');

    registerAPIDataTable(editor);
    registerAPIForm(editor);
    registerAPIButton(editor);

    console.log('API components registered');
}

/**
 * API Data Table - Loads data from backend API
 */
function registerAPIDataTable(editor) {
    editor.BlockManager.add('api-datatable', {
        label: '<div class="text-center"><i class="ph-duotone ph-database text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">API Table</div></div>',
        category: 'API Components',
        content: {
            type: 'api-datatable'
        }
    });

    editor.DomComponents.addType('api-datatable', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'api-datatable',
                    'data-api-entity': 'companies',
                    'data-api-endpoint': '/api/v1/data/companies/list',
                    class: 'api-datatable-container'
                },
                components: `
                    <div class="bg-white dark:bg-slate-800 rounded-lg shadow">
                        <div class="p-4 border-b border-gray-200 dark:border-slate-700">
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Data Table</h3>
                            <input type="text" placeholder="Search..."
                                   class="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg"
                                   data-search-input />
                        </div>
                        <div class="overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
                                <thead class="bg-gray-50 dark:bg-slate-900">
                                    <tr data-table-header>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Loading...</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white dark:bg-slate-800 divide-y divide-gray-200" data-table-body>
                                    <tr>
                                        <td class="px-6 py-4 text-sm text-gray-500">Loading data...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="p-4 border-t border-gray-200 flex justify-between items-center" data-pagination>
                            <span class="text-sm text-gray-700 dark:text-gray-300">Page <span data-current-page>1</span> of <span data-total-pages>1</span></span>
                            <div class="flex gap-2">
                                <button class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" data-prev-page>Previous</button>
                                <button class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" data-next-page>Next</button>
                            </div>
                        </div>
                    </div>
                `,
                script: function() {
                    const container = this;
                    const entity = container.getAttribute('data-api-entity') || 'companies';
                    const endpoint = container.getAttribute('data-api-endpoint') || '/api/v1/data/companies/list';

                    let currentPage = 1;
                    const pageSize = 10;

                    // Get DOM elements
                    const searchInput = container.querySelector('[data-search-input]');
                    const tableHeader = container.querySelector('[data-table-header]');
                    const tableBody = container.querySelector('[data-table-body]');
                    const currentPageSpan = container.querySelector('[data-current-page]');
                    const totalPagesSpan = container.querySelector('[data-total-pages]');
                    const prevBtn = container.querySelector('[data-prev-page]');
                    const nextBtn = container.querySelector('[data-next-page]');

                    async function loadData(page = 1, search = '') {
                        try {
                            const token = localStorage.getItem('token');
                            const response = await fetch(endpoint, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({
                                    page: page,
                                    page_size: pageSize,
                                    search: search,
                                    filters: [],
                                    sort: []
                                })
                            });

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const data = await response.json();
                            renderTable(data);
                        } catch (error) {
                            console.error('Error loading data:', error);
                            tableBody.innerHTML = `<tr><td colspan="10" class="px-6 py-4 text-center text-red-500">Error: ${error.message}</td></tr>`;
                        }
                    }

                    function renderTable(data) {
                        if (!data.rows || data.rows.length === 0) {
                            tableBody.innerHTML = '<tr><td class="px-6 py-4 text-center text-gray-500">No data found</td></tr>';
                            return;
                        }

                        // Render headers
                        const columns = Object.keys(data.rows[0]);
                        tableHeader.innerHTML = columns.map(col =>
                            `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${col}</th>`
                        ).join('');

                        // Render rows
                        tableBody.innerHTML = data.rows.map(row =>
                            '<tr class="hover:bg-gray-50 dark:hover:bg-slate-700">' +
                            columns.map(col =>
                                `<td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-300">${row[col] || ''}</td>`
                            ).join('') +
                            '</tr>'
                        ).join('');

                        // Update pagination
                        const totalPages = Math.ceil(data.total / pageSize);
                        currentPageSpan.textContent = currentPage;
                        totalPagesSpan.textContent = totalPages;

                        prevBtn.disabled = currentPage <= 1;
                        nextBtn.disabled = currentPage >= totalPages;
                    }

                    // Event listeners
                    let searchTimeout;
                    searchInput.addEventListener('input', (e) => {
                        clearTimeout(searchTimeout);
                        searchTimeout = setTimeout(() => {
                            currentPage = 1;
                            loadData(currentPage, e.target.value);
                        }, 300);
                    });

                    prevBtn.addEventListener('click', () => {
                        if (currentPage > 1) {
                            currentPage--;
                            loadData(currentPage, searchInput.value);
                        }
                    });

                    nextBtn.addEventListener('click', () => {
                        currentPage++;
                        loadData(currentPage, searchInput.value);
                    });

                    // Initial load
                    loadData(currentPage);
                },
                traits: [
                    {
                        type: 'select',
                        label: 'Entity',
                        name: 'data-api-entity',
                        options: [
                            { id: 'companies', name: 'Companies' },
                            { id: 'branches', name: 'Branches' },
                            { id: 'departments', name: 'Departments' },
                            { id: 'users', name: 'Users' }
                        ],
                        changeProp: 1
                    },
                    {
                        type: 'text',
                        label: 'API Endpoint',
                        name: 'data-api-endpoint',
                        changeProp: 1
                    }
                ]
            }
        }
    });
}

/**
 * API Form - Submit data to backend API
 */
function registerAPIForm(editor) {
    editor.BlockManager.add('api-form', {
        label: '<div class="text-center"><i class="ph-duotone ph-paper-plane-tilt text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">API Form</div></div>',
        category: 'API Components',
        content: {
            type: 'api-form'
        }
    });

    editor.DomComponents.addType('api-form', {
        model: {
            defaults: {
                tagName: 'form',
                attributes: {
                    'data-component': 'api-form',
                    'data-api-endpoint': '/api/v1/data/companies',
                    'data-api-method': 'POST',
                    class: 'api-form max-w-2xl mx-auto'
                },
                components: `
                    <div class="bg-white dark:bg-slate-800 rounded-lg shadow p-6 space-y-4">
                        <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">Create New Record</h3>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                            <input type="text" name="name" required
                                   class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Code</label>
                            <input type="text" name="code" required
                                   class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                            <textarea name="description" rows="3"
                                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
                        </div>

                        <div class="flex gap-2">
                            <button type="submit"
                                    class="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition">
                                Submit
                            </button>
                            <button type="reset"
                                    class="px-6 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition">
                                Reset
                            </button>
                        </div>

                        <div data-form-message class="hidden p-4 rounded-lg"></div>
                    </div>
                `,
                script: function() {
                    const form = this;
                    const endpoint = form.getAttribute('data-api-endpoint') || '/api/v1/data/companies';
                    const method = form.getAttribute('data-api-method') || 'POST';
                    const messageDiv = form.querySelector('[data-form-message]');

                    form.addEventListener('submit', async (e) => {
                        e.preventDefault();

                        // Collect form data
                        const formData = new FormData(form);
                        const data = {};
                        formData.forEach((value, key) => {
                            data[key] = value;
                        });

                        try {
                            const token = localStorage.getItem('token');
                            const response = await fetch(endpoint, {
                                method: method,
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({ data: data })
                            });

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const result = await response.json();

                            // Show success message
                            messageDiv.className = 'p-4 rounded-lg bg-green-50 border border-green-200 text-green-800';
                            messageDiv.textContent = 'Success! Record created.';
                            messageDiv.classList.remove('hidden');

                            // Reset form
                            form.reset();

                            // Hide message after 5 seconds
                            setTimeout(() => {
                                messageDiv.classList.add('hidden');
                            }, 5000);

                        } catch (error) {
                            console.error('Error submitting form:', error);
                            messageDiv.className = 'p-4 rounded-lg bg-red-50 border border-red-200 text-red-800';
                            messageDiv.textContent = `Error: ${error.message}`;
                            messageDiv.classList.remove('hidden');
                        }
                    });
                },
                traits: [
                    {
                        type: 'text',
                        label: 'API Endpoint',
                        name: 'data-api-endpoint',
                        placeholder: '/api/v1/data/companies',
                        changeProp: 1
                    },
                    {
                        type: 'select',
                        label: 'HTTP Method',
                        name: 'data-api-method',
                        options: [
                            { id: 'POST', name: 'POST' },
                            { id: 'PUT', name: 'PUT' },
                            { id: 'PATCH', name: 'PATCH' }
                        ],
                        changeProp: 1
                    }
                ]
            }
        }
    });
}

/**
 * API Action Button - Trigger API calls
 */
function registerAPIButton(editor) {
    editor.BlockManager.add('api-button', {
        label: '<div class="text-center"><i class="ph-duotone ph-lightning text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">API Button</div></div>',
        category: 'API Components',
        content: {
            type: 'api-button'
        }
    });

    editor.DomComponents.addType('api-button', {
        model: {
            defaults: {
                tagName: 'button',
                attributes: {
                    'data-component': 'api-button',
                    'data-api-endpoint': '/api/v1/data/companies/list',
                    'data-api-method': 'POST',
                    class: 'px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition'
                },
                content: 'Fetch Data',
                script: function() {
                    const button = this;
                    const endpoint = button.getAttribute('data-api-endpoint');
                    const method = button.getAttribute('data-api-method') || 'POST';
                    const resultContainer = button.getAttribute('data-result-container');

                    button.addEventListener('click', async (e) => {
                        e.preventDefault();

                        button.disabled = true;
                        button.textContent = 'Loading...';

                        try {
                            const token = localStorage.getItem('token');
                            const response = await fetch(endpoint, {
                                method: method,
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: method !== 'GET' ? JSON.stringify({
                                    page: 1,
                                    page_size: 10,
                                    filters: [],
                                    sort: []
                                }) : undefined
                            });

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const data = await response.json();
                            console.log('API Response:', data);

                            // If result container specified, display data there
                            if (resultContainer) {
                                const container = document.querySelector(resultContainer);
                                if (container) {
                                    container.innerHTML = `<pre class="p-4 bg-gray-100 rounded overflow-auto">${JSON.stringify(data, null, 2)}</pre>`;
                                }
                            }

                            alert(`Success! Received ${data.rows?.length || 0} records`);

                        } catch (error) {
                            console.error('Error calling API:', error);
                            alert(`Error: ${error.message}`);
                        } finally {
                            button.disabled = false;
                            button.textContent = button.getAttribute('data-button-text') || 'Fetch Data';
                        }
                    });
                },
                traits: [
                    {
                        type: 'text',
                        label: 'Button Text',
                        name: 'data-button-text',
                        changeProp: 1
                    },
                    {
                        type: 'text',
                        label: 'API Endpoint',
                        name: 'data-api-endpoint',
                        placeholder: '/api/v1/data/companies/list',
                        changeProp: 1
                    },
                    {
                        type: 'select',
                        label: 'HTTP Method',
                        name: 'data-api-method',
                        options: [
                            { id: 'GET', name: 'GET' },
                            { id: 'POST', name: 'POST' },
                            { id: 'PUT', name: 'PUT' },
                            { id: 'DELETE', name: 'DELETE' }
                        ],
                        changeProp: 1
                    },
                    {
                        type: 'text',
                        label: 'Result Container (CSS Selector)',
                        name: 'data-result-container',
                        placeholder: '#result-div',
                        changeProp: 1
                    }
                ]
            }
        }
    });
}
