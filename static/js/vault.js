/* Vault Interaction JS Module */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('vaultSearchInput');
    const categorySelect = document.getElementById('vaultCategorySelect');

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(filterVaultItems, 200);
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            const selectedCat = categorySelect.value;
            const currentUrl = new URL(window.location.href);
            if (selectedCat) {
                currentUrl.searchParams.set('category', selectedCat);
            } else {
                currentUrl.searchParams.delete('category');
            }
            window.location.href = currentUrl.toString();
        });
    }
});

function filterVaultItems() {
    const searchInput = document.getElementById('vaultSearchInput');
    if (!searchInput) return;
    const query = searchInput.value.toLowerCase().trim();
    const rows = document.querySelectorAll('.vault-item-row');

    rows.forEach(row => {
        const textContent = row.textContent.toLowerCase();
        if (textContent.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Fetch decrypted password via API and reveal in element
 */
async function revealVaultPassword(credId, btnElem, targetElemId) {
    const targetElem = document.getElementById(targetElemId);
    if (!targetElem) return;

    const icon = btnElem.querySelector('i');

    if (targetElem.dataset.revealed === 'true') {
        // Hide password
        targetElem.textContent = '••••••••••••';
        targetElem.dataset.revealed = 'false';
        if (icon) {
            icon.className = 'fas fa-eye';
        }
        return;
    }

    try {
        btnElem.disabled = true;
        const response = await fetch(`/vault/decrypt/${credId}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await response.json();

        if (data.status === 'success') {
            targetElem.textContent = data.password;
            targetElem.dataset.revealed = 'true';
            if (icon) {
                icon.className = 'fas fa-eye-slash';
            }

            // Auto mask password after 10 seconds
            setTimeout(() => {
                if (targetElem.dataset.revealed === 'true') {
                    targetElem.textContent = '••••••••••••';
                    targetElem.dataset.revealed = 'false';
                    if (icon) {
                        icon.className = 'fas fa-eye';
                    }
                }
            }, 10000);
        } else {
            showToast('Failed to decrypt password', 'danger');
        }
    } catch (err) {
        showToast('Error communicating with server', 'danger');
    } finally {
        btnElem.disabled = false;
    }
}

/**
 * Fetch decrypted password and copy to clipboard
 */
async function copyVaultPassword(credId) {
    try {
        const response = await fetch(`/vault/decrypt/${credId}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await response.json();

        if (data.status === 'success') {
            copyToClipboard(data.password, "Password copied to clipboard!");
        } else {
            showToast('Failed to decrypt password for copy', 'danger');
        }
    } catch (err) {
        showToast('Error communicating with server', 'danger');
    }
}
