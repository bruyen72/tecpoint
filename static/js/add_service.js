function addFeature() {
    const container = document.getElementById('features-container');
    const featureDiv = document.createElement('div');
    featureDiv.className = 'feature-item';
    featureDiv.innerHTML = `
        <input type="text" name="features[]" class="form-control" 
               placeholder="Digite uma característica importante do serviço" required>
        <button type="button" class="button button-danger" onclick="this.parentElement.remove()">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(featureDiv);
}