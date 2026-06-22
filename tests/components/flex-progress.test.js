/**
 * FlexProgress Component Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexProgress from '../../frontend/assets/js/components/flex-progress.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

describe('FlexProgress', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    // ── Bar variant ──────────────────────────────────────────────────────────

    describe('Bar variant (default)', () => {
        it('renders a progress track and fill', () => {
            new FlexProgress(container, { value: 50 });
            expect(container.querySelector('.flex-progress-track')).toBeTruthy();
            expect(container.querySelector('.flex-progress-fill')).toBeTruthy();
        });

        it('sets fill width to correct percentage', () => {
            new FlexProgress(container, { value: 75, max: 100 });
            const fill = container.querySelector('.flex-progress-fill');
            expect(fill.style.width).toBe('75%');
        });

        it('clamps value to min/max range', () => {
            const p = new FlexProgress(container, { value: 150, max: 100 });
            expect(p.state.value).toBe(100);
            expect(container.querySelector('.flex-progress-fill').style.width).toBe('100%');
        });

        it('handles min offset correctly', () => {
            const p = new FlexProgress(container, { value: 60, min: 50, max: 100 });
            // (60-50)/(100-50) = 20%
            expect(p.getPercent()).toBeCloseTo(20);
        });

        it('renders right-position label when showLabel:true', () => {
            new FlexProgress(container, { value: 40, showLabel: true, labelPosition: 'right' });
            expect(container.innerHTML).toContain('40%');
        });

        it('renders custom label string instead of percentage', () => {
            new FlexProgress(container, { value: 30, showLabel: true, label: 'Loading…', labelPosition: 'right' });
            expect(container.innerHTML).toContain('Loading…');
            const fillSpan = container.querySelector('.flex-progress-fill span'); expect(fillSpan).toBeFalsy(); // no pct label rendered when custom label used
        });

        it('renders top label', () => {
            new FlexProgress(container, { value: 60, showLabel: true, labelPosition: 'top' });
            expect(container.innerHTML).toContain('60%');
        });

        it('applies correct size class', () => {
            new FlexProgress(container, { value: 50, size: 'lg' });
            expect(container.querySelector('.flex-progress-track').className).toContain('h-4');
        });

        it('applies blue fill class by default', () => {
            new FlexProgress(container, { value: 50 });
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-blue-500');
        });

        it('applies green fill class when color:green', () => {
            new FlexProgress(container, { value: 50, color: 'green' });
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-green-500');
        });

        it('auto color: red below 33%', () => {
            new FlexProgress(container, { value: 20, color: 'auto' });
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-red-500');
        });

        it('auto color: amber between 33-67%', () => {
            new FlexProgress(container, { value: 50, color: 'auto' });
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-amber-500');
        });

        it('auto color: green above 67%', () => {
            new FlexProgress(container, { value: 80, color: 'auto' });
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-green-500');
        });

        it('renders indeterminate bar without fill width', () => {
            new FlexProgress(container, { indeterminate: true });
            expect(container.querySelector('.flex-progress-indeterminate')).toBeTruthy();
            expect(container.querySelector('.flex-progress-fill')).toBeFalsy();
        });

        it('applies striped class when striped:true', () => {
            new FlexProgress(container, { value: 50, striped: true });
            expect(container.querySelector('.flex-progress-striped')).toBeTruthy();
        });

        it('applies animated class when animated:true', () => {
            new FlexProgress(container, { value: 50, animated: true });
            expect(container.querySelector('.flex-progress-animated')).toBeTruthy();
        });

        it('sets aria attributes on fill', () => {
            new FlexProgress(container, { value: 60, min: 0, max: 200 });
            const fill = container.querySelector('.flex-progress-fill');
            expect(fill.getAttribute('aria-valuenow')).toBe('60');
            expect(fill.getAttribute('aria-valuemax')).toBe('200');
        });
    });

    // ── Circular variant ─────────────────────────────────────────────────────

    describe('Circular variant', () => {
        it('renders an SVG element', () => {
            new FlexProgress(container, { variant: 'circular', value: 50 });
            expect(container.querySelector('svg')).toBeTruthy();
        });

        it('renders two circles (track + fill)', () => {
            new FlexProgress(container, { variant: 'circular', value: 50 });
            expect(container.querySelectorAll('circle').length).toBe(2);
        });

        it('shows value percentage text by default', () => {
            new FlexProgress(container, { variant: 'circular', value: 75 });
            expect(container.innerHTML).toContain('75%');
        });

        it('hides value when showValue:false', () => {
            new FlexProgress(container, { variant: 'circular', value: 75, showValue: false });
            expect(container.querySelector('.flex-progress-value')).toBeFalsy();
        });

        it('SVG circle uses correct stroke color', () => {
            new FlexProgress(container, { variant: 'circular', value: 50, color: 'green' });
            const fill = container.querySelector('.flex-progress-circle-fill');
            expect(fill.getAttribute('stroke')).toBe('#22c55e');
        });

        it('renders indeterminate spin class', () => {
            new FlexProgress(container, { variant: 'circular', indeterminate: true });
            expect(container.querySelector('svg').className.baseVal).toContain('flex-progress-spin');
        });
    });

    // ── Segmented variant ─────────────────────────────────────────────────────

    describe('Segmented variant', () => {
        const segs = [
            { value: 40, color: 'blue',  label: 'Used' },
            { value: 30, color: 'green', label: 'Free' },
            { value: 30, color: 'gray',  label: 'Reserved' },
        ];

        it('renders one child div per segment', () => {
            new FlexProgress(container, { variant: 'segmented', segments: segs });
            // segments rendered inside the track wrapper
            const track = container.querySelector('.flex-progress--segmented');
            expect(track).toBeTruthy();
        });

        it('renders legend items for labelled segments', () => {
            new FlexProgress(container, { variant: 'segmented', segments: segs });
            expect(container.innerHTML).toContain('Used');
            expect(container.innerHTML).toContain('Free');
            expect(container.innerHTML).toContain('Reserved');
        });

        it('applies correct color per segment', () => {
            new FlexProgress(container, { variant: 'segmented', segments: segs });
            expect(container.innerHTML).toContain('bg-blue-500');
            expect(container.innerHTML).toContain('bg-green-500');
        });
    });

    // ── Public API ────────────────────────────────────────────────────────────

    describe('setValue()', () => {
        it('updates state value', () => {
            const p = new FlexProgress(container, { value: 0 });
            p.setValue(60);
            expect(p.getValue()).toBe(60);
        });

        it('updates fill width in DOM', () => {
            const p = new FlexProgress(container, { value: 0 });
            p.setValue(80);
            expect(container.querySelector('.flex-progress-fill').style.width).toBe('80%');
        });

        it('clamps to max', () => {
            const p = new FlexProgress(container, { value: 50, max: 100 });
            p.setValue(200);
            expect(p.getValue()).toBe(100);
        });

        it('clamps to min', () => {
            const p = new FlexProgress(container, { value: 50, min: 10 });
            p.setValue(0);
            expect(p.getValue()).toBe(10);
        });

        it('calls onChange callback', () => {
            const onChange = vi.fn();
            const p = new FlexProgress(container, { value: 0, onChange });
            p.setValue(50);
            expect(onChange).toHaveBeenCalled();
        });
    });

    describe('increment() / decrement()', () => {
        it('increments by 1 by default', () => {
            const p = new FlexProgress(container, { value: 40 });
            p.increment();
            expect(p.getValue()).toBe(41);
        });

        it('increments by custom step', () => {
            const p = new FlexProgress(container, { value: 40 });
            p.increment(10);
            expect(p.getValue()).toBe(50);
        });

        it('decrements by 1 by default', () => {
            const p = new FlexProgress(container, { value: 40 });
            p.decrement();
            expect(p.getValue()).toBe(39);
        });
    });

    describe('reset() and complete()', () => {
        it('reset() sets value to min', () => {
            const p = new FlexProgress(container, { value: 70, min: 10 });
            p.reset();
            expect(p.getValue()).toBe(10);
        });

        it('complete() sets value to max', () => {
            const p = new FlexProgress(container, { value: 30, max: 100 });
            p.complete();
            expect(p.getValue()).toBe(100);
        });
    });

    describe('setIndeterminate()', () => {
        it('switches to indeterminate mode and re-renders', () => {
            const p = new FlexProgress(container, { value: 50 });
            p.setIndeterminate(true);
            expect(container.querySelector('.flex-progress-indeterminate')).toBeTruthy();
        });

        it('clears indeterminate mode', () => {
            const p = new FlexProgress(container, { indeterminate: true });
            p.setIndeterminate(false);
            expect(container.querySelector('.flex-progress-fill')).toBeTruthy();
        });
    });

    describe('setColor()', () => {
        it('changes color and re-renders', () => {
            const p = new FlexProgress(container, { value: 50, color: 'blue' });
            p.setColor('red');
            expect(container.querySelector('.flex-progress-fill').className).toContain('bg-red-500');
        });
    });

    describe('getPercent()', () => {
        it('returns correct percentage', () => {
            const p = new FlexProgress(container, { value: 25, max: 100 });
            expect(p.getPercent()).toBe(25);
        });

        it('returns 0 when value equals min', () => {
            const p = new FlexProgress(container, { value: 20, min: 20, max: 80 });
            expect(p.getPercent()).toBe(0);
        });

        it('returns 100 when value equals max', () => {
            const p = new FlexProgress(container, { value: 80, min: 20, max: 80 });
            expect(p.getPercent()).toBe(100);
        });
    });
});
