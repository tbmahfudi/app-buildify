/**
 * FlexSection Component
 *
 * Full-width semantic page sections with backgrounds, consistent spacing, and slotted content areas.
 * Provides preset variants for common section types and flexible configuration options.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Section variants (hero, content, feature, cta, footer)
 * - Multiple background types (solid, gradient, image, pattern)
 * - Slot system for header, body, and footer content
 * - Responsive spacing with preset and custom configurations
 * - Width control via FlexContainer integration
 * - Dividers (top/bottom borders)
 * - Sticky headers, parallax effects, scroll snap
 * - Animation and viewport triggers
 *
 * @example
 * // Hero section with gradient
 * const hero = new FlexSection('#hero', {
 *   variant: 'hero',
 *   padding: '2xl',
 *   background: {
 *     type: 'gradient',
 *     gradient: { from: 'indigo-600', to: 'purple-600' }
 *   },
 *   slots: {
 *     body: { content: heroContent, align: 'center' }
 *   }
 * });
 *
 * @example
 * // Content section with container
 * const content = new FlexSection('#content', {
 *   variant: 'content',
 *   width: 'contained',
 *   slots: {
 *     header: { content: '<h2>About Us</h2>' },
 *     body: { content: bodyContent }
 *   }
 * });
 */

import { BREAKPOINTS, SPACING_SCALE, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import FlexContainer from './flex-container.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexSection extends BaseComponent {
    /**
     * Section variant presets
     */
    static VARIANTS = {
        hero: {
            padding: '2xl',
            textAlign: 'center',
            minHeight: '500px'
        },
        content: {
            padding: 'xl',
            textAlign: 'left'
        },
        feature: {
            padding: 'xl',
            backgroundSupport: true
        },
        cta: {
            padding: 'lg',
            textAlign: 'center'
        },
        footer: {
            padding: 'lg',
            textAlign: 'left'
        },
        custom: {}
    };

    /**
     * Spacing scale presets
     */
    static SPACING = {
        sm: { xs: 8, lg: 10 },      // 2rem -> 2.5rem
        md: { xs: 10, lg: 12 },     // 2.5rem -> 3rem
        lg: { xs: 12, lg: 16 },     // 3rem -> 4rem
        xl: { xs: 16, lg: 20 },     // 4rem -> 5rem
        '2xl': { xs: 20, lg: 28 }   // 5rem -> 7rem
    };

    /**
     * Default options
     */
    static DEFAULTS = {
        variant: 'content',
        width: 'contained',      // fluid | contained | breakout
        padding: 'xl',
        paddingTop: null,
        paddingBottom: null,
        background: null,
        slots: {},
        divider: null,
        sticky: false,
        scrollSnap: false,
        parallax: null,
        animated: null,
        tag: 'section',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexSection.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.sectionElement = null;
        this.containerInstance = null;
        this.slots = {
            header: null,
            body: null,
            footer: null
        };
        this.parallaxHandler = null;

        this.init();
    }

    /**
     * Initialize the section
     */
    init() {
        this.resolveOptions();
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Resolve configuration options
     */
    resolveOptions() {
        const { variant } = this.options;

        // Apply variant defaults
        if (variant && FlexSection.VARIANTS[variant]) {
            const variantDefaults = FlexSection.VARIANTS[variant];
            this.options = { ...variantDefaults, ...this.options };
        }

        // Resolve padding
        this.resolvePadding();
    }

    /**
     * Resolve padding configuration
     */
    resolvePadding() {
        const { padding, paddingTop, paddingBottom } = this.options;

        // Resolve top padding
        if (paddingTop !== null) {
            this.paddingTopConfig = typeof paddingTop === 'object' ? paddingTop : { xs: paddingTop };
        } else if (typeof padding === 'string' && FlexSection.SPACING[padding]) {
            this.paddingTopConfig = { ...FlexSection.SPACING[padding] };
        } else if (typeof padding === 'object') {
            this.paddingTopConfig = padding;
        } else {
            this.paddingTopConfig = FlexSection.SPACING.xl;
        }

        // Resolve bottom padding
        if (paddingBottom !== null) {
            this.paddingBottomConfig = typeof paddingBottom === 'object' ? paddingBottom : { xs: paddingBottom };
        } else if (typeof padding === 'string' && FlexSection.SPACING[padding]) {
            this.paddingBottomConfig = { ...FlexSection.SPACING[padding] };
        } else if (typeof padding === 'object') {
            this.paddingBottomConfig = padding;
        } else {
            this.paddingBottomConfig = FlexSection.SPACING.xl;
        }
    }

    /**
     * Render the section
     */
    render() {
        // Get or create section element
        if (this.container instanceof HTMLElement) {
            this.sectionElement = this.container;
        } else {
            this.sectionElement = document.querySelector(this.container);
        }

        if (!this.sectionElement) {
            console.error(`FlexSection: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.sectionElement.classList.add('flex-section');
        this.sectionElement.classList.add(`flex-section--${this.options.variant}`);

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.sectionElement.classList.add(...this.options.classes);
        }

        // Apply background
        if (this.options.background) {
            this.applyBackground();
        }

        // Apply spacing
        this.applySpacing();

        // Create dividers
        if (this.options.divider) {
            this.createDividers();
        }

        // Create slot structure
        this.createSlotStructure();

        // Apply additional features
        if (this.options.sticky) {
            this.applySticky();
        }

        if (this.options.scrollSnap) {
            this.applyScrollSnap();
        }

        if (this.options.parallax) {
            this.initParallax();
        }

        if (this.options.animated) {
            this.initAnimations();
        }

        // Apply text alignment
        if (this.options.textAlign) {
            this.sectionElement.style.textAlign = this.options.textAlign;
        }

        // Apply min-height
        if (this.options.minHeight) {
            this.sectionElement.style.minHeight = this.options.minHeight;
        }

        this.emit(EVENTS.RENDER);
    }

    /**
     * Create slot structure (header, body, footer)
     */
    createSlotStructure() {
        const { slots, width } = this.options;

        // Create wrapper for slots
        const slotsWrapper = this.createElement('div', ['flex-section__slots']);

        // Apply width control
        if (width === 'contained') {
            // Use FlexContainer for width control
            this.containerInstance = new FlexContainer(slotsWrapper, {
                preset: 'standard',
                gutter: true
            });
        } else if (width === 'breakout') {
            this.containerInstance = new FlexContainer(slotsWrapper, {
                preset: 'wide',
                gutter: true
            });
        }
        // If 'fluid', no container wrapper needed

        // Create slots
        ['header', 'body', 'footer'].forEach(slotName => {
            if (slots[slotName]) {
                this.createSlot(slotName, slots[slotName], slotsWrapper);
            }
        });

        this.sectionElement.appendChild(slotsWrapper);
    }

    /**
     * Create individual slot
     */
    createSlot(slotName, slotConfig, wrapper) {
        const slotElement = this.createElement('div', [`flex-section__${slotName}`]);

        // Apply slot configuration
        if (typeof slotConfig === 'object' && !slotConfig.nodeType) {
            const { content, align, maxWidth, layout } = slotConfig;

            // Apply alignment
            if (align) {
                slotElement.style.textAlign = align;
            }

            // Apply max-width
            if (maxWidth) {
                slotElement.style.maxWidth = maxWidth;
                if (align === 'center') {
                    slotElement.style.marginLeft = 'auto';
                    slotElement.style.marginRight = 'auto';
                }
            }

            // Add content
            if (content) {
                if (typeof content === 'string') {
                    slotElement.innerHTML = content;
                } else if (content instanceof HTMLElement) {
                    slotElement.appendChild(content);
                } else if (content.getElement && typeof content.getElement === 'function') {
                    // Component with getElement method
                    slotElement.appendChild(content.getElement());
                }
            }

            // Apply layout class
            if (layout) {
                slotElement.classList.add(`flex-section__${slotName}--${layout}`);
            }
        } else {
            // Simple content (string or element)
            if (typeof slotConfig === 'string') {
                slotElement.innerHTML = slotConfig;
            } else if (slotConfig instanceof HTMLElement) {
                slotElement.appendChild(slotConfig);
            } else if (slotConfig.getElement && typeof slotConfig.getElement === 'function') {
                slotElement.appendChild(slotConfig.getElement());
            }
        }

        this.slots[slotName] = slotElement;
        wrapper.appendChild(slotElement);
    }

    /**
     * Apply background styles
     */
    applyBackground() {
        const { background } = this.options;

        if (!background) return;

        const { type, color, gradient, image, pattern } = background;

        if (type === 'solid' && color) {
            // Solid color background
            this.sectionElement.classList.add(`bg-${color}`);
        } else if (type === 'gradient' && gradient) {
            // Gradient background
            const { from, via, to, direction = 'to-br' } = gradient;
            let gradientClasses = [`bg-gradient-${direction}`, `from-${from}`, `to-${to}`];
            if (via) {
                gradientClasses.push(`via-${via}`);
            }
            this.sectionElement.classList.add(...gradientClasses);
        } else if (type === 'image' && image) {
            // Image background
            this.applyImageBackground(image);
        } else if (type === 'pattern' && pattern) {
            // Pattern background
            this.applyPatternBackground(pattern);
        }
    }

    /**
     * Apply image background
     */
    applyImageBackground(imageConfig) {
        const {
            url,
            overlay = null,
            overlayOpacity = 0.5,
            position = 'center',
            size = 'cover',
            parallax = false
        } = imageConfig;

        // Set background image
        this.sectionElement.style.backgroundImage = `url(${url})`;
        this.sectionElement.style.backgroundPosition = position;
        this.sectionElement.style.backgroundSize = size;
        this.sectionElement.style.backgroundRepeat = 'no-repeat';

        if (!parallax) {
            this.sectionElement.style.backgroundAttachment = 'scroll';
        }

        // Add overlay if specified
        if (overlay) {
            const overlayElement = this.createElement('div', ['flex-section__overlay']);
            overlayElement.style.backgroundColor = overlay;
            overlayElement.style.opacity = overlayOpacity;
            overlayElement.style.position = 'absolute';
            overlayElement.style.top = '0';
            overlayElement.style.left = '0';
            overlayElement.style.width = '100%';
            overlayElement.style.height = '100%';
            overlayElement.style.pointerEvents = 'none';

            // Ensure section has position relative
            this.sectionElement.style.position = 'relative';

            this.sectionElement.prepend(overlayElement);
        }
    }

    /**
     * Apply pattern background
     */
    applyPatternBackground(pattern) {
        // Add pattern class for CSS-based patterns
        this.sectionElement.classList.add(`bg-pattern-${pattern}`);
    }

    /**
     * Apply spacing (padding)
     */
    applySpacing() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();

        // Apply top padding
        const paddingTop = this.getResponsiveValue(this.paddingTopConfig, currentBreakpoint);
        if (paddingTop !== null && paddingTop !== undefined) {
            const paddingTopValue = SPACING_SCALE[paddingTop] || paddingTop;
            this.sectionElement.style.paddingTop = paddingTopValue;
        }

        // Apply bottom padding
        const paddingBottom = this.getResponsiveValue(this.paddingBottomConfig, currentBreakpoint);
        if (paddingBottom !== null && paddingBottom !== undefined) {
            const paddingBottomValue = SPACING_SCALE[paddingBottom] || paddingBottom;
            this.sectionElement.style.paddingBottom = paddingBottomValue;
        }
    }

    /**
     * Create dividers
     */
    createDividers() {
        const { divider } = this.options;

        if (!divider) return;

        const {
            top = false,
            bottom = false,
            variant = 'line',
            color = 'gray-200',
            thickness = '1px'
        } = divider;

        if (top) {
            this.sectionElement.style.borderTop = `${thickness} ${variant === 'dashed' ? 'dashed' : variant === 'dotted' ? 'dotted' : 'solid'} var(--${color})`;
        }

        if (bottom) {
            this.sectionElement.style.borderBottom = `${thickness} ${variant === 'dashed' ? 'dashed' : variant === 'dotted' ? 'dotted' : 'solid'} var(--${color})`;
        }
    }

    /**
     * Apply sticky positioning
     */
    applySticky() {
        this.sectionElement.style.position = 'sticky';
        this.sectionElement.style.top = '0';
        this.sectionElement.style.zIndex = '10';
    }

    /**
     * Apply scroll snap
     */
    applyScrollSnap() {
        this.sectionElement.style.scrollSnapAlign = 'start';
    }

    /**
     * Initialize parallax effect
     */
    initParallax() {
        const { parallax } = this.options;

        if (!parallax || !parallax.enabled) return;

        const speed = parallax.speed || 0.5;

        this.parallaxHandler = this.throttle(() => {
            const scrolled = window.pageYOffset;
            const sectionTop = this.sectionElement.offsetTop;
            const sectionHeight = this.sectionElement.offsetHeight;

            // Only apply parallax when section is in viewport
            if (scrolled + window.innerHeight > sectionTop && scrolled < sectionTop + sectionHeight) {
                const offset = (scrolled - sectionTop) * speed;
                this.sectionElement.style.backgroundPositionY = `${offset}px`;
            }
        }, 16); // ~60fps

        window.addEventListener('scroll', this.parallaxHandler, { passive: true });
    }

    /**
     * Initialize animations
     */
    initAnimations() {
        const { animated } = this.options;

        if (!animated || !animated.enabled) return;

        const { trigger = 'viewport', effect = 'fade-in' } = animated;

        if (trigger === 'viewport') {
            // Use Intersection Observer for viewport-triggered animations
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.sectionElement.classList.add(`animate-${effect}`);
                            observer.unobserve(entry.target);
                        }
                    });
                },
                { threshold: 0.1 }
            );

            observer.observe(this.sectionElement);
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.applySpacing();
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint()
            });
        });
    }

    /**
     * Set section variant
     * @param {string} variant - Variant name
     */
    setVariant(variant) {
        if (!FlexSection.VARIANTS[variant]) {
            console.warn(`FlexSection: Invalid variant "${variant}"`);
            return;
        }

        // Remove old variant class
        this.sectionElement.classList.remove(`flex-section--${this.options.variant}`);

        // Update options
        this.options.variant = variant;
        const variantDefaults = FlexSection.VARIANTS[variant];
        this.options = { ...this.options, ...variantDefaults };

        // Add new variant class
        this.sectionElement.classList.add(`flex-section--${variant}`);

        this.emit(EVENTS.UPDATE, { variant });
    }

    /**
     * Update background
     * @param {object} background - Background configuration
     */
    updateBackground(background) {
        // Remove old background classes and styles
        this.sectionElement.className = this.sectionElement.className
            .split(' ')
            .filter(cls => !cls.startsWith('bg-'))
            .join(' ');

        this.sectionElement.style.backgroundImage = '';
        this.sectionElement.style.backgroundPosition = '';
        this.sectionElement.style.backgroundSize = '';

        // Apply new background
        this.options.background = background;
        this.applyBackground();

        this.emit(EVENTS.UPDATE, { background });
    }

    /**
     * Update slot content
     * @param {string} slotName - Slot name (header, body, footer)
     * @param {object} config - Slot configuration
     */
    updateSlot(slotName, config) {
        if (!['header', 'body', 'footer'].includes(slotName)) {
            console.warn(`FlexSection: Invalid slot name "${slotName}"`);
            return;
        }

        const slotElement = this.slots[slotName];

        if (!slotElement) {
            console.warn(`FlexSection: Slot "${slotName}" not found`);
            return;
        }

        // Clear current content
        slotElement.innerHTML = '';

        // Add new content
        const content = config.content || config;

        if (typeof content === 'string') {
            slotElement.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            slotElement.appendChild(content);
        } else if (content.getElement && typeof content.getElement === 'function') {
            slotElement.appendChild(content.getElement());
        }

        this.emit(EVENTS.UPDATE, { slot: slotName });
    }

    /**
     * Update padding
     * @param {string|object} padding - Padding value or responsive config
     */
    updatePadding(padding) {
        this.options.padding = padding;
        this.resolvePadding();
        this.applySpacing();

        this.emit(EVENTS.UPDATE, { padding });
    }

    /**
     * Enable or disable parallax
     * @param {boolean} enabled - Whether to enable parallax
     */
    enableParallax(enabled) {
        if (enabled) {
            if (!this.parallaxHandler) {
                this.options.parallax = { enabled: true, speed: 0.5 };
                this.initParallax();
            }
        } else {
            if (this.parallaxHandler) {
                window.removeEventListener('scroll', this.parallaxHandler);
                this.parallaxHandler = null;
                this.sectionElement.style.backgroundPositionY = '';
            }
        }

        this.emit(EVENTS.UPDATE, { parallax: enabled });
    }

    /**
     * Scroll to this section
     * @param {boolean} smooth - Whether to use smooth scrolling
     */
    scrollToSection(smooth = true) {
        this.sectionElement.scrollIntoView({
            behavior: smooth ? 'smooth' : 'auto',
            block: 'start'
        });
    }

    /**
     * Get section element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.sectionElement;
    }

    /**
     * Get slot element
     * @param {string} slotName - Slot name
     * @returns {HTMLElement|null}
     */
    getSlot(slotName) {
        return this.slots[slotName] || null;
    }

    /**
     * Destroy the section
     */
    destroy() {
        // Remove parallax handler
        if (this.parallaxHandler) {
            window.removeEventListener('scroll', this.parallaxHandler);
        }

        // Destroy container instance
        if (this.containerInstance) {
            this.containerInstance.destroy();
        }

        // Remove classes
        this.sectionElement.classList.remove('flex-section');
        this.sectionElement.classList.remove(`flex-section--${this.options.variant}`);

        if (this.options.classes.length > 0) {
            this.sectionElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.sectionElement.style.paddingTop = '';
        this.sectionElement.style.paddingBottom = '';
        this.sectionElement.style.textAlign = '';
        this.sectionElement.style.minHeight = '';
        this.sectionElement.style.position = '';
        this.sectionElement.style.top = '';
        this.sectionElement.style.zIndex = '';
        this.sectionElement.style.backgroundImage = '';
        this.sectionElement.style.backgroundPosition = '';
        this.sectionElement.style.backgroundSize = '';
        this.sectionElement.style.backgroundRepeat = '';
        this.sectionElement.style.backgroundAttachment = '';
        this.sectionElement.style.borderTop = '';
        this.sectionElement.style.borderBottom = '';

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
