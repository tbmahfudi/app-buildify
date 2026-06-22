/**
 * FlexDatepicker Component Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexDatepicker from '../../frontend/assets/js/components/flex-datepicker.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

describe('FlexDatepicker', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('renders trigger input and hidden popup by default', () => {
            const dp = new FlexDatepicker(container);
            expect(container.querySelector('.flex-dp-trigger')).toBeTruthy();
            expect(container.querySelector('.flex-dp-popup')).toBeTruthy();
            expect(container.querySelector('.flex-dp-popup').classList.contains('hidden')).toBe(true);
        });

        it('renders with label and required marker', () => {
            new FlexDatepicker(container, { label: 'Birth Date', required: true });
            const label = container.querySelector('label');
            expect(label).toBeTruthy();
            expect(label.textContent).toContain('Birth Date');
            expect(label.innerHTML).toContain('*');
        });

        it('sets initial value from ISO string', () => {
            const dp = new FlexDatepicker(container, { value: '2025-06-15' });
            expect(dp.state.value).toBeInstanceOf(Date);
            expect(dp.state.value.getFullYear()).toBe(2025);
            expect(dp.state.value.getMonth()).toBe(5);   // 0-indexed
            expect(dp.state.value.getDate()).toBe(15);
        });

        it('renders inline calendar when inline:true', () => {
            new FlexDatepicker(container, { inline: true });
            const popup = container.querySelector('.flex-dp-popup');
            expect(popup).toBeTruthy();
            expect(popup.classList.contains('hidden')).toBe(false);
        });
    });

    describe('Calendar rendering', () => {
        it('renders correct number of day cells', () => {
            // June 2025 has 30 days
            const dp = new FlexDatepicker(container, { value: '2025-06-01', inline: true });
            const days = container.querySelectorAll('.flex-dp-day');
            expect(days.length).toBe(30);
        });

        it('marks today with a border class', () => {
            const today = new Date();
            const dp = new FlexDatepicker(container, {
                value: `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-01`,
                inline: true
            });
            // navigate to current month/year
            dp.state.viewYear  = today.getFullYear();
            dp.state.viewMonth = today.getMonth();
            dp._refreshPopup();
            const todayBtn = container.querySelector('.flex-dp-day[data-date="' +
                `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}` + '"]');
            expect(todayBtn).toBeTruthy();
            expect(todayBtn.className).toContain('border-blue-400');
        });

        it('disables dates before minDate', () => {
            new FlexDatepicker(container, {
                value: '2025-06-01',
                minDate: '2025-06-15',
                inline: true,
            });
            const btn = container.querySelector('.flex-dp-day[data-date="2025-06-10"]');
            expect(btn.disabled).toBe(true);
        });
    });

    describe('Value selection', () => {
        it('emits change event on date click', () => {
            const onChange = vi.fn();
            const dp = new FlexDatepicker(container, {
                value: '2025-06-01',
                inline: true,
                onChange,
            });
            const dayBtn = container.querySelector('.flex-dp-day[data-date="2025-06-10"]');
            dayBtn.click();
            expect(onChange).toHaveBeenCalledOnce();
            const { value: date, formatted } = onChange.mock.calls[0][0];
            expect(date.getDate()).toBe(10);
            expect(formatted).toBe('2025-06-10');
        });

        it('updates input display value after selection', () => {
            const dp = new FlexDatepicker(container, { value: '2025-06-01', inline: true });
            dp._selectDate(new Date(2025, 5, 20));
            const input = container.querySelector('.flex-dp-input');
            expect(input.value).toBe('2025-06-20');
        });

        it('clears value on clear button click', () => {
            const onChange = vi.fn();
            const dp = new FlexDatepicker(container, {
                value: '2025-06-01',
                inline: true,
                clearable: true,
                onChange,
            });
            const clearBtn = container.querySelector('.flex-dp-clear-cal');
            clearBtn?.click();
            expect(dp.state.value).toBeNull();
            expect(onChange).toHaveBeenCalledWith({ value: null, formatted: null });
        });
    });

    describe('Navigation', () => {
        it('navigates to previous month', () => {
            const dp = new FlexDatepicker(container, { value: '2025-06-01', inline: true });
            expect(dp.state.viewMonth).toBe(5);
            container.querySelector('.flex-dp-prev').click();
            expect(dp.state.viewMonth).toBe(4);
        });

        it('wraps from January to December when going prev', () => {
            const dp = new FlexDatepicker(container, { value: '2025-01-01', inline: true });
            container.querySelector('.flex-dp-prev').click();
            expect(dp.state.viewMonth).toBe(11);
            expect(dp.state.viewYear).toBe(2024);
        });

        it('navigates to next month', () => {
            const dp = new FlexDatepicker(container, { value: '2025-06-01', inline: true });
            container.querySelector('.flex-dp-next').click();
            expect(dp.state.viewMonth).toBe(6);
        });
    });

    describe('Public API', () => {
        it('getValue returns current Date or null', () => {
            const dp = new FlexDatepicker(container, { value: '2025-06-15' });
            expect(dp.getValue()).toBeInstanceOf(Date);
        });

        it('setValue updates state and input', () => {
            const dp = new FlexDatepicker(container);
            dp.setValue('2025-12-25');
            expect(dp.state.value.getMonth()).toBe(11);
            const input = container.querySelector('.flex-dp-input');
            expect(input.value).toBe('2025-12-25');
        });

        it('setError renders error message', () => {
            const dp = new FlexDatepicker(container, { label: 'Date' });
            dp.setError('Date is required');
            expect(container.innerHTML).toContain('Date is required');
        });
    });

    describe('Format option', () => {
        it('formats output using custom format string', () => {
            const dp = new FlexDatepicker(container, { format: 'DD/MM/YYYY', value: '2025-06-15' });
            expect(container.querySelector('.flex-dp-input').value).toBe('15/06/2025');
        });
    });
});
