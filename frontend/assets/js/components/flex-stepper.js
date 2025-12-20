/**
 * FlexStepper - Multi-step Form/Wizard Component
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';
import { hasPermission } from '../rbac.js';

export default class FlexStepper extends BaseComponent {
    static DEFAULTS = {
        steps: [],                  // Array of step definitions
        linear: true,               // Must complete in order
        showProgress: true,
        allowSkip: false,
        persistData: true,
        variant: 'horizontal',      // horizontal | vertical
        size: 'md',
        onStepChange: null,
        onComplete: null,
        onCancel: null,
        showBackButton: true,
        showCancelButton: true,
        nextButtonText: 'Next',
        backButtonText: 'Back',
        finishButtonText: 'Submit',
        cancelButtonText: 'Cancel',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            currentStepIndex: 0,
            completedSteps: new Set(),
            stepData: {},
            visitedSteps: new Set([0])
        };

        this.stepComponents = [];
        this.init();
    }

    async init() {
        await this.filterStepsByPermission();
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    async filterStepsByPermission() {
        this.accessibleSteps = [];

        for (const step of this.options.steps) {
            if (step.permission) {
                const hasAccess = await hasPermission(step.permission);
                if (hasAccess) {
                    this.accessibleSteps.push(step);
                }
            } else {
                this.accessibleSteps.push(step);
            }
        }
    }

    render() {
        this.container.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = `flex-stepper ${this.options.variant} ${this.options.classes.join(' ')}`;

        // Progress indicator
        if (this.options.showProgress) {
            wrapper.appendChild(this.renderProgress());
        }

        // Step content
        wrapper.appendChild(this.renderStepContent());

        // Navigation
        wrapper.appendChild(this.renderNavigation());

        this.container.appendChild(wrapper);
    }

    renderProgress() {
        const progress = document.createElement('div');

        if (this.options.variant === 'horizontal') {
            progress.className = 'flex items-center justify-between mb-8';

            this.accessibleSteps.forEach((step, index) => {
                const stepEl = this.renderProgressStep(step, index);
                progress.appendChild(stepEl);

                if (index < this.accessibleSteps.length - 1) {
                    const connector = document.createElement('div');
                    connector.className = `flex-1 h-1 mx-4 ${
                        index < this.state.currentStepIndex ? 'bg-blue-600' : 'bg-gray-300'
                    }`;
                    progress.appendChild(connector);
                }
            });
        } else {
            progress.className = 'flex flex-col gap-4 mb-8';

            this.accessibleSteps.forEach((step, index) => {
                const stepEl = this.renderProgressStep(step, index);
                progress.appendChild(stepEl);
            });
        }

        return progress;
    }

    renderProgressStep(step, index) {
        const isActive = index === this.state.currentStepIndex;
        const isCompleted = this.state.completedSteps.has(index);
        const isVisited = this.state.visitedSteps.has(index);

        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center gap-3';

        const circle = document.createElement('div');
        circle.className = `w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
            isCompleted ? 'bg-green-600 text-white' :
            isActive ? 'bg-blue-600 text-white' :
            isVisited ? 'bg-gray-300 text-gray-700' :
            'bg-gray-200 text-gray-400'
        }`;

        circle.innerHTML = isCompleted
            ? '<i class="ph ph-check text-xl"></i>'
            : (step.icon || (index + 1));

        wrapper.appendChild(circle);

        const info = document.createElement('div');
        info.className = 'flex-1';

        const title = document.createElement('div');
        title.className = `font-medium ${isActive ? 'text-blue-600' : 'text-gray-700'}`;
        title.textContent = step.title;

        info.appendChild(title);

        if (step.description) {
            const desc = document.createElement('div');
            desc.className = 'text-sm text-gray-500';
            desc.textContent = step.description;
            info.appendChild(desc);
        }

        wrapper.appendChild(info);

        return wrapper;
    }

    renderStepContent() {
        const content = document.createElement('div');
        content.className = 'step-content min-h-[400px] p-6 bg-white rounded-lg border border-gray-200 mb-6';
        content.id = 'step-content-container';

        const currentStep = this.accessibleSteps[this.state.currentStepIndex];

        if (currentStep.component) {
            if (typeof currentStep.component === 'function') {
                const instance = new currentStep.component(content, this.state.stepData[currentStep.id] || {});
                this.stepComponents[this.state.currentStepIndex] = instance;
            } else {
                content.appendChild(currentStep.component);
            }
        }

        return content;
    }

    renderNavigation() {
        const nav = document.createElement('div');
        nav.className = 'flex items-center justify-between';

        const left = document.createElement('div');
        left.className = 'flex gap-2';

        if (this.options.showCancelButton) {
            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition';
            cancelBtn.textContent = this.options.cancelButtonText;
            cancelBtn.setAttribute('data-cancel', 'true');
            left.appendChild(cancelBtn);
        }

        if (this.options.showBackButton && this.state.currentStepIndex > 0) {
            const backBtn = document.createElement('button');
            backBtn.className = 'px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition';
            backBtn.textContent = this.options.backButtonText;
            backBtn.setAttribute('data-back', 'true');
            left.appendChild(backBtn);
        }

        nav.appendChild(left);

        const right = document.createElement('div');
        const isLastStep = this.state.currentStepIndex === this.accessibleSteps.length - 1;

        const nextBtn = document.createElement('button');
        nextBtn.className = 'px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition';
        nextBtn.textContent = isLastStep ? this.options.finishButtonText : this.options.nextButtonText;
        nextBtn.setAttribute('data-next', 'true');
        right.appendChild(nextBtn);

        nav.appendChild(right);

        return nav;
    }

    attachEventListeners() {
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('[data-next]')) {
                this.nextStep();
            } else if (e.target.closest('[data-back]')) {
                this.previousStep();
            } else if (e.target.closest('[data-cancel]')) {
                this.cancel();
            }
        });
    }

    async nextStep() {
        const currentStep = this.accessibleSteps[this.state.currentStepIndex];

        // Validate current step
        if (currentStep.validate) {
            const isValid = await currentStep.validate();
            if (!isValid) {
                return;
            }
        }

        // Save step data
        if (this.options.persistData) {
            const stepComponent = this.stepComponents[this.state.currentStepIndex];
            if (stepComponent && stepComponent.getData) {
                this.state.stepData[currentStep.id] = stepComponent.getData();
            }
        }

        // Mark as completed
        this.state.completedSteps.add(this.state.currentStepIndex);

        // Check if last step
        if (this.state.currentStepIndex === this.accessibleSteps.length - 1) {
            this.complete();
            return;
        }

        // Move to next step
        const fromStep = this.state.currentStepIndex;
        this.state.currentStepIndex++;
        this.state.visitedSteps.add(this.state.currentStepIndex);

        if (this.options.onStepChange) {
            this.options.onStepChange(fromStep, this.state.currentStepIndex);
        }

        this.emit('stepChange', { from: fromStep, to: this.state.currentStepIndex });

        this.render();
        this.attachEventListeners();
    }

    previousStep() {
        if (this.state.currentStepIndex === 0) return;

        const fromStep = this.state.currentStepIndex;
        this.state.currentStepIndex--;

        if (this.options.onStepChange) {
            this.options.onStepChange(fromStep, this.state.currentStepIndex);
        }

        this.emit('stepChange', { from: fromStep, to: this.state.currentStepIndex });

        this.render();
        this.attachEventListeners();
    }

    complete() {
        if (this.options.onComplete) {
            this.options.onComplete(this.state.stepData);
        }

        this.emit('complete', { data: this.state.stepData });
    }

    cancel() {
        if (this.options.onCancel) {
            this.options.onCancel();
        }

        this.emit('cancel');
    }

    goToStep(index) {
        if (index < 0 || index >= this.accessibleSteps.length) return;

        if (this.options.linear && !this.state.completedSteps.has(index - 1) && index > 0) {
            return; // Can't skip steps in linear mode
        }

        const fromStep = this.state.currentStepIndex;
        this.state.currentStepIndex = index;
        this.state.visitedSteps.add(index);

        if (this.options.onStepChange) {
            this.options.onStepChange(fromStep, index);
        }

        this.emit('stepChange', { from: fromStep, to: index });

        this.render();
        this.attachEventListeners();
    }

    getData() {
        return this.state.stepData;
    }

    destroy() {
        this.stepComponents.forEach(component => {
            if (component && component.destroy) {
                component.destroy();
            }
        });
        this.container.innerHTML = '';
        super.destroy();
    }
}
