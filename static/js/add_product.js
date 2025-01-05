function addSpec() {
    const container = document.getElementById('specsContainer');
    const specItem = document.createElement('div');
    specItem.className = 'spec-item';
    specItem.innerHTML = `
        <input type="text" name="spec" placeholder="Ex: GPS Integrado" required>
        <button type="button" class="remove-spec" onclick="removeSpec(this)">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(specItem);
}

function removeSpec(button) {
    const container = document.getElementById('specsContainer');
    if (container.children.length > 1) {
        button.parentElement.remove();
    }
}

function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const previewImg = preview.querySelector('img');

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.style.display = 'none';
    }
}