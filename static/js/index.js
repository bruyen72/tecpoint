async function sendContactEmail(event) {
    event.preventDefault();

    // Elementos do botão
    const button = document.getElementById('submitButton');
    const buttonText = button.querySelector('.button-text');
    const buttonLoading = button.querySelector('.button-loading');

    // Validação básica
    const name = document.getElementById('contact_name').value.trim();
    const email = document.getElementById('contact_email').value.trim();
    const message = document.getElementById('contact_message').value.trim();

    if (!name || !email || !message) {
        alert('Por favor, preencha todos os campos obrigatórios');
        return false;
    }

    // Preparar dados
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('phone', document.getElementById('contact_phone').value);
    formData.append('message', message);

    try {
        // Desabilitar botão e mostrar loading
        button.disabled = true;
        buttonText.style.display = 'none';
        buttonLoading.style.display = 'inline-block';

        // Enviar email
        const response = await fetch('/enviar-contato-site', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            alert('Mensagem enviada com sucesso! Em breve entraremos em contato.');
            document.getElementById('contactForm').reset();
        } else {
            throw new Error(data.error || 'Erro ao enviar mensagem');
        }

    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao enviar mensagem. Por favor, tente novamente.');
    } finally {
        // Restaurar botão
        button.disabled = false;
        buttonText.style.display = 'inline-block';
        buttonLoading.style.display = 'none';
    }

    return false;
}

// Máscara para telefone
document.getElementById('contact_phone').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length <= 11) {
        value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
        value = value.replace(/(\d)(\d{4})$/, '$1-$2');
    }
    e.target.value = value;
});

        // Menu Toggle
        const mobileToggle = document.querySelector('.mobile-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // Smooth Scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    if (navMenu.classList.contains('active')) {
                        navMenu.classList.remove('active');
                    }
                }
            });
        });

        // Animation on Scroll
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate');
                    }
                });
            }, { threshold: 0.1 }
        );

        document.querySelectorAll('.product-card, .contact-form, .footer-section')
            .forEach(el => observer.observe(el));
        document.querySelectorAll('.radio-container img').forEach(img => {
            img.addEventListener('click', (event) => {
                event.preventDefault(); // cancela o comportamento padrão
            });
        });

        // Atualiza o feed do Instagram a cada 5 minutos
        setInterval(() => {
            const instagramIframe = document.querySelector('.instagram-feed iframe');
            if (instagramIframe) {
                instagramIframe.src = instagramIframe.src;
            }
        }, 300000);

        // Script para manipular o placeholder de carregamento do Instagram
        document.addEventListener("DOMContentLoaded", function () {
            const script = document.querySelector('script[src="//www.instagram.com/embed.js"]');
            const placeholder = document.querySelector('.loading-placeholder');
            const instagramMedia = document.querySelector('.instagram-media');

            script.onload = function () {
                if (placeholder) {
                    placeholder.style.display = 'none';
                    if (instagramMedia) {
                        instagramMedia.style.display = 'block';
                    }
                }
            };

            script.onerror = function () {
                if (placeholder) {
                    placeholder.innerHTML = '<p>Não foi possível carregar o feed do Instagram. Tente novamente mais tarde.</p>';
                }
            };
        });