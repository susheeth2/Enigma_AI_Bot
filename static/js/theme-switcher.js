/**
 * Theme Switcher Component
 * Handles theme switching with smooth transitions, local storage, and accessibility
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = 'white'; // default theme
        this.themes = ['white', 'gray', 'dark'];
        this.transitionDuration = 300; // ms
        this.init();
    }

    init() {
        this.loadSavedTheme();
        this.createThemeSwitcher();
        this.bindEvents();
        this.applyTheme(this.currentTheme, false); // Apply without transition on init
    }

    /**
     * Load theme preference from localStorage
     */
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('theme-preference');
        if (savedTheme && this.themes.includes(savedTheme)) {
            this.currentTheme = savedTheme;
        } else {
            // Check system preference for dark mode
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.currentTheme = 'dark';
            }
        }
    }

    /**
     * Save theme preference to localStorage
     */
    saveThemePreference(theme) {
        localStorage.setItem('theme-preference', theme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme }
        }));
    }

    /**
     * Create the theme switcher UI component
     */
    createThemeSwitcher() {
        const themeSwitcherHTML = `
            <div class="theme-switcher" id="themeSwitcher" role="radiogroup" aria-label="Theme selector">
                <span class="theme-switcher-label">Theme:</span>
                <div class="theme-options">
                    ${this.themes.map(theme => `
                        <button 
                            class="theme-option ${theme === this.currentTheme ? 'active' : ''}" 
                            data-theme="${theme}"
                            role="radio"
                            aria-checked="${theme === this.currentTheme}"
                            aria-label="${this.getThemeLabel(theme)}"
                            title="${this.getThemeLabel(theme)}"
                        >
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        // Add to settings modal if it exists
        const settingsModal = document.querySelector('.modal-body');
        if (settingsModal) {
            const themeGroup = document.createElement('div');
            themeGroup.className = 'setting-group';
            themeGroup.innerHTML = `
                <label class="setting-label">Color Theme</label>
                <div class="setting-description">Choose your preferred color scheme</div>
                ${themeSwitcherHTML}
            `;
            settingsModal.insertBefore(themeGroup, settingsModal.firstChild);
        }

        // Also add to chat header for quick access
        const chatActions = document.querySelector('.chat-actions');
        if (chatActions) {
            const compactSwitcher = document.createElement('div');
            compactSwitcher.className = 'theme-switcher theme-switcher-compact';
            compactSwitcher.innerHTML = themeSwitcherHTML.replace('theme-switcher', 'theme-switcher-compact');
            chatActions.insertBefore(compactSwitcher, chatActions.firstChild);
        }
    }

    /**
     * Get human-readable theme label
     */
    getThemeLabel(theme) {
        const labels = {
            'white': 'White Theme - Light background with dark text',
            'gray': 'Gray Theme - Gray background with dark text', 
            'dark': 'Dark Theme - Dark background with light text'
        };
        return labels[theme] || theme;
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Theme option clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('theme-option')) {
                const theme = e.target.dataset.theme;
                this.switchTheme(theme);
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('theme-option')) {
                this.handleKeyboardNavigation(e);
            }
        });

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually selected a theme
                if (!localStorage.getItem('theme-preference')) {
                    this.switchTheme(e.matches ? 'dark' : 'white');
                }
            });
        }

        // Handle reduced motion preference
        if (window.matchMedia) {
            window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
                if (e.matches) {
                    document.documentElement.style.setProperty('--theme-transition', 'none');
                } else {
                    document.documentElement.style.setProperty('--theme-transition', 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)');
                }
            });
        }
    }

    /**
     * Handle keyboard navigation for accessibility
     */
    handleKeyboardNavigation(e) {
        const themeOptions = Array.from(document.querySelectorAll('.theme-option'));
        const currentIndex = themeOptions.indexOf(e.target);

        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                const prevIndex = currentIndex > 0 ? currentIndex - 1 : themeOptions.length - 1;
                themeOptions[prevIndex].focus();
                break;
            
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                const nextIndex = currentIndex < themeOptions.length - 1 ? currentIndex + 1 : 0;
                themeOptions[nextIndex].focus();
                break;
            
            case 'Enter':
            case ' ':
                e.preventDefault();
                const theme = e.target.dataset.theme;
                this.switchTheme(theme);
                break;
        }
    }

    /**
     * Switch to a new theme
     */
    switchTheme(newTheme) {
        if (!this.themes.includes(newTheme) || newTheme === this.currentTheme) {
            return;
        }

        // Add loading state
        this.setLoadingState(true);

        // Apply theme with transition
        this.applyTheme(newTheme, true);

        // Update current theme
        this.currentTheme = newTheme;

        // Save preference
        this.saveThemePreference(newTheme);

        // Update UI
        this.updateThemeButtons();

        // Remove loading state after transition
        setTimeout(() => {
            this.setLoadingState(false);
        }, this.transitionDuration);

        // Announce theme change for screen readers
        this.announceThemeChange(newTheme);
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme, withTransition = true) {
        // Create transition overlay for smooth switching
        if (withTransition) {
            this.createTransitionOverlay();
        }

        // Apply theme attribute
        document.documentElement.setAttribute('data-theme', theme);

        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);

        // Remove transition overlay
        if (withTransition) {
            setTimeout(() => {
                this.removeTransitionOverlay();
            }, this.transitionDuration / 2);
        }
    }

    /**
     * Create transition overlay for smooth theme switching
     */
    createTransitionOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'theme-transition-overlay';
        overlay.id = 'themeTransitionOverlay';
        document.body.appendChild(overlay);

        // Trigger animation
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });
    }

    /**
     * Remove transition overlay
     */
    removeTransitionOverlay() {
        const overlay = document.getElementById('themeTransitionOverlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.remove();
            }, this.transitionDuration);
        }
    }

    /**
     * Update meta theme-color for mobile browsers
     */
    updateMetaThemeColor(theme) {
        const colors = {
            'white': '#ffffff',
            'gray': '#808080',
            'dark': '#1a1a1a'
        };

        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        metaThemeColor.content = colors[theme];
    }

    /**
     * Update theme button states
     */
    updateThemeButtons() {
        document.querySelectorAll('.theme-option').forEach(button => {
            const isActive = button.dataset.theme === this.currentTheme;
            button.classList.toggle('active', isActive);
            button.setAttribute('aria-checked', isActive);
        });
    }

    /**
     * Set loading state during theme switching
     */
    setLoadingState(loading) {
        document.querySelectorAll('.theme-switcher').forEach(switcher => {
            switcher.classList.toggle('theme-switching', loading);
        });
    }

    /**
     * Announce theme change for screen readers
     */
    announceThemeChange(theme) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Theme changed to ${this.getThemeLabel(theme)}`;
        
        document.body.appendChild(announcement);
        
        // Remove announcement after it's been read
        setTimeout(() => {
            announcement.remove();
        }, 1000);
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Check if theme has good contrast ratios
     */
    validateContrast(theme) {
        const contrastRatios = {
            'white': { bg: '#ffffff', text: '#000000', ratio: 21 },
            'gray': { bg: '#808080', text: '#000000', ratio: 4.6 },
            'dark': { bg: '#1a1a1a', text: '#ffffff', ratio: 15.8 }
        };

        const themeData = contrastRatios[theme];
        return themeData && themeData.ratio >= 4.5; // WCAG AA standard
    }

    /**
     * Get theme accessibility info
     */
    getThemeAccessibilityInfo(theme) {
        const info = {
            'white': {
                name: 'White Theme',
                description: 'High contrast with dark text on white background',
                contrastRatio: '21:1',
                wcagLevel: 'AAA'
            },
            'gray': {
                name: 'Gray Theme', 
                description: 'Medium contrast with dark text on gray background',
                contrastRatio: '4.6:1',
                wcagLevel: 'AA'
            },
            'dark': {
                name: 'Dark Theme',
                description: 'High contrast with light text on dark background',
                contrastRatio: '15.8:1', 
                wcagLevel: 'AAA'
            }
        };

        return info[theme] || null;
    }

    /**
     * Export theme settings
     */
    exportSettings() {
        return {
            currentTheme: this.currentTheme,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        };
    }

    /**
     * Import theme settings
     */
    importSettings(settings) {
        if (settings && settings.currentTheme && this.themes.includes(settings.currentTheme)) {
            this.switchTheme(settings.currentTheme);
            return true;
        }
        return false;
    }
}

// Screen reader only class for accessibility announcements
const srOnlyCSS = `
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
`;

// Add screen reader styles
const style = document.createElement('style');
style.textContent = srOnlyCSS;
document.head.appendChild(style);

// Initialize theme switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeSwitcher = new ThemeSwitcher();
    
    // Make it globally accessible
    window.switchTheme = (theme) => window.themeSwitcher.switchTheme(theme);
    window.getCurrentTheme = () => window.themeSwitcher.getCurrentTheme();
    window.getThemeAccessibilityInfo = (theme) => window.themeSwitcher.getThemeAccessibilityInfo(theme);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}