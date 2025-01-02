
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.filtro-btn');

    // Ação ao clicar nos botões de filtro
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove a classe 'active' de todos os botões
            buttons.forEach(btn => btn.classList.remove('active'));
            // Adiciona a classe 'active' ao botão clicado
            button.classList.add('active');

            // Pega a categoria do botão clicado
            const category = button.getAttribute('data-category');

            // Recarrega a página com o filtro aplicado
            // Substitua por sua lógica de renderização ou AJAX se necessário
            window.location.href = `?category=${category}`;
        });
    });

    // Código adicional do menu mobile
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

    document.querySelectorAll('.produto-card, .contact-form, .footer-section')
        .forEach(el => observer.observe(el));
});
