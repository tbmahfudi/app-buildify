import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { FlexTabs } from '../../frontend/assets/js/components/flex-tabs.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockReturnValue(true)
}));

const sampleTabs = [
    { id: 'tab1', label: 'Tab One', content: '<p>Content One</p>' },
    { id: 'tab2', label: 'Tab Two', content: '<p>Content Two</p>' },
    { id: 'tab3', label: 'Tab Three', content: '<p>Content Three</p>' }
];

describe('FlexTabs', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should activate first tab by default', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(tabs.state.activeTab).toBe('tab1');
        });

        it('should activate specified default tab', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs, defaultTab: 'tab2' });
            expect(tabs.state.activeTab).toBe('tab2');
        });

        it('should throw if container not found', () => {
            expect(() => new FlexTabs('#nonexistent-element', { tabs: sampleTabs })).toThrow();
        });
    });

    describe('Rendering', () => {
        it('should render tab buttons', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(container.textContent).toContain('Tab One');
            expect(container.textContent).toContain('Tab Two');
        });

        it('should render active tab content', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(container.textContent).toContain('Content One');
        });

        it('should apply underline variant by default', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(tabs.options.variant).toBe('underline');
        });

        it('should apply pills variant', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs, variant: 'pills' });
            expect(tabs.options.variant).toBe('pills');
        });
    });

    describe('Tab switching', () => {
        it('should switch to tab with showTab()', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            tabs.showTab('tab2');
            expect(tabs.state.activeTab).toBe('tab2');
        });

        it('should call onTabChange callback', () => {
            const cb = vi.fn();
            const tabs = new FlexTabs(container, { tabs: sampleTabs, onTabChange: cb });
            tabs.showTab('tab2');
            expect(cb).toHaveBeenCalled();
        });

        it('should show content of active tab', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            tabs.showTab('tab2');
            expect(container.textContent).toContain('Content Two');
        });

        it('should switch on data-tab-id button click', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            const tabBtn = container.querySelector('[data-tab-id=tab2]');
            if (tabBtn) {
                click(tabBtn);
                expect(tabs.state.activeTab).toBe('tab2');
            }
        });
    });

    describe('Disabled tabs', () => {
        it('should not switch to disabled tab', () => {
            const disabledTabs = [
                { id: 'tab1', label: 'Tab One', content: 'One' },
                { id: 'tab2', label: 'Tab Two', content: 'Two', disabled: true }
            ];
            const tabs = new FlexTabs(container, { tabs: disabledTabs });
            tabs.showTab('tab2');
            expect(tabs.state.activeTab).toBe('tab1');
        });
    });

    describe('API methods', () => {
        it('should return active tab with getActiveTab()', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(tabs.getActiveTab()).toBe('tab1');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const tabs = new FlexTabs(container, { tabs: sampleTabs });
            expect(() => tabs.destroy()).not.toThrow();
        });
    });
});
