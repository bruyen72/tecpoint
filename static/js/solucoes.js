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
    },
    { threshold: 0.1 }
);

document.querySelectorAll('.solucao-card')
    .forEach(el => observer.observe(el));
document.addEventListener('DOMContentLoaded', function () {
    // Seleciona o formulário de contato
    const formularioContato = document.getElementById('formularioContato');

    if (formularioContato) {
        formularioContato.addEventListener('submit', async function (event) {
            event.preventDefault();

            // Coleta os dados do formulário
            const dados = {
                nome: document.getElementById('nomeContato').value.trim(),
                email: document.getElementById('emailContato').value.trim(),
                telefone: document.getElementById('telefoneContato').value.trim(),
                categoria: document.getElementById('servicoCategoria').value.trim(),
                mensagem: document.getElementById('mensagemContato').value.trim()
            };

            // Valida os campos obrigatórios no frontend
            if (!dados.nome || !dados.email || !dados.mensagem) {
                alert('Os campos Nome, Email e Mensagem são obrigatórios.');
                return;
            }

            // Botão de envio: desativa e mostra o estado de carregamento
            const botaoEnviar = formularioContato.querySelector('button[type="submit"]');
            const textoOriginalBotao = botaoEnviar.innerHTML;
            botaoEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
            botaoEnviar.disabled = true;

            try {
                // Envia os dados para o backend
                const response = await fetch('/enviar-serviço', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(dados)
                });

                // Processa a resposta
                if (!response.ok) {
                    const errorData = await response.json().catch(() => null);
                    const errorMessage = errorData?.error || 'Erro desconhecido no envio do formulário';
                    throw new Error(errorMessage);
                }

                const resultado = await response.json();
                alert(resultado.message || 'Mensagem enviada com sucesso!');
                formularioContato.reset();
                fecharModalContato();
            } catch (erro) {
                console.error('Erro:', erro);
                alert(`Erro ao enviar mensagem: ${erro.message}. Por favor, tente novamente.`);
            } finally {
                // Restaura o botão ao estado original
                botaoEnviar.innerHTML = textoOriginalBotao;
                botaoEnviar.disabled = false;
            }
        });
    }

    // Função para abrir o modal e preencher a categoria automaticamente
    window.abrirModalContato = function (categoria) {
        const modalContato = document.getElementById('modalContato');
        const categoriaInput = document.getElementById('servicoCategoria');
        if (categoriaInput) categoriaInput.value = categoria; // Define a categoria no campo oculto
        modalContato.style.display = 'block';
    };

    // Função para fechar o modal
    window.fecharModalContato = function () {
        const modalContato = document.getElementById('modalContato');
        if (modalContato) modalContato.style.display = 'none';
    };

    // Fecha o modal ao clicar fora dele
    window.addEventListener('click', function (event) {
        const modalContato = document.getElementById('modalContato');
        if (event.target === modalContato) {
            fecharModalContato();
        }
    });
});