/**
 * Widget Library Palette Component
 *
 * Visual widget palette with 26 widget types across 6 categories.
 * Provides drag-and-drop functionality to add widgets to dashboard canvas.
 *
 * Features:
 * - 26 widget types organized by category
 * - Visual thumbnails with hover previews
 * - Drag from palette to canvas
 * - Widget search functionality
 * - Favorites and recent widgets
 * - Category filtering
 *
 * Usage:
 * const palette = new WidgetLibraryPalette(container, {
 *   onWidgetSelect: (widget) => console.log('Selected:', widget),
 *   onWidgetDragStart: (widget) => console.log('Dragging:', widget)
 * });
 */

export class WidgetLibraryPalette {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = options;

        // Callbacks
        this.onWidgetSelect = options.onWidgetSelect || (() => {});
        this.onWidgetDragStart = options.onWidgetDragStart || (() => {});

        // State
        this.selectedCategory = 'all';
        this.searchQuery = '';
        this.favorites = this.loadFavorites();
        this.recentWidgets = this.loadRecentWidgets();
        this.expandedPreview = null;

        // Define all 26 widget types
        this.widgetTypes = this.defineWidgetTypes();

        // Initialize
        this.init();
    }

    defineWidgetTypes() {
        return {
            // 📊 Charts (9 types)
            charts: [
                {
                    id: 'chart-bar',
                    name: 'Bar Chart',
                    icon: 'ph-chart-bar',
                    description: 'Compare values across categories',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSI0MCIgd2lkdGg9IjE1IiBoZWlnaHQ9IjMwIiBmaWxsPSIjM0I4MkY2Ii8+PHJlY3QgeD0iMzUiIHk9IjIwIiB3aWR0aD0iMTUiIGhlaWdodD0iNTAiIGZpbGw9IiMzQjgyRjYiLz48cmVjdCB4PSI2MCIgeT0iMzAiIHdpZHRoPSIxNSIgaGVpZ2h0PSI0MCIgZmlsbD0iIzNCODJGNiIvPjxyZWN0IHg9Ijg1IiB5PSIxMCIgd2lkdGg9IjE1IiBoZWlnaHQ9IjYwIiBmaWxsPSIjM0I4MkY2Ii8+PC9zdmc+'
                },
                {
                    id: 'chart-line',
                    name: 'Line Chart',
                    icon: 'ph-chart-line',
                    description: 'Show trends over time',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0xMCA2MCBMMzAgNDAgTDUwIDQ1IEw3MCAyNSBMOTAgMzUiIHN0cm9rZT0iIzNCODJGNiIgc3Ryb2tlLXdpZHRoPSIzIiBmaWxsPSJub25lIi8+PC9zdmc+'
                },
                {
                    id: 'chart-pie',
                    name: 'Pie Chart',
                    icon: 'ph-chart-pie',
                    description: 'Show proportions of a whole',
                    defaultWidth: 4,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjUwIiBjeT0iNDAiIHI9IjMwIiBmaWxsPSIjRTVFN0VCIi8+PHBhdGggZD0iTTUwIDQwIEw1MCAxMCBBMzAgMzAgMCAwIDEgODAgNDBaIiBmaWxsPSIjM0I4MkY2Ii8+PHBhdGggZD0iTTUwIDQwIEw4MCA0MCBBMzAgMzAgMCAwIDEgNTAgNzBaIiBmaWxsPSIjMTBCOTgxIi8+PC9zdmc+'
                },
                {
                    id: 'chart-donut',
                    name: 'Donut Chart',
                    icon: 'ph-chart-donut',
                    description: 'Pie chart with center hole',
                    defaultWidth: 4,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjUwIiBjeT0iNDAiIHI9IjMwIiBmaWxsPSJub25lIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMTUiLz48cGF0aCBkPSJNNTAgMTAgQTMwIDMwIDAgMCAxIDgwIDQwIiBzdHJva2U9IiMzQjgyRjYiIHN0cm9rZS13aWR0aD0iMTUiIGZpbGw9Im5vbmUiLz48L3N2Zz4='
                },
                {
                    id: 'chart-area',
                    name: 'Area Chart',
                    icon: 'ph-chart-line-up',
                    description: 'Filled line chart for trends',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0xMCA2MCBMMzAgNDAgTDUwIDQ1IEw3MCAyNSBMOTAgMzUgTDkwIDcwIEwxMCA3MFoiIGZpbGw9IiMzQjgyRjYiIGZpbGwtb3BhY2l0eT0iMC4zIi8+PHBhdGggZD0iTTEwIDYwIEwzMCA0MCBMNTAGNDUGBMN0wgMjUgTDkwIDM1IiBzdHJva2U9IiMzQjgyRjYiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIvPjwvc3ZnPg=='
                },
                {
                    id: 'chart-scatter',
                    name: 'Scatter Plot',
                    icon: 'ph-scatter-chart',
                    description: 'Plot correlation between variables',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjIwIiBjeT0iNTAiIHI9IjQiIGZpbGw9IiMzQjgyRjYiLz48Y2lyY2xlIGN4PSI0MCIgY3k9IjMwIiByPSI0IiBmaWxsPSIjM0I4MkY2Ii8+PGNpcmNsZSBjeD0iNjAiIGN5PSI0MCIgcj0iNCIgZmlsbD0iIzNCODJGNiIvPjxjaXJjbGUgY3g9IjgwIiBjeT0iMjAiIHI9IjQiIGZpbGw9IiMzQjgyRjYiLz48L3N2Zz4='
                },
                {
                    id: 'chart-radar',
                    name: 'Radar Chart',
                    icon: 'ph-polygon',
                    description: 'Multi-variable comparison',
                    defaultWidth: 5,
                    defaultHeight: 5,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwb2x5Z29uIHBvaW50cz0iNTAsMTUgNzUsMzAgNjUsNjAgMzUsNjAgMjUsMzAiIHN0cm9rZT0iI0U1RTdFQiIgc3Ryb2tlLXdpZHRoPSIxIiBmaWxsPSJub25lIi8+PHBvbHlnb24gcG9pbnRzPSI1MCwyMCA3MCwzMiA2Miw1NSAzOCw1NSAzMCwzMiIgZmlsbD0iIzNCODJGNiIgZmlsbC1vcGFjaXR5PSIwLjMiIHN0cm9rZT0iIzNCODJGNiIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9zdmc+'
                },
                {
                    id: 'chart-polar',
                    name: 'Polar Chart',
                    icon: 'ph-circle-half',
                    description: 'Circular data visualization',
                    defaultWidth: 5,
                    defaultHeight: 5,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjUwIiBjeT0iNDAiIHI9IjMwIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMSIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik01MCA0MCBMNTAgMTAgQTMwIDMwIDAgMCAxIDY1IDE0IFoiIGZpbGw9IiMzQjgyRjYiLz48cGF0aCBkPSJNNTAgNDAgTDY1IDE0IEEzMCAzMCAwIDAgMSA3NSAyNSBaIiBmaWxsPSIjMTBCOTgxIi8+PC9zdmc+'
                },
                {
                    id: 'chart-bubble',
                    name: 'Bubble Chart',
                    icon: 'ph-circles-three',
                    description: 'Three-dimensional data plot',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjI1IiBjeT0iNTAiIHI9IjEwIiBmaWxsPSIjM0I4MkY2IiBmaWxsLW9wYWNpdHk9IjAuNSIvPjxjaXJjbGUgY3g9IjU1IiBjeT0iMzAiIHI9IjE1IiBmaWxsPSIjMTBCOTgxIiBmaWxsLW9wYWNpdHk9IjAuNSIvPjxjaXJjbGUgY3g9IjgwIiBjeT0iNDUiIHI9IjgiIGZpbGw9IiNGNTlFMEIiIGZpbGwtb3BhY2l0eT0iMC41Ii8+PC9zdmc+'
                }
            ],

            // 📈 Metrics (5 types)
            metrics: [
                {
                    id: 'metric-kpi',
                    name: 'KPI Card',
                    icon: 'ph-chart-line-up',
                    description: 'Key performance indicator with trend',
                    defaultWidth: 3,
                    defaultHeight: 2,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjEwIiB5PSIzMCIgZm9udC1zaXplPSIyNCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IiMxRjI5MzciPiQ4Ny41SzwvdGV4dD48dGV4dCB4PSIxMCIgeT0iNTAiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiMxMEI5ODEiPuKGkSAxMi41JTwvdGV4dD48L3N2Zz4='
                },
                {
                    id: 'metric-gauge',
                    name: 'Gauge',
                    icon: 'ph-gauge',
                    description: 'Semi-circular progress indicator',
                    defaultWidth: 4,
                    defaultHeight: 3,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0yMCA2MCBBMzAgMzAgMCAwIDEgODAgNjAiIHN0cm9rZT0iI0U1RTdFQiIgc3Ryb2tlLXdpZHRoPSI4IiBmaWxsPSJub25lIi8+PHBhdGggZD0iTTIwIDYwIEEzMCAzMCAwIDAgMSA2NSAyOCIgc3Ryb2tlPSIjM0I4MkY2IiBzdHJva2Utd2lkdGg9IjgiIGZpbGw9Im5vbmUiLz48L3N2Zz4='
                },
                {
                    id: 'metric-progress',
                    name: 'Progress Bar',
                    icon: 'ph-arrows-horizontal',
                    description: 'Linear progress indicator',
                    defaultWidth: 4,
                    defaultHeight: 2,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIzNSIgd2lkdGg9IjgwIiBoZWlnaHQ9IjEwIiByeD0iNSIgZmlsbD0iI0U1RTdFQiIvPjxyZWN0IHg9IjEwIiB5PSIzNSIgd2lkdGg9IjU2IiBoZWlnaHQ9IjEwIiByeD0iNSIgZmlsbD0iIzNCODJGNiIvPjwvc3ZnPg=='
                },
                {
                    id: 'metric-stat',
                    name: 'Stat Card',
                    icon: 'ph-number-square-one',
                    description: 'Simple statistic display',
                    defaultWidth: 3,
                    defaultHeight: 2,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjEwIiB5PSIyNSIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzY0NzQ4QiI+VG90YWwgU2FsZXM8L3RleHQ+PHRleHQgeD0iMTAiIHk9IjUwIiBmb250LXNpemU9IjI4IiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzFGMjkzNyI+MTIzNDwvdGV4dD48L3N2Zz4='
                },
                {
                    id: 'metric-counter',
                    name: 'Number Counter',
                    icon: 'ph-hash',
                    description: 'Animated number counter',
                    defaultWidth: 3,
                    defaultHeight: 2,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIzNiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IiMzQjgyRjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiPjk4LjclPC90ZXh0Pjwvc3ZnPg=='
                }
            ],

            // 📋 Tables (3 types)
            tables: [
                {
                    id: 'table-grid',
                    name: 'Data Grid',
                    icon: 'ph-table',
                    description: 'Interactive data table with sorting',
                    defaultWidth: 8,
                    defaultHeight: 5,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMSIgZmlsbD0id2hpdGUiLz48bGluZSB4MT0iMTAiIHkxPSIyNSIgeDI9IjkwIiB5Mj0iMjUiIHN0cm9rZT0iI0U1RTdFQiIgc3Ryb2tlLXdpZHRoPSIxIi8+PGxpbmUgeDE9IjM1IiB5MT0iMTAiIHgyPSIzNSIgeTI9IjcwIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMSIvPjxsaW5lIHgxPSI2NSIgeTE9IjEwIiB4Mj0iNjUiIHkyPSI3MCIgc3Ryb2tlPSIjRTVFN0VCIiBzdHJva2Utd2lkdGg9IjEiLz48L3N2Zz4='
                },
                {
                    id: 'table-summary',
                    name: 'Summary Table',
                    icon: 'ph-list-dashes',
                    description: 'Aggregated data table',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxNSIgd2lkdGg9IjgwIiBoZWlnaHQ9IjEyIiBmaWxsPSIjRjNGNEY2Ii8+PHJlY3QgeD0iMTAiIHk9IjMzIiB3aWR0aD0iODAiIGhlaWdodD0iMTIiIGZpbGw9IndoaXRlIi8+PHJlY3QgeD0iMTAiIHk9IjUxIiB3aWR0aD0iODAiIGhlaWdodD0iMTIiIGZpbGw9IiNGM0Y0RjYiLz48L3N2Zz4='
                },
                {
                    id: 'table-pivot',
                    name: 'Pivot Table',
                    icon: 'ph-grid-four',
                    description: 'Multi-dimensional data analysis',
                    defaultWidth: 8,
                    defaultHeight: 5,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjI1IiBoZWlnaHQ9IjE1IiBmaWxsPSIjM0I4MkY2IiBmaWxsLW9wYWNpdHk9IjAuMiIvPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMSIgZmlsbD0ibm9uZSIvPjxsaW5lIHgxPSIzNSIgeTE9IjEwIiB4Mj0iMzUiIHkyPSI3MCIgc3Ryb2tlPSIjRTVFN0VCIi8+PGxpbmUgeDE9IjEwIiB5MT0iMjUiIHgyPSI5MCIgeTI9IjI1IiBzdHJva2U9IiNFNUU3RUIiLz48L3N2Zz4='
                }
            ],

            // 📝 Text (3 types)
            text: [
                {
                    id: 'text-header',
                    name: 'Header',
                    icon: 'ph-text-h',
                    description: 'Heading text (H1-H6)',
                    defaultWidth: 12,
                    defaultHeight: 1,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjEwIiB5PSI0NSIgZm9udC1zaXplPSIyNCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IiMxRjI5MzciPkhlYWRpbmc8L3RleHQ+PC9zdmc+'
                },
                {
                    id: 'text-paragraph',
                    name: 'Paragraph',
                    icon: 'ph-text-aa',
                    description: 'Plain text paragraph',
                    defaultWidth: 6,
                    defaultHeight: 2,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjEwIiB5PSIyNSIgZm9udC1zaXplPSIxMCIgZmlsbD0iIzY0NzQ4QiI+TG9yZW0gaXBzdW0gZG9sb3Igc2l0IGFtZXQ8L3RleHQ+PHRleHQgeD0iMTAiIHk9IjQwIiBmb250LXNpemU9IjEwIiBmaWxsPSIjNjQ3NDhCIj5jb25zZWN0ZXR1ciBhZGlwaXNjaW5nPC90ZXh0Pjx0ZXh0IHg9IjEwIiB5PSI1NSIgZm9udC1zaXplPSIxMCIgZmlsbD0iIzY0NzQ4QiI+ZWxpdCBzZWQgZG8gZWl1c21vZDwvdGV4dD48L3N2Zz4='
                },
                {
                    id: 'text-rich',
                    name: 'Rich Text',
                    icon: 'ph-text-align-left',
                    description: 'Formatted text with editor',
                    defaultWidth: 8,
                    defaultHeight: 3,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjE1IiBmaWxsPSIjRjNGNEY2Ii8+PHRleHQgeD0iMTUiIHk9IjM1IiBmb250LXNpemU9IjEyIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzFGMjkzNyI+Qm9sZCBUZXh0PC90ZXh0Pjx0ZXh0IHg9IjE1IiB5PSI1MCIgZm9udC1zaXplPSIxMCIgZmlsbD0iIzY0NzQ4QiI+UmVndWxhciB0ZXh0IGNvbnRlbnQ8L3RleHQ+PC9zdmc+'
                }
            ],

            // 🖼️ Media (3 types)
            media: [
                {
                    id: 'media-image',
                    name: 'Image',
                    icon: 'ph-image',
                    description: 'Image display',
                    defaultWidth: 4,
                    defaultHeight: 3,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjRjNGNEY2Ii8+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iOCIgZmlsbD0iI0U1RTdFQiIvPjxwYXRoIGQ9Ik0xMCA1MCBMNDAGMJBMNTE1MCAzNSBMOTAgNzAgTDEwIDcwWiIgZmlsbD0iI0U1RTdFQiIvPjwvc3ZnPg=='
                },
                {
                    id: 'media-video',
                    name: 'Video',
                    icon: 'ph-video-camera',
                    description: 'Video player embed',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjMUYyOTM3Ii8+PHBvbHlnb24gcG9pbnRzPSI0MCwzMCA2MCw0MCA0MCw1MCIgZmlsbD0id2hpdGUiLz48L3N2Zz4='
                },
                {
                    id: 'media-iframe',
                    name: 'Iframe Embed',
                    icon: 'ph-browser',
                    description: 'External content embed',
                    defaultWidth: 6,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBzdHJva2U9IiNFNUU3RUIiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0id2hpdGUiLz48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIzIiBmaWxsPSIjRUY0NDQ0Ii8+PGNpcmNsZSBjeD0iMzAiIGN5PSIyMCIgcj0iMyIgZmlsbD0iI0Y1OUUwQiIvPjxjaXJjbGUgY3g9IjQwIiBjeT0iMjAiIHI9IjMiIGZpbGw9IiMxMEI5ODEiLz48L3N2Zz4='
                }
            ],

            // 🔗 Actions (3 types)
            actions: [
                {
                    id: 'action-button',
                    name: 'Button',
                    icon: 'ph-hand-pointing',
                    description: 'Interactive button',
                    defaultWidth: 2,
                    defaultHeight: 1,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjIwIiB5PSIyOCIgd2lkdGg9IjYwIiBoZWlnaHQ9IjI0IiByeD0iNCIgZmlsbD0iIzNCODJGNiIvPjx0ZXh0IHg9IjUwIiB5PSI0NSIgZm9udC1zaXplPSIxMiIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkNsaWNrIE1lPC90ZXh0Pjwvc3ZnPg=='
                },
                {
                    id: 'action-link',
                    name: 'Link',
                    icon: 'ph-link',
                    description: 'Hyperlink navigation',
                    defaultWidth: 2,
                    defaultHeight: 1,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjMwIiB5PSI0NSIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzNCODJGNiIgdGV4dC1kZWNvcmF0aW9uPSJ1bmRlcmxpbmUiPkxpbmsgVGV4dDwvdGV4dD48L3N2Zz4='
                },
                {
                    id: 'action-filter',
                    name: 'Filter Panel',
                    icon: 'ph-funnel',
                    description: 'Interactive dashboard filters',
                    defaultWidth: 3,
                    defaultHeight: 4,
                    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiB2aWV3Qm94PSIwIDAgMTAwIDgwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjE1IiB5PSIxNSIgd2lkdGg9IjcwIiBoZWlnaHQ9IjEyIiByeD0iMiIgZmlsbD0iI0YzRjRGNiIvPjxyZWN0IHg9IjE1IiB5PSIzNCIgd2lkdGg9IjcwIiBoZWlnaHQ9IjEyIiByeD0iMiIgZmlsbD0iI0YzRjRGNiIvPjxyZWN0IHg9IjE1IiB5PSI1MyIgd2lkdGg9IjcwIiBoZWlnaHQ9IjEyIiByeD0iMiIgZmlsbD0iI0YzRjRGNiIvPjwvc3ZnPg=='
                }
            ]
        };
    }

    async init() {
        await this.render();
        this.attachEventListeners();
    }

    async render() {
        this.container.innerHTML = `
            <div class="widget-library-palette bg-white border-r border-gray-200 h-full flex flex-col">
                <!-- Header -->
                <div class="p-4 border-b border-gray-200">
                    <h3 class="text-sm font-semibold text-gray-900 mb-3">Widget Library</h3>

                    <!-- Search -->
                    <div class="relative">
                        <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" id="widget-search"
                            class="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Search widgets...">
                    </div>
                </div>

                <!-- Quick Access Tabs -->
                <div class="flex border-b border-gray-200 bg-gray-50">
                    <button class="quick-tab flex-1 px-3 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent" data-tab="all">
                        <i class="ph ph-squares-four mr-1"></i>
                        All
                    </button>
                    <button class="quick-tab flex-1 px-3 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent" data-tab="favorites">
                        <i class="ph ph-star mr-1"></i>
                        Favorites
                    </button>
                    <button class="quick-tab flex-1 px-3 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent" data-tab="recent">
                        <i class="ph ph-clock mr-1"></i>
                        Recent
                    </button>
                </div>

                <!-- Widget Categories -->
                <div class="flex-1 overflow-y-auto p-4 space-y-4">
                    ${this.renderWidgetCategories()}
                </div>
            </div>
        `;

        // Set default active tab
        this.setActiveTab('all');
    }

    renderWidgetCategories() {
        const categories = [
            { key: 'charts', icon: 'ph-chart-bar', label: 'Charts', count: 9 },
            { key: 'metrics', icon: 'ph-chart-line-up', label: 'Metrics', count: 5 },
            { key: 'tables', icon: 'ph-table', label: 'Tables', count: 3 },
            { key: 'text', icon: 'ph-text-aa', label: 'Text', count: 3 },
            { key: 'media', icon: 'ph-image', label: 'Media', count: 3 },
            { key: 'actions', icon: 'ph-hand-pointing', label: 'Actions', count: 3 }
        ];

        return categories.map(cat => `
            <div class="widget-category">
                <div class="flex items-center justify-between mb-2 cursor-pointer category-header" data-category="${cat.key}">
                    <div class="flex items-center">
                        <i class="${cat.icon} text-gray-500 mr-2"></i>
                        <span class="text-sm font-medium text-gray-700">${cat.label}</span>
                        <span class="ml-2 text-xs text-gray-500">(${cat.count})</span>
                    </div>
                    <i class="ph ph-caret-down text-gray-400 category-toggle"></i>
                </div>
                <div class="widget-grid grid grid-cols-2 gap-2" data-category="${cat.key}">
                    ${this.renderWidgets(cat.key)}
                </div>
            </div>
        `).join('');
    }

    renderWidgets(categoryKey) {
        const widgets = this.widgetTypes[categoryKey] || [];
        return widgets.map(widget => {
            const isFavorite = this.favorites.includes(widget.id);
            return `
                <div class="widget-card group relative bg-white border border-gray-200 rounded-lg p-2 cursor-move hover:border-blue-500 hover:shadow-md transition-all"
                    draggable="true"
                    data-widget-id="${widget.id}"
                    data-widget-name="${widget.name}"
                    data-widget-type="${categoryKey}">

                    <!-- Favorite Button -->
                    <button class="favorite-btn absolute top-1 right-1 w-5 h-5 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10 ${isFavorite ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'}"
                        data-widget-id="${widget.id}">
                        <i class="ph ${isFavorite ? 'ph-star-fill' : 'ph-star'} text-xs"></i>
                    </button>

                    <!-- Thumbnail -->
                    <div class="widget-thumbnail aspect-video bg-gray-50 rounded mb-2 flex items-center justify-center overflow-hidden">
                        <img src="${widget.thumbnail}" alt="${widget.name}" class="w-full h-full object-contain">
                    </div>

                    <!-- Info -->
                    <div class="text-center">
                        <div class="flex items-center justify-center mb-1">
                            <i class="${widget.icon} text-gray-600 text-sm mr-1"></i>
                            <span class="text-xs font-medium text-gray-900">${widget.name}</span>
                        </div>
                        <p class="text-xs text-gray-500 line-clamp-1">${widget.description}</p>
                    </div>

                    <!-- Hover Preview -->
                    <div class="widget-preview hidden absolute left-full top-0 ml-2 z-20 bg-white border border-gray-300 rounded-lg shadow-xl p-3 w-64">
                        <h4 class="font-semibold text-sm mb-2">${widget.name}</h4>
                        <p class="text-xs text-gray-600 mb-2">${widget.description}</p>
                        <div class="text-xs text-gray-500">
                            <div>Default size: ${widget.defaultWidth}x${widget.defaultHeight}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    attachEventListeners() {
        const container = this.container;

        // Search
        const searchInput = container.querySelector('#widget-search');
        searchInput?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.filterWidgets();
        });

        // Quick tabs
        container.querySelectorAll('.quick-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.setActiveTab(tabName);
            });
        });

        // Category toggle
        container.querySelectorAll('.category-header').forEach(header => {
            header.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                this.toggleCategory(category);
            });
        });

        // Widget drag start
        container.querySelectorAll('.widget-card').forEach(card => {
            card.addEventListener('dragstart', (e) => {
                const widgetId = e.currentTarget.dataset.widgetId;
                const widgetName = e.currentTarget.dataset.widgetName;
                const widgetType = e.currentTarget.dataset.widgetType;

                const widget = this.widgetTypes[widgetType].find(w => w.id === widgetId);

                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('application/json', JSON.stringify(widget));

                // Add to recent widgets
                this.addToRecent(widgetId);

                // Callback
                this.onWidgetDragStart(widget);
            });

            // Widget click
            card.addEventListener('click', (e) => {
                if (e.target.closest('.favorite-btn')) return;

                const widgetId = e.currentTarget.dataset.widgetId;
                const widgetType = e.currentTarget.dataset.widgetType;
                const widget = this.widgetTypes[widgetType].find(w => w.id === widgetId);

                this.onWidgetSelect(widget);
            });

            // Show preview on hover
            card.addEventListener('mouseenter', (e) => {
                const preview = e.currentTarget.querySelector('.widget-preview');
                if (preview) {
                    preview.classList.remove('hidden');
                }
            });

            card.addEventListener('mouseleave', (e) => {
                const preview = e.currentTarget.querySelector('.widget-preview');
                if (preview) {
                    preview.classList.add('hidden');
                }
            });
        });

        // Favorite toggle
        container.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const widgetId = e.currentTarget.dataset.widgetId;
                this.toggleFavorite(widgetId);
            });
        });
    }

    setActiveTab(tabName) {
        this.selectedCategory = tabName;

        // Update UI
        this.container.querySelectorAll('.quick-tab').forEach(tab => {
            const isActive = tab.dataset.tab === tabName;
            tab.classList.toggle('text-blue-600', isActive);
            tab.classList.toggle('border-blue-600', isActive);
            tab.classList.toggle('text-gray-600', !isActive);
        });

        this.filterWidgets();
    }

    toggleCategory(category) {
        const gridElement = this.container.querySelector(`.widget-grid[data-category="${category}"]`);
        const toggleIcon = this.container.querySelector(`.category-header[data-category="${category}"] .category-toggle`);

        if (gridElement) {
            const isHidden = gridElement.classList.contains('hidden');
            gridElement.classList.toggle('hidden');
            toggleIcon?.classList.toggle('ph-caret-down', isHidden);
            toggleIcon?.classList.toggle('ph-caret-right', !isHidden);
        }
    }

    filterWidgets() {
        const allCards = this.container.querySelectorAll('.widget-card');

        allCards.forEach(card => {
            const widgetId = card.dataset.widgetId;
            const widgetName = card.dataset.widgetName.toLowerCase();
            const widgetType = card.dataset.widgetType;

            let shouldShow = true;

            // Filter by tab
            if (this.selectedCategory === 'favorites') {
                shouldShow = this.favorites.includes(widgetId);
            } else if (this.selectedCategory === 'recent') {
                shouldShow = this.recentWidgets.includes(widgetId);
            }

            // Filter by search
            if (shouldShow && this.searchQuery) {
                const widget = this.widgetTypes[widgetType].find(w => w.id === widgetId);
                shouldShow = widgetName.includes(this.searchQuery) ||
                            widget.description.toLowerCase().includes(this.searchQuery);
            }

            card.classList.toggle('hidden', !shouldShow);
        });

        // Show/hide categories based on visible widgets
        this.container.querySelectorAll('.widget-category').forEach(category => {
            const visibleCards = category.querySelectorAll('.widget-card:not(.hidden)');
            category.classList.toggle('hidden', visibleCards.length === 0);
        });
    }

    toggleFavorite(widgetId) {
        const index = this.favorites.indexOf(widgetId);
        if (index > -1) {
            this.favorites.splice(index, 1);
        } else {
            this.favorites.push(widgetId);
        }

        this.saveFavorites();
        this.render();
        this.attachEventListeners();
    }

    addToRecent(widgetId) {
        // Remove if already exists
        const index = this.recentWidgets.indexOf(widgetId);
        if (index > -1) {
            this.recentWidgets.splice(index, 1);
        }

        // Add to beginning
        this.recentWidgets.unshift(widgetId);

        // Keep only last 10
        this.recentWidgets = this.recentWidgets.slice(0, 10);

        this.saveRecentWidgets();
    }

    loadFavorites() {
        try {
            const stored = localStorage.getItem('dashboardWidgetFavorites');
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    }

    saveFavorites() {
        try {
            localStorage.setItem('dashboardWidgetFavorites', JSON.stringify(this.favorites));
        } catch (e) {
            console.error('Failed to save favorites', e);
        }
    }

    loadRecentWidgets() {
        try {
            const stored = localStorage.getItem('dashboardRecentWidgets');
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    }

    saveRecentWidgets() {
        try {
            localStorage.setItem('dashboardRecentWidgets', JSON.stringify(this.recentWidgets));
        } catch (e) {
            console.error('Failed to save recent widgets', e);
        }
    }

    // Public API
    getAllWidgetTypes() {
        return this.widgetTypes;
    }

    getWidgetById(widgetId) {
        for (const category in this.widgetTypes) {
            const widget = this.widgetTypes[category].find(w => w.id === widgetId);
            if (widget) return widget;
        }
        return null;
    }
}
