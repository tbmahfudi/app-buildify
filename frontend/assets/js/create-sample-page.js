/**
 * Script to programmatically create a sample page with API integration
 */

export async function createSampleAPIPage() {
    const token = localStorage.getItem('token');

    if (!token) {
        console.error('No authentication token found');
        alert('Please login first');
        return;
    }

    // Define the sample page data
    const samplePageData = {
        "css": [
            {
                "selectors": ["#iojr"],
                "style": {
                    "padding": "20px 10px 10px 10px",
                    "background-color": "rgb(248, 249, 250)"
                }
            }
        ],
        "styles": [],
        "pages": [
            {
                "frames": [
                    {
                        "component": {
                            "type": "wrapper",
                            "stylable": [
                                "background",
                                "background-color",
                                "background-image",
                                "background-repeat",
                                "background-attachment",
                                "background-position",
                                "background-size"
                            ],
                            "components": [
                                {
                                    "tagName": "section",
                                    "attributes": {
                                        "data-component": "flex-section",
                                        "id": "iojr",
                                        "class": "py-12 px-4"
                                    },
                                    "components": [
                                        {
                                            "tagName": "div",
                                            "attributes": {
                                                "class": "max-w-7xl mx-auto"
                                            },
                                            "components": [
                                                {
                                                    "tagName": "h1",
                                                    "type": "text",
                                                    "attributes": {
                                                        "class": "text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8 text-center"
                                                    },
                                                    "components": [
                                                        {
                                                            "type": "textnode",
                                                            "content": "API Integration Demo"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "tagName": "p",
                                                    "type": "text",
                                                    "attributes": {
                                                        "class": "text-lg text-gray-600 dark:text-gray-400 mb-12 text-center"
                                                    },
                                                    "components": [
                                                        {
                                                            "type": "textnode",
                                                            "content": "This page demonstrates real-time API integration with backend services"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "tagName": "div",
                                                    "attributes": {
                                                        "class": "grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12"
                                                    },
                                                    "components": [
                                                        {
                                                            "type": "api-datatable",
                                                            "attributes": {
                                                                "data-component": "api-datatable",
                                                                "data-api-entity": "companies",
                                                                "data-api-endpoint": "/api/v1/data/companies/list"
                                                            }
                                                        },
                                                        {
                                                            "type": "api-form",
                                                            "attributes": {
                                                                "data-component": "api-form",
                                                                "data-api-endpoint": "/api/v1/data/companies",
                                                                "data-api-method": "POST"
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    "tagName": "div",
                                                    "attributes": {
                                                        "class": "text-center"
                                                    },
                                                    "components": [
                                                        {
                                                            "type": "api-button",
                                                            "attributes": {
                                                                "data-component": "api-button",
                                                                "data-api-endpoint": "/api/v1/data/users/list",
                                                                "data-api-method": "POST",
                                                                "data-button-text": "Fetch Users",
                                                                "class": "px-8 py-4 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition text-lg"
                                                            },
                                                            "content": "Fetch Users"
                                                        },
                                                        {
                                                            "tagName": "div",
                                                            "attributes": {
                                                                "id": "api-result",
                                                                "class": "mt-6"
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ],
                "id": "sample-api-page"
            }
        ]
    };

    // Generate HTML and CSS from the page data
    const htmlOutput = generateHTML(samplePageData);
    const cssOutput = generateCSS(samplePageData);

    // Prepare the page metadata
    const pagePayload = {
        name: "API Integration Demo",
        slug: "api-demo",
        description: "Sample page demonstrating backend API integration with real-time data loading",
        module_name: "core",
        route_path: "/api-demo",
        grapejs_data: samplePageData,
        html_output: htmlOutput,
        css_output: cssOutput,
        js_output: "",
        menu_label: "API Demo",
        menu_icon: "ph-duotone ph-plugs-connected",
        menu_parent: null,
        menu_order: 100,
        show_in_menu: true,
        permission_code: "api:demo:view",
        permission_scope: "company"
    };

    try {
        // Create the page
        console.log('Creating sample page...');
        const createResponse = await fetch('/api/v1/builder/pages/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(pagePayload)
        });

        if (!createResponse.ok) {
            const error = await createResponse.json();
            throw new Error(error.detail || 'Failed to create page');
        }

        const createdPage = await createResponse.json();
        console.log('Page created:', createdPage);

        // Publish the page
        console.log('Publishing page...');
        const publishResponse = await fetch(`/api/v1/builder/pages/${createdPage.id}/publish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                commit_message: 'Initial publication of API Integration Demo page'
            })
        });

        if (!publishResponse.ok) {
            throw new Error('Failed to publish page');
        }

        const publishedPage = await publishResponse.json();
        console.log('Page published:', publishedPage);

        alert(`✅ Success!\n\nSample page created and published!\n\nPage ID: ${createdPage.id}\nRoute: ${createdPage.route_path}\nPublished: ${createdPage.published}`);

        return createdPage;

    } catch (error) {
        console.error('Error creating sample page:', error);
        alert(`❌ Error: ${error.message}`);
        throw error;
    }
}

/**
 * Generate HTML from GrapeJS data
 */
function generateHTML(grapesjsData) {
    // In a real implementation, GrapeJS would handle this
    // For now, return a simple HTML structure
    return `
        <section id="iojr" class="py-12 px-4" data-component="flex-section">
            <div class="max-w-7xl mx-auto">
                <h1 class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8 text-center">
                    API Integration Demo
                </h1>
                <p class="text-lg text-gray-600 dark:text-gray-400 mb-12 text-center">
                    This page demonstrates real-time API integration with backend services
                </p>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                    <div data-component="api-datatable" data-api-entity="companies" data-api-endpoint="/api/v1/data/companies/list"></div>
                    <form data-component="api-form" data-api-endpoint="/api/v1/data/companies" data-api-method="POST"></form>
                </div>
                <div class="text-center">
                    <button data-component="api-button" data-api-endpoint="/api/v1/data/users/list" data-api-method="POST" data-button-text="Fetch Users" class="px-8 py-4 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition text-lg">
                        Fetch Users
                    </button>
                    <div id="api-result" class="mt-6"></div>
                </div>
            </div>
        </section>
    `;
}

/**
 * Generate CSS from GrapeJS data
 */
function generateCSS(grapesjsData) {
    let css = '';
    if (grapesjsData.css) {
        grapesjsData.css.forEach(rule => {
            const selector = rule.selectors.join(', ');
            const styles = Object.entries(rule.style)
                .map(([prop, value]) => `  ${prop}: ${value};`)
                .join('\n');
            css += `${selector} {\n${styles}\n}\n\n`;
        });
    }
    return css;
}

// Auto-execute if this script is loaded in a page with a specific trigger
if (window.location.hash === '#create-sample-page') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (confirm('Create a sample API integration page?')) {
                createSampleAPIPage();
            }
        }, 1000);
    });
}
