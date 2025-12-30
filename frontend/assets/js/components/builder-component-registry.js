/**
 * Component Registry for GrapeJS
 *
 * Registers all available UI components as GrapeJS blocks
 * Includes: Basic UI components (7) + Flex Layout components (12) + API components (3) = 22 total
 */

import { registerAPIComponents } from './api-components.js';

export async function registerComponents(editor) {
    console.log('Registering components...');

    // Register Basic UI Components
    registerButton(editor);
    registerInput(editor);
    registerTextarea(editor);
    registerSelect(editor);
    registerCard(editor);
    registerBadge(editor);
    registerAlert(editor);

    // Register Layout Components
    registerFlexContainer(editor);
    registerFlexSection(editor);
    registerFlexStack(editor);
    registerFlexGrid(editor);
    registerFlexCluster(editor);
    registerFlexMasonry(editor);
    registerFlexSidebar(editor);
    registerFlexToolbar(editor);
    registerFlexSplitPane(editor);

    // Register Data Components
    registerFlexModal(editor);
    registerDataTable(editor);
    registerDynamicForm(editor);

    // Register API Components
    registerAPIComponents(editor);

    console.log('All components registered');
}

// ==================== BASIC UI COMPONENTS ====================

function registerButton(editor) {
    editor.BlockManager.add('ui-button', {
        label: '<div class="text-center"><i class="ph-duotone ph-cursor-click text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Button</div></div>',
        category: 'Basic Forms',
        content: {
            type: 'ui-button',
            content: 'Click Me',
            attributes: {
                'data-variant': 'primary',
                'data-size': 'md'
            }
        }
    });

    editor.DomComponents.addType('ui-button', {
        model: {
            defaults: {
                tagName: 'button',
                draggable: true,
                droppable: false,
                attributes: { class: 'inline-flex items-center justify-center px-4 py-2 text-base font-medium rounded-lg transition-all bg-blue-600 hover:bg-blue-700 text-white' },
                traits: [
                    { type: 'text', label: 'Text', name: 'content', changeProp: 1 },
                    {
                        type: 'select',
                        label: 'Variant',
                        name: 'data-variant',
                        options: [
                            { id: 'primary', name: 'Primary' },
                            { id: 'secondary', name: 'Secondary' },
                            { id: 'success', name: 'Success' },
                            { id: 'danger', name: 'Danger' },
                            { id: 'warning', name: 'Warning' },
                            { id: 'ghost', name: 'Ghost' },
                            { id: 'outline', name: 'Outline' }
                        ],
                        changeProp: 1
                    },
                    {
                        type: 'select',
                        label: 'Size',
                        name: 'data-size',
                        options: [
                            { id: 'sm', name: 'Small' },
                            { id: 'md', name: 'Medium' },
                            { id: 'lg', name: 'Large' },
                            { id: 'xl', name: 'Extra Large' }
                        ],
                        changeProp: 1
                    },
                    { type: 'checkbox', label: 'Disabled', name: 'disabled' },
                    { type: 'checkbox', label: 'Full Width', name: 'data-full-width' }
                ]
            }
        }
    });
}

function registerInput(editor) {
    editor.BlockManager.add('ui-input', {
        label: '<div class="text-center"><i class="ph-duotone ph-text-aa text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Input</div></div>',
        category: 'Basic Forms',
        content: {
            type: 'ui-input-wrapper'
        }
    });

    editor.DomComponents.addType('ui-input-wrapper', {
        model: {
            defaults: {
                tagName: 'div',
                components: [
                    {
                        tagName: 'label',
                        type: 'text',
                        content: 'Label',
                        attributes: { class: 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1' }
                    },
                    {
                        tagName: 'input',
                        type: 'ui-input',
                        attributes: {
                            type: 'text',
                            placeholder: 'Enter text...',
                            class: 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-base'
                        }
                    }
                ],
                traits: [
                    { type: 'text', label: 'Label', name: 'data-label', changeProp: 1 },
                    { type: 'text', label: 'Placeholder', name: 'data-placeholder', changeProp: 1 },
                    {
                        type: 'select',
                        label: 'Type',
                        name: 'data-input-type',
                        options: [
                            { id: 'text', name: 'Text' },
                            { id: 'email', name: 'Email' },
                            { id: 'password', name: 'Password' },
                            { id: 'number', name: 'Number' },
                            { id: 'date', name: 'Date' },
                            { id: 'tel', name: 'Phone' }
                        ],
                        changeProp: 1
                    },
                    { type: 'checkbox', label: 'Required', name: 'data-required' },
                    { type: 'checkbox', label: 'Disabled', name: 'data-disabled' }
                ]
            }
        }
    });

    editor.DomComponents.addType('ui-input', {
        isComponent: el => el.tagName === 'INPUT',
        model: {
            defaults: {
                traits: ['type', 'placeholder', 'name', 'required', 'disabled']
            }
        }
    });
}

function registerTextarea(editor) {
    editor.BlockManager.add('ui-textarea', {
        label: '<div class="text-center"><i class="ph-duotone ph-text-align-left text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Textarea</div></div>',
        category: 'Basic Forms',
        content: {
            tagName: 'textarea',
            attributes: {
                placeholder: 'Enter text...',
                rows: 4,
                class: 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-base'
            },
            traits: ['placeholder', 'rows', 'required', 'disabled']
        }
    });
}

function registerSelect(editor) {
    editor.BlockManager.add('ui-select', {
        label: '<div class="text-center"><i class="ph-duotone ph-caret-down text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Select</div></div>',
        category: 'Basic Forms',
        content: {
            tagName: 'select',
            components: [
                { tagName: 'option', content: 'Option 1', attributes: { value: '1' } },
                { tagName: 'option', content: 'Option 2', attributes: { value: '2' } },
                { tagName: 'option', content: 'Option 3', attributes: { value: '3' } }
            ],
            attributes: {
                class: 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-base'
            },
            traits: ['name', 'required', 'disabled']
        }
    });
}

function registerCard(editor) {
    editor.BlockManager.add('ui-card', {
        label: '<div class="text-center"><i class="ph-duotone ph-card text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Card</div></div>',
        category: 'Display',
        content: {
            type: 'ui-card'
        }
    });

    editor.DomComponents.addType('ui-card', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    class: 'bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg overflow-hidden p-6'
                },
                components: [
                    {
                        tagName: 'h3',
                        type: 'text',
                        content: 'Card Title',
                        attributes: { class: 'text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2' }
                    },
                    {
                        tagName: 'p',
                        type: 'text',
                        content: 'Card content goes here...',
                        attributes: { class: 'text-gray-700 dark:text-gray-300' }
                    }
                ],
                traits: [
                    {
                        type: 'select',
                        label: 'Variant',
                        name: 'data-variant',
                        options: [
                            { id: 'default', name: 'Default' },
                            { id: 'bordered', name: 'Bordered' },
                            { id: 'elevated', name: 'Elevated' }
                        ]
                    },
                    {
                        type: 'select',
                        label: 'Padding',
                        name: 'data-padding',
                        options: [
                            { id: 'none', name: 'None' },
                            { id: 'sm', name: 'Small' },
                            { id: 'md', name: 'Medium' },
                            { id: 'lg', name: 'Large' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerBadge(editor) {
    editor.BlockManager.add('ui-badge', {
        label: '<div class="text-center"><i class="ph-duotone ph-tag text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Badge</div></div>',
        category: 'Display',
        content: {
            type: 'ui-badge',
            content: 'Badge'
        }
    });

    editor.DomComponents.addType('ui-badge', {
        model: {
            defaults: {
                tagName: 'span',
                attributes: {
                    class: 'inline-flex items-center px-2.5 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800'
                },
                traits: [
                    { type: 'text', label: 'Text', name: 'content', changeProp: 1 },
                    {
                        type: 'select',
                        label: 'Variant',
                        name: 'data-variant',
                        options: [
                            { id: 'default', name: 'Default' },
                            { id: 'primary', name: 'Primary' },
                            { id: 'success', name: 'Success' },
                            { id: 'warning', name: 'Warning' },
                            { id: 'danger', name: 'Danger' },
                            { id: 'info', name: 'Info' }
                        ]
                    },
                    {
                        type: 'select',
                        label: 'Size',
                        name: 'data-size',
                        options: [
                            { id: 'sm', name: 'Small' },
                            { id: 'md', name: 'Medium' },
                            { id: 'lg', name: 'Large' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerAlert(editor) {
    editor.BlockManager.add('ui-alert', {
        label: '<div class="text-center"><i class="ph-duotone ph-info text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Alert</div></div>',
        category: 'Display',
        content: {
            type: 'ui-alert'
        }
    });

    editor.DomComponents.addType('ui-alert', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    class: 'rounded-lg border p-4 bg-blue-50 border-blue-200 text-blue-800'
                },
                components: [
                    {
                        tagName: 'p',
                        type: 'text',
                        content: 'This is an alert message',
                        attributes: { class: 'text-sm' }
                    }
                ],
                traits: [
                    {
                        type: 'select',
                        label: 'Variant',
                        name: 'data-variant',
                        options: [
                            { id: 'info', name: 'Info' },
                            { id: 'success', name: 'Success' },
                            { id: 'warning', name: 'Warning' },
                            { id: 'danger', name: 'Danger' }
                        ]
                    },
                    { type: 'checkbox', label: 'Dismissible', name: 'data-dismissible' },
                    { type: 'checkbox', label: 'Show Icon', name: 'data-show-icon' }
                ]
            }
        }
    });
}

// ==================== LAYOUT COMPONENTS ====================

function registerFlexContainer(editor) {
    editor.BlockManager.add('flex-container', {
        label: '<div class="text-center"><i class="ph-duotone ph-container text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Container</div></div>',
        category: 'Containers',
        content: {
            type: 'flex-container'
        }
    });

    editor.DomComponents.addType('flex-container', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-container',
                    class: 'mx-auto px-4 sm:px-6 lg:px-8',
                    style: 'max-width: 1280px;'
                },
                components: '<p class="text-gray-600">Drop content here...</p>',
                droppable: true,
                traits: [
                    {
                        type: 'select',
                        label: 'Preset',
                        name: 'data-preset',
                        options: [
                            { id: 'narrow', name: 'Narrow (768px)' },
                            { id: 'standard', name: 'Standard (1280px)' },
                            { id: 'wide', name: 'Wide (1536px)' },
                            { id: 'full', name: 'Full Width' }
                        ]
                    },
                    {
                        type: 'select',
                        label: 'Alignment',
                        name: 'data-align',
                        options: [
                            { id: 'left', name: 'Left' },
                            { id: 'center', name: 'Center' },
                            { id: 'right', name: 'Right' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerFlexSection(editor) {
    editor.BlockManager.add('flex-section', {
        label: '<div class="text-center"><i class="ph-duotone ph-layout text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Section</div></div>',
        category: 'Containers',
        content: {
            type: 'flex-section'
        }
    });

    editor.DomComponents.addType('flex-section', {
        model: {
            defaults: {
                tagName: 'section',
                attributes: {
                    'data-component': 'flex-section',
                    class: 'py-12 px-4'
                },
                components: '<div class="max-w-7xl mx-auto"><p class="text-gray-600">Section content here...</p></div>',
                droppable: true,
                traits: [
                    {
                        type: 'select',
                        label: 'Variant',
                        name: 'data-variant',
                        options: [
                            { id: 'hero', name: 'Hero' },
                            { id: 'content', name: 'Content' },
                            { id: 'feature', name: 'Feature' },
                            { id: 'cta', name: 'Call to Action' },
                            { id: 'footer', name: 'Footer' }
                        ]
                    },
                    { type: 'text', label: 'Background Color', name: 'data-bg-color' },
                    { type: 'text', label: 'Min Height', name: 'data-min-height', placeholder: '500px' }
                ]
            }
        }
    });
}

function registerFlexStack(editor) {
    editor.BlockManager.add('flex-stack', {
        label: '<div class="text-center"><i class="ph-duotone ph-rows text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Stack</div></div>',
        category: 'Layout',
        content: {
            type: 'flex-stack'
        }
    });

    editor.DomComponents.addType('flex-stack', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-stack',
                    class: 'flex flex-col gap-4'
                },
                components: [
                    '<div class="p-4 bg-gray-100 rounded">Stack Item 1</div>',
                    '<div class="p-4 bg-gray-100 rounded">Stack Item 2</div>',
                    '<div class="p-4 bg-gray-100 rounded">Stack Item 3</div>'
                ],
                droppable: true,
                traits: [
                    {
                        type: 'select',
                        label: 'Direction',
                        name: 'data-direction',
                        options: [
                            { id: 'vertical', name: 'Vertical' },
                            { id: 'horizontal', name: 'Horizontal' }
                        ],
                        changeProp: 1
                    },
                    {
                        type: 'select',
                        label: 'Gap',
                        name: 'data-gap',
                        options: [
                            { id: '0', name: 'None' },
                            { id: '2', name: 'Small (0.5rem)' },
                            { id: '4', name: 'Medium (1rem)' },
                            { id: '6', name: 'Large (1.5rem)' },
                            { id: '8', name: 'XLarge (2rem)' }
                        ],
                        changeProp: 1
                    },
                    {
                        type: 'select',
                        label: 'Align Items',
                        name: 'data-align',
                        options: [
                            { id: 'start', name: 'Start' },
                            { id: 'center', name: 'Center' },
                            { id: 'end', name: 'End' },
                            { id: 'stretch', name: 'Stretch' },
                            { id: 'baseline', name: 'Baseline' }
                        ]
                    },
                    {
                        type: 'select',
                        label: 'Justify',
                        name: 'data-justify',
                        options: [
                            { id: 'start', name: 'Start' },
                            { id: 'center', name: 'Center' },
                            { id: 'end', name: 'End' },
                            { id: 'between', name: 'Space Between' },
                            { id: 'around', name: 'Space Around' },
                            { id: 'evenly', name: 'Space Evenly' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerFlexGrid(editor) {
    editor.BlockManager.add('flex-grid', {
        label: '<div class="text-center"><i class="ph-duotone ph-grid-four text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Grid</div></div>',
        category: 'Layout',
        content: {
            type: 'flex-grid'
        }
    });

    editor.DomComponents.addType('flex-grid', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-grid',
                    class: 'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6'
                },
                components: [
                    '<div class="p-4 bg-gray-100 rounded">Grid Item 1</div>',
                    '<div class="p-4 bg-gray-100 rounded">Grid Item 2</div>',
                    '<div class="p-4 bg-gray-100 rounded">Grid Item 3</div>',
                    '<div class="p-4 bg-gray-100 rounded">Grid Item 4</div>'
                ],
                droppable: true,
                traits: [
                    { type: 'number', label: 'Columns (XS)', name: 'data-columns-xs', placeholder: '1' },
                    { type: 'number', label: 'Columns (SM)', name: 'data-columns-sm', placeholder: '2' },
                    { type: 'number', label: 'Columns (MD)', name: 'data-columns-md', placeholder: '3' },
                    { type: 'number', label: 'Columns (LG)', name: 'data-columns-lg', placeholder: '4' },
                    {
                        type: 'select',
                        label: 'Gap',
                        name: 'data-gap',
                        options: [
                            { id: '2', name: 'Small' },
                            { id: '4', name: 'Medium' },
                            { id: '6', name: 'Large' },
                            { id: '8', name: 'XLarge' }
                        ]
                    },
                    { type: 'checkbox', label: 'Equal Height', name: 'data-equal-height' },
                    { type: 'checkbox', label: 'Dense Packing', name: 'data-dense' }
                ]
            }
        }
    });
}

function registerFlexCluster(editor) {
    editor.BlockManager.add('flex-cluster', {
        label: '<div class="text-center"><i class="ph-duotone ph-dots-three text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Cluster</div></div>',
        category: 'Layout',
        content: {
            type: 'flex-cluster'
        }
    });

    editor.DomComponents.addType('flex-cluster', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-cluster',
                    class: 'flex flex-wrap gap-2'
                },
                components: [
                    '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Tag 1</span>',
                    '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Tag 2</span>',
                    '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Tag 3</span>'
                ],
                droppable: true,
                traits: [
                    {
                        type: 'select',
                        label: 'Gap',
                        name: 'data-gap',
                        options: [
                            { id: '1', name: 'XSmall' },
                            { id: '2', name: 'Small' },
                            { id: '3', name: 'Medium' },
                            { id: '4', name: 'Large' }
                        ]
                    },
                    {
                        type: 'select',
                        label: 'Justify',
                        name: 'data-justify',
                        options: [
                            { id: 'start', name: 'Start' },
                            { id: 'center', name: 'Center' },
                            { id: 'end', name: 'End' },
                            { id: 'between', name: 'Space Between' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerFlexMasonry(editor) {
    editor.BlockManager.add('flex-masonry', {
        label: '<div class="text-center"><i class="ph-duotone ph-images text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Masonry</div></div>',
        category: 'Layout',
        content: {
            type: 'flex-masonry'
        }
    });

    editor.DomComponents.addType('flex-masonry', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-masonry',
                    class: 'columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-4'
                },
                components: [
                    '<div class="mb-4 break-inside-avoid"><img src="https://via.placeholder.com/300x400" class="w-full rounded" /></div>',
                    '<div class="mb-4 break-inside-avoid"><img src="https://via.placeholder.com/300x500" class="w-full rounded" /></div>',
                    '<div class="mb-4 break-inside-avoid"><img src="https://via.placeholder.com/300x300" class="w-full rounded" /></div>'
                ],
                droppable: true,
                traits: [
                    { type: 'number', label: 'Columns (XS)', name: 'data-columns-xs', placeholder: '1' },
                    { type: 'number', label: 'Columns (SM)', name: 'data-columns-sm', placeholder: '2' },
                    { type: 'number', label: 'Columns (MD)', name: 'data-columns-md', placeholder: '3' },
                    { type: 'number', label: 'Columns (LG)', name: 'data-columns-lg', placeholder: '4' },
                    {
                        type: 'select',
                        label: 'Gap',
                        name: 'data-gap',
                        options: [
                            { id: '2', name: 'Small' },
                            { id: '4', name: 'Medium' },
                            { id: '6', name: 'Large' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerFlexSidebar(editor) {
    editor.BlockManager.add('flex-sidebar', {
        label: '<div class="text-center"><i class="ph-duotone ph-sidebar text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Sidebar</div></div>',
        category: 'Navigation',
        content: {
            type: 'flex-sidebar'
        }
    });

    editor.DomComponents.addType('flex-sidebar', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-sidebar',
                    class: 'flex'
                },
                components: [
                    '<aside class="w-64 bg-gray-100 p-4"><p>Sidebar content</p></aside>',
                    '<main class="flex-1 p-4"><p>Main content</p></main>'
                ],
                droppable: false,
                traits: [
                    {
                        type: 'select',
                        label: 'Position',
                        name: 'data-position',
                        options: [
                            { id: 'left', name: 'Left' },
                            { id: 'right', name: 'Right' }
                        ]
                    },
                    { type: 'text', label: 'Width', name: 'data-width', placeholder: '280px' },
                    { type: 'checkbox', label: 'Collapsible', name: 'data-collapsible' },
                    { type: 'checkbox', label: 'Sticky', name: 'data-sticky' }
                ]
            }
        }
    });
}

function registerFlexToolbar(editor) {
    editor.BlockManager.add('flex-toolbar', {
        label: '<div class="text-center"><i class="ph-duotone ph-navigation-arrow text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Toolbar</div></div>',
        category: 'Navigation',
        content: {
            type: 'flex-toolbar'
        }
    });

    editor.DomComponents.addType('flex-toolbar', {
        model: {
            defaults: {
                tagName: 'nav',
                attributes: {
                    'data-component': 'flex-toolbar',
                    class: 'bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between'
                },
                components: [
                    '<div class="flex items-center gap-4"><span class="font-bold">Logo</span></div>',
                    '<div class="flex items-center gap-2"><button class="px-4 py-2">Action</button></div>'
                ],
                droppable: false,
                traits: [
                    {
                        type: 'select',
                        label: 'Position',
                        name: 'data-position',
                        options: [
                            { id: 'top', name: 'Top' },
                            { id: 'bottom', name: 'Bottom' }
                        ]
                    },
                    { type: 'checkbox', label: 'Sticky', name: 'data-sticky' },
                    {
                        type: 'select',
                        label: 'Theme',
                        name: 'data-theme',
                        options: [
                            { id: 'light', name: 'Light' },
                            { id: 'dark', name: 'Dark' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerFlexSplitPane(editor) {
    editor.BlockManager.add('flex-split-pane', {
        label: '<div class="text-center"><i class="ph-duotone ph-columns text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Split Pane</div></div>',
        category: 'Navigation',
        content: {
            type: 'flex-split-pane'
        }
    });

    editor.DomComponents.addType('flex-split-pane', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-split-pane',
                    class: 'flex h-96'
                },
                components: [
                    '<div class="flex-1 border-r p-4">Left Pane</div>',
                    '<div class="flex-1 p-4">Right Pane</div>'
                ],
                droppable: false,
                traits: [
                    {
                        type: 'select',
                        label: 'Direction',
                        name: 'data-direction',
                        options: [
                            { id: 'horizontal', name: 'Horizontal' },
                            { id: 'vertical', name: 'Vertical' }
                        ]
                    },
                    { type: 'checkbox', label: 'Resizable', name: 'data-resizable' },
                    { type: 'text', label: 'Min Size', name: 'data-min-size', placeholder: '200px' }
                ]
            }
        }
    });
}

// ==================== DATA COMPONENTS ====================

function registerFlexModal(editor) {
    editor.BlockManager.add('flex-modal', {
        label: '<div class="text-center"><i class="ph-duotone ph-window text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Modal</div></div>',
        category: 'Data',
        content: {
            type: 'flex-modal'
        }
    });

    editor.DomComponents.addType('flex-modal', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'flex-modal',
                    'data-modal-id': 'modal-1',
                    class: 'hidden'
                },
                components: '<p>Modal content (trigger needed)</p>',
                traits: [
                    { type: 'text', label: 'Modal ID', name: 'data-modal-id' },
                    { type: 'text', label: 'Title', name: 'data-title' },
                    {
                        type: 'select',
                        label: 'Size',
                        name: 'data-size',
                        options: [
                            { id: 'sm', name: 'Small' },
                            { id: 'md', name: 'Medium' },
                            { id: 'lg', name: 'Large' },
                            { id: 'xl', name: 'Extra Large' },
                            { id: 'full', name: 'Full Screen' }
                        ]
                    }
                ]
            }
        }
    });
}

function registerDataTable(editor) {
    editor.BlockManager.add('data-table', {
        label: '<div class="text-center"><i class="ph-duotone ph-table text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Data Table</div></div>',
        category: 'Data',
        content: {
            type: 'data-table'
        }
    });

    editor.DomComponents.addType('data-table', {
        model: {
            defaults: {
                tagName: 'div',
                attributes: {
                    'data-component': 'data-table',
                    class: 'overflow-x-auto'
                },
                components: `
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column 1</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column 2</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <tr><td class="px-6 py-4">Data 1</td><td class="px-6 py-4">Data 2</td></tr>
                        </tbody>
                    </table>
                `,
                traits: [
                    { type: 'text', label: 'API Endpoint', name: 'data-api-endpoint' },
                    { type: 'checkbox', label: 'Sortable', name: 'data-sortable' },
                    { type: 'checkbox', label: 'Filterable', name: 'data-filterable' },
                    { type: 'checkbox', label: 'Paginated', name: 'data-paginated' }
                ]
            }
        }
    });
}

function registerDynamicForm(editor) {
    editor.BlockManager.add('dynamic-form', {
        label: '<div class="text-center"><i class="ph-duotone ph-list-checks text-lg text-blue-500 mb-1"></i><div style="font-size: 0.65rem; line-height: 1.2">Dynamic Form</div></div>',
        category: 'Data',
        content: {
            type: 'dynamic-form'
        }
    });

    editor.DomComponents.addType('dynamic-form', {
        model: {
            defaults: {
                tagName: 'form',
                attributes: {
                    'data-component': 'dynamic-form',
                    class: 'space-y-4'
                },
                components: '<p class="text-gray-500">Form will be generated from metadata</p>',
                traits: [
                    { type: 'text', label: 'Metadata Source', name: 'data-metadata-source' },
                    { type: 'text', label: 'Submit Endpoint', name: 'data-submit-endpoint' },
                    { type: 'checkbox', label: 'RBAC Enabled', name: 'data-rbac-enabled' }
                ]
            }
        }
    });
}
