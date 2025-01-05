let currentTab = 'produtos'; // Aba inicial padrão

// Exibir aba selecionada
function showTab(tab) {
    currentTab = tab;

    // Atualizar botões ativos
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.tab-button[onclick="showTab('${tab}')"]`).classList.add('active');

    // Atualizar conteúdo visível
    document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');
    document.getElementById(`${tab}-content`).style.display = 'block';

    // Atualizar o valor da aba no formulário, se necessário
    document.querySelectorAll('input[name="current_tab"]').forEach(input => input.value = tab);
}

// Abrir modal de edição
function editarItem(tipo, id) {
    const modal = tipo === 'produto' ? 'modalEdicaoProduto' : 'modalEdicaoServico';
    const formId = tipo === 'produto' ? 'formEdicaoProduto' : 'formEdicaoServico';
    const listId = tipo === 'produto' ? 'specs-list' : 'features-list';

    // Limpar campos dinâmicos
    document.getElementById(listId).innerHTML = '';

    // Buscar dados do item
    fetch(`/admin/${tipo}s/${id}`)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar dados do item.');
            return response.json();
        })
        .then(data => {
            if (tipo === 'produto') {
                preencherCamposProduto(data);
            } else {
                preencherCamposServico(data);
            }

            // Configurar ação do formulário
            document.getElementById(formId).action = `/admin/${tipo}s/editar/${id}`;
            document.getElementById(modal).style.display = 'block';
        })
        .catch(error => {
            console.error(error);
            alert('Erro ao carregar os dados. Tente novamente.');
        });
}

// Preencher campos de produtos
function preencherCamposProduto(data) {
    document.getElementById('nomeProduto').value = data.name || '';
    document.getElementById('descricaoProduto').value = data.description || '';
    document.getElementById('categoriaProduto').value = data.category || 'DMR';

    if (data.specs) {
        const specs = Array.isArray(data.specs) ? data.specs : JSON.parse(data.specs);
        specs.forEach(spec => adicionarSpec(spec));
    }
}

// Preencher campos de serviços
function preencherCamposServico(data) {
    document.getElementById('nomeServico').value = data.name || '';
    document.getElementById('descricaoServico').value = data.description || '';
    document.getElementById('categoriaServico').value = data.category || 'locacao';

    if (data.features) {
        const features = Array.isArray(data.features) ? data.features : JSON.parse(data.features);
        features.forEach(feature => adicionarFeature(feature));
    }
}

// Adicionar especificação para produtos
function adicionarSpec(valor = '') {
    const container = document.getElementById('specs-list');
    const div = document.createElement('div');
    div.style.marginBottom = '10px';
    div.innerHTML = `
        <input type="text" name="specs[]" value="${valor}" class="form-control" required placeholder="Especificação">
        <button type="button" class="button button-danger" onclick="this.parentElement.remove()">Excluir</button>
    `;
    container.appendChild(div);
}

// Adicionar característica para serviços
function adicionarFeature(valor = '') {
    const container = document.getElementById('features-list');
    const div = document.createElement('div');
    div.style.marginBottom = '10px';
    div.innerHTML = `
        <input type="text" name="features[]" value="${valor}" class="form-control" required placeholder="Característica">
        <button type="button" class="button button-danger" onclick="this.parentElement.remove()">Excluir</button>
    `;
    container.appendChild(div);
}

// Fechar modais
function fecharModalProduto() {
    document.getElementById('modalEdicaoProduto').style.display = 'none';
    document.getElementById('formEdicaoProduto').reset();
    document.getElementById('specs-list').innerHTML = '';
}

function fecharModalServico() {
    document.getElementById('modalEdicaoServico').style.display = 'none';
    document.getElementById('formEdicaoServico').reset();
    document.getElementById('features-list').innerHTML = '';
}

// Fechar modal ao clicar fora
window.onclick = function (event) {
    if (event.target.id === 'modalEdicaoProduto') fecharModalProduto();
    if (event.target.id === 'modalEdicaoServico') fecharModalServico();
};

// Inicializar página
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab') || 'produtos'; // Pegar a aba da URL ou usar 'produtos'
    showTab(tab);
};
