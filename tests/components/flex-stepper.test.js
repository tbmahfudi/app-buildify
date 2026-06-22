import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexStepper from '../../frontend/assets/js/components/flex-stepper.js';
import { createTestContainer, cleanupTestContainer, wait } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockResolvedValue(true)
}));

const steps = [
    { id: 'step1', title: 'Personal Info' },
    { id: 'step2', title: 'Address' },
    { id: 'step3', title: 'Review' }
];

describe('FlexStepper', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create stepper at step 0', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            expect(stepper.state.currentStepIndex).toBe(0);
        });

        it('should render step titles', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            expect(container.textContent).toContain('Personal Info');
            expect(container.textContent).toContain('Address');
        });

        it('should render navigation buttons', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            const nextBtn = container.querySelector('[data-next]');
            expect(nextBtn).toBeTruthy();
        });
    });

    describe('Navigation', () => {
        it('should go to next step', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            await stepper.nextStep();
            expect(stepper.state.currentStepIndex).toBe(1);
        });

        it('should go to previous step', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            await stepper.nextStep();
            stepper.previousStep();
            expect(stepper.state.currentStepIndex).toBe(0);
        });

        it('should not go before step 0', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            stepper.previousStep();
            expect(stepper.state.currentStepIndex).toBe(0);
        });

        it('should call onStepChange on navigation', async () => {
            const cb = vi.fn();
            const stepper = new FlexStepper(container, { steps, onStepChange: cb });
            await wait(50);
            await stepper.nextStep();
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('goToStep', () => {
        it('should jump to specific step when not linear', async () => {
            const stepper = new FlexStepper(container, { steps, linear: false });
            await wait(50);
            stepper.goToStep(2);
            expect(stepper.state.currentStepIndex).toBe(2);
        });
    });

    describe('Completion', () => {
        it('should call onComplete when finishing last step', async () => {
            const cb = vi.fn();
            const stepper = new FlexStepper(container, {
                steps: [{ id: 's1', title: 'Only' }],
                onComplete: cb
            });
            await wait(50);
            await stepper.nextStep();
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Progress tracking', () => {
        it('should track completed steps', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            await stepper.nextStep();
            expect(stepper.state.completedSteps.has(0)).toBe(true);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', async () => {
            const stepper = new FlexStepper(container, { steps });
            await wait(50);
            expect(() => stepper.destroy()).not.toThrow();
        });
    });
});
