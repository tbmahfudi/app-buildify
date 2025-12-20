/**
 * FlexDataGrid - Advanced Data Grid Component
 *
 * Excel-like data grid with advanced features:
 * - Inline editing
 * - Column resizing
 * - Column reordering
 * - Frozen columns
 * - Virtual scrolling (for large datasets)
 * - Excel-like keyboard navigation
 * - Copy/paste support
 * - Cell formatting
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexDataGrid extends BaseComponent {
    static DEFAULTS = {
        columns: [],
        data: [],
        keyField: 'id',

        // Editing
        editable: false,
        editMode: 'cell',           // cell | row

        // Columns
        resizable: true,
        reorderable: true,
        frozenColumns: 0,           // Number of columns to freeze

        // Virtualization
        virtual: false,             // Enable virtual scrolling
        rowHeight: 40,
        visibleRows: 20,

        // Navigation
        keyboardNavigation: true,

        // Copy/Paste
        copyPaste: true,

        // Selection
        cellSelection: true,
        rangeSelection: true,

        // Styling
        gridLines: true,
        alternateRows: true,
        classes: [],

        // Callbacks
        onCellEdit: null,
        onCellChange: null,
        onRowEdit: null,
        onColumnResize: null,
        onColumnReorder: null
    };

    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            data: this.options.data,
            editingCell: null,
            selectedCell: null,
            selectedRange: null,
            scrollTop: 0,
            visibleStartIndex: 0,
            visibleEndIndex: 0
        };

        this.gridElement = null;
        this.init();
    }

    init() {
        this.calculateVisibleRange();
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    calculateVisibleRange() {
        if (!this.options.virtual) {
            this.state.visibleStartIndex = 0;
            this.state.visibleEndIndex = this.state.data.length;
            return;
        }

        const scrollTop = this.state.scrollTop;
        const rowHeight = this.options.rowHeight;
        const visibleRows = this.options.visibleRows;

        this.state.visibleStartIndex = Math.floor(scrollTop / rowHeight);
        this.state.visibleEndIndex = Math.min(
            this.state.visibleStartIndex + visibleRows + 5, // Buffer
            this.state.data.length
        );
    }

    render() {
        this.container.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = `flex-datagrid overflow-auto border border-gray-300 ${this.options.classes.join(' ')}`;
        wrapper.style.maxHeight = this.options.virtual
            ? `${this.options.rowHeight * this.options.visibleRows}px`
            : 'auto';

        this.gridElement = document.createElement('table');
        this.gridElement.className = `w-full border-collapse ${this.options.gridLines ? 'border-separate border-spacing-0' : ''}`;

        // Header
        this.gridElement.appendChild(this.renderHeader());

        // Body
        this.gridElement.appendChild(this.renderBody());

        wrapper.appendChild(this.gridElement);
        this.container.appendChild(wrapper);
    }

    renderHeader() {
        const thead = document.createElement('thead');
        thead.className = 'bg-gray-100 sticky top-0 z-10';

        const tr = document.createElement('tr');

        this.options.columns.forEach((column, index) => {
            const th = document.createElement('th');
            th.className = `px-3 py-2 text-left text-sm font-semibold text-gray-700 border-b border-r border-gray-300 ${
                index < this.options.frozenColumns ? 'sticky left-0 z-20 bg-gray-100' : ''
            }`;

            if (column.width) {
                th.style.width = column.width;
                th.style.minWidth = column.width;
            }

            const content = document.createElement('div');
            content.className = 'flex items-center justify-between';

            const label = document.createElement('span');
            label.textContent = column.label;
            content.appendChild(label);

            // Resize handle
            if (this.options.resizable) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500';
                resizeHandle.setAttribute('data-resize-column', index);
                th.style.position = 'relative';
                th.appendChild(resizeHandle);
            }

            th.appendChild(content);
            th.setAttribute('data-column-index', index);

            tr.appendChild(th);
        });

        thead.appendChild(tr);
        return thead;
    }

    renderBody() {
        const tbody = document.createElement('tbody');

        if (this.options.virtual) {
            // Virtual scrolling: add spacer rows
            if (this.state.visibleStartIndex > 0) {
                const spacerTop = document.createElement('tr');
                const spacerTd = document.createElement('td');
                spacerTd.colSpan = this.options.columns.length;
                spacerTd.style.height = `${this.state.visibleStartIndex * this.options.rowHeight}px`;
                spacerTop.appendChild(spacerTd);
                tbody.appendChild(spacerTop);
            }
        }

        const startIndex = this.options.virtual ? this.state.visibleStartIndex : 0;
        const endIndex = this.options.virtual ? this.state.visibleEndIndex : this.state.data.length;

        for (let i = startIndex; i < endIndex; i++) {
            const row = this.state.data[i];
            tbody.appendChild(this.renderRow(row, i));
        }

        if (this.options.virtual) {
            const remainingRows = this.state.data.length - this.state.visibleEndIndex;
            if (remainingRows > 0) {
                const spacerBottom = document.createElement('tr');
                const spacerTd = document.createElement('td');
                spacerTd.colSpan = this.options.columns.length;
                spacerTd.style.height = `${remainingRows * this.options.rowHeight}px`;
                spacerBottom.appendChild(spacerTd);
                tbody.appendChild(spacerBottom);
            }
        }

        return tbody;
    }

    renderRow(row, rowIndex) {
        const tr = document.createElement('tr');
        tr.className = this.options.alternateRows && rowIndex % 2 === 0
            ? 'bg-white hover:bg-gray-50'
            : 'bg-gray-50 hover:bg-gray-100';
        tr.style.height = `${this.options.rowHeight}px`;
        tr.setAttribute('data-row-index', rowIndex);

        this.options.columns.forEach((column, colIndex) => {
            const td = document.createElement('td');
            td.className = `px-3 py-2 text-sm text-gray-900 border-b border-r border-gray-200 ${
                colIndex < this.options.frozenColumns ? 'sticky left-0 z-10 bg-inherit' : ''
            }`;

            if (column.width) {
                td.style.width = column.width;
                td.style.minWidth = column.width;
            }

            const isEditing = this.state.editingCell?.row === rowIndex && this.state.editingCell?.col === colIndex;

            if (isEditing) {
                td.appendChild(this.renderEditCell(row, column, rowIndex, colIndex));
            } else {
                const value = this.getCellValue(row, column.key);
                if (column.render) {
                    td.innerHTML = column.render(value, row);
                } else {
                    td.textContent = value;
                }
            }

            td.setAttribute('data-row', rowIndex);
            td.setAttribute('data-col', colIndex);
            td.setAttribute('tabindex', '0');

            tr.appendChild(td);
        });

        return tr;
    }

    renderEditCell(row, column, rowIndex, colIndex) {
        const input = document.createElement('input');
        input.type = column.type || 'text';
        input.value = this.getCellValue(row, column.key);
        input.className = 'w-full px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500';
        input.setAttribute('data-edit-input', 'true');

        setTimeout(() => {
            input.focus();
            input.select();
        }, 0);

        return input;
    }

    getCellValue(row, key) {
        return key.split('.').reduce((obj, k) => obj?.[k], row) ?? '';
    }

    attachEventListeners() {
        // Cell click - select or edit
        this.gridElement.addEventListener('click', (e) => {
            const cell = e.target.closest('[data-row][data-col]');
            if (cell) {
                const row = parseInt(cell.getAttribute('data-row'));
                const col = parseInt(cell.getAttribute('data-col'));
                this.selectCell(row, col);
            }
        });

        // Double click - edit
        if (this.options.editable) {
            this.gridElement.addEventListener('dblclick', (e) => {
                const cell = e.target.closest('[data-row][data-col]');
                if (cell) {
                    const row = parseInt(cell.getAttribute('data-row'));
                    const col = parseInt(cell.getAttribute('data-col'));
                    this.editCell(row, col);
                }
            });
        }

        // Edit input blur - save
        this.gridElement.addEventListener('blur', (e) => {
            if (e.target.hasAttribute('data-edit-input')) {
                this.saveCell(e.target.value);
            }
        }, true);

        // Edit input enter - save and move
        this.gridElement.addEventListener('keydown', (e) => {
            if (e.target.hasAttribute('data-edit-input')) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.saveCell(e.target.value);
                    this.moveCellSelection(1, 0); // Move down
                } else if (e.key === 'Escape') {
                    this.cancelEdit();
                } else if (e.key === 'Tab') {
                    e.preventDefault();
                    this.saveCell(e.target.value);
                    this.moveCellSelection(0, e.shiftKey ? -1 : 1); // Move left/right
                }
            } else if (this.options.keyboardNavigation) {
                // Arrow key navigation
                const cell = e.target.closest('[data-row][data-col]');
                if (cell) {
                    if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        this.moveCellSelection(-1, 0);
                    } else if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        this.moveCellSelection(1, 0);
                    } else if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        this.moveCellSelection(0, -1);
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        this.moveCellSelection(0, 1);
                    } else if (e.key === 'Enter' && this.options.editable) {
                        e.preventDefault();
                        const row = parseInt(cell.getAttribute('data-row'));
                        const col = parseInt(cell.getAttribute('data-col'));
                        this.editCell(row, col);
                    }
                }
            }
        });

        // Column resize
        if (this.options.resizable) {
            let resizing = null;

            this.gridElement.addEventListener('mousedown', (e) => {
                const handle = e.target.closest('[data-resize-column]');
                if (handle) {
                    resizing = {
                        columnIndex: parseInt(handle.getAttribute('data-resize-column')),
                        startX: e.clientX,
                        startWidth: handle.parentElement.offsetWidth
                    };
                    e.preventDefault();
                }
            });

            document.addEventListener('mousemove', (e) => {
                if (resizing) {
                    const diff = e.clientX - resizing.startX;
                    const newWidth = Math.max(50, resizing.startWidth + diff);
                    this.resizeColumn(resizing.columnIndex, newWidth);
                }
            });

            document.addEventListener('mouseup', () => {
                if (resizing) {
                    if (this.options.onColumnResize) {
                        this.options.onColumnResize(resizing.columnIndex, resizing.startWidth);
                    }
                    resizing = null;
                }
            });
        }

        // Virtual scrolling
        if (this.options.virtual) {
            const wrapper = this.container.querySelector('.flex-datagrid');
            wrapper.addEventListener('scroll', (e) => {
                this.state.scrollTop = e.target.scrollTop;
                this.calculateVisibleRange();
                this.render();
                this.attachEventListeners();
            });
        }

        // Copy/Paste
        if (this.options.copyPaste) {
            this.gridElement.addEventListener('copy', (e) => {
                if (this.state.selectedCell) {
                    const { row, col } = this.state.selectedCell;
                    const column = this.options.columns[col];
                    const value = this.getCellValue(this.state.data[row], column.key);
                    e.clipboardData.setData('text/plain', value);
                    e.preventDefault();
                }
            });

            this.gridElement.addEventListener('paste', (e) => {
                if (this.state.selectedCell && this.options.editable) {
                    const text = e.clipboardData.getData('text/plain');
                    const { row, col } = this.state.selectedCell;
                    this.updateCellValue(row, col, text);
                    e.preventDefault();
                }
            });
        }
    }

    selectCell(row, col) {
        this.state.selectedCell = { row, col };
        this.emit('cellSelect', { row, col });

        // Focus the cell
        const cell = this.gridElement.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (cell) {
            cell.focus();
        }
    }

    moveCellSelection(rowDelta, colDelta) {
        if (!this.state.selectedCell) return;

        const newRow = Math.max(0, Math.min(this.state.data.length - 1, this.state.selectedCell.row + rowDelta));
        const newCol = Math.max(0, Math.min(this.options.columns.length - 1, this.state.selectedCell.col + colDelta));

        this.selectCell(newRow, newCol);
    }

    editCell(row, col) {
        if (!this.options.editable) return;

        this.state.editingCell = { row, col };
        this.render();
        this.attachEventListeners();

        if (this.options.onCellEdit) {
            this.options.onCellEdit(row, col);
        }

        this.emit('cellEdit', { row, col });
    }

    saveCell(value) {
        if (!this.state.editingCell) return;

        const { row, col } = this.state.editingCell;
        this.updateCellValue(row, col, value);

        this.state.editingCell = null;
        this.render();
        this.attachEventListeners();
    }

    cancelEdit() {
        this.state.editingCell = null;
        this.render();
        this.attachEventListeners();
    }

    updateCellValue(row, col, value) {
        const column = this.options.columns[col];
        const keys = column.key.split('.');
        let obj = this.state.data[row];

        for (let i = 0; i < keys.length - 1; i++) {
            obj = obj[keys[i]];
        }

        obj[keys[keys.length - 1]] = value;

        if (this.options.onCellChange) {
            this.options.onCellChange(row, col, value);
        }

        this.emit('cellChange', { row, col, value });
    }

    resizeColumn(colIndex, width) {
        this.options.columns[colIndex].width = `${width}px`;
        this.render();
        this.attachEventListeners();
    }

    setData(data) {
        this.state.data = data;
        this.calculateVisibleRange();
        this.render();
        this.attachEventListeners();
    }

    getData() {
        return this.state.data;
    }

    destroy() {
        this.container.innerHTML = '';
        super.destroy();
    }
}
