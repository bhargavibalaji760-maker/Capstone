/**
 * MediTrial AI - Shared UI Components
 * Centralized layout management using native Web Components.
 */

// 1. Clinical Loader Component
class ClinicalLoader extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <div class="page-loader" id="pageLoader">
                <div class="loader-logo">
                    <i class="fas fa-certificate text-accent"></i>
                </div>
            </div>
        `;
    }
}

// 2. Clinical Sidebar Component
class ClinicalSidebar extends HTMLElement {
    connectedCallback() {
        const activePage = this.getAttribute('active') || '';
        
        this.innerHTML = `
            <aside class="sidebar">
                <div class="sidebar-logo">
                    <i class="fas fa-certificate text-accent"></i>
                    <span>MediTrial <span class="text-accent">AI</span></span>
                </div>
                <nav class="sidebar-nav">
                    <a href="/home" class="${activePage === 'home' ? 'active' : ''}"><i class="fas fa-home"></i> Home</a>
                    <a href="/dashboard" class="${activePage === 'dashboard' ? 'active' : ''}"><i class="fas fa-chart-line"></i> Dashboard</a>
                    <a href="/patients" class="${activePage === 'patients' ? 'active' : ''}"><i class="fas fa-user-injured"></i> Patients</a>
                    <a href="/trials" class="${activePage === 'trials' ? 'active' : ''}"><i class="fas fa-flask"></i> Trials</a>
                    <a href="/matches" class="${activePage === 'matches' ? 'active' : ''}"><i class="fas fa-link"></i> Clinical Matching</a>
                    <a href="/profile" class="${activePage === 'profile' ? 'active' : ''}"><i class="fas fa-user-circle"></i> Profile</a>
                </nav>
                <div class="sidebar-footer">
                    <div class="status-indicator px-2 mb-3">
                        <div class="ai-pulse"></div>
                        <span id="globalAiStatus" class="text-emerald small fw-bold">System Ready</span>
                    </div>
                    <a href="#" id="logoutBtn" class="text-secondary d-flex align-items-center gap-2 text-decoration-none">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </aside>
        `;

        // Attach logout logic after render
        const logoutBtn = this.querySelector('#logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (typeof api !== 'undefined' && api.logout) {
                    api.logout();
                } else {
                    localStorage.removeItem('access_token');
                    window.location.replace('/login');
                }
            });
        }
    }
}

// 3. Clinical Footer Component
class ClinicalFooter extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <footer class="footer">
                <div class="container text-center">
                    <p class="mb-0">© 2026 MediTrial AI. Clinical Intelligence Accelerated.</p>
                </div>
            </footer>
        `;
    }
}

// Register Components
if (!customElements.get('clinical-loader')) customElements.define('clinical-loader', ClinicalLoader);
if (!customElements.get('clinical-sidebar')) customElements.define('clinical-sidebar', ClinicalSidebar);
if (!customElements.get('clinical-footer')) customElements.define('clinical-footer', ClinicalFooter);
