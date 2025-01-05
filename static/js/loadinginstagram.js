class InstagramFeed {
    constructor() {
        // Elementos principais
        this.container = document.querySelector('.instagram-container');
        this.placeholder = document.getElementById('loadingPlaceholder');
        this.content = document.getElementById('instagramContent');
        this.initialized = false;
    }

    init() {
        if (this.initialized || !this.container) return;
        this.initialized = true;
        
        // Inicia o carregamento
        this.loadInstagramScript();
    }

    loadInstagramScript() {
        const script = document.createElement('script');
        script.src = 'https://www.instagram.com/embed.js';
        script.async = true;
        
        script.onload = () => this.handleScriptLoad();
        script.onerror = () => this.handleError();
        
        document.body.appendChild(script);
    }

    handleScriptLoad() {
        if (!window.instgrm) {
            this.handleError();
            return;
        }

        window.instgrm.Embeds.process();
        this.checkEmbedLoad();
    }

    checkEmbedLoad() {
        let attempts = 0;
        const maxAttempts = 20;
        
        const checkInterval = setInterval(() => {
            attempts++;
            const embedElement = document.querySelector('.instagram-media-rendered');
            
            if (embedElement) {
                clearInterval(checkInterval);
                this.showContent();
            } else if (attempts >= maxAttempts) {
                clearInterval(checkInterval);
                this.handleError();
            }
        }, 1000);
    }

    showContent() {
        if (!this.content || !this.placeholder) return;

        // Fade out placeholder
        this.placeholder.style.opacity = '0';
        
        // Show content with fade
        setTimeout(() => {
            this.content.classList.add('loaded');
            
            // Remove placeholder after transition
            setTimeout(() => {
                this.placeholder.remove();
            }, 300);
        }, 300);
    }

    handleError() {
        if (!this.container) return;

        // Remove placeholder if exists
        if (this.placeholder) {
            this.placeholder.remove();
        }

        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'instagram-error';
        errorDiv.innerHTML = `
            <p>Não foi possível carregar o feed do Instagram</p>
            <a href="https://www.instagram.com/tecpointmt/" 
               target="_blank" 
               rel="noopener noreferrer">
                Ver no Instagram
            </a>
        `;

        this.container.appendChild(errorDiv);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const feed = new InstagramFeed();
    feed.init();
});