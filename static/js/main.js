// PrediQ Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm before leaving pages with unsaved forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        let formChanged = false;
        form.addEventListener('change', () => {
            formChanged = true;
        });
        form.addEventListener('submit', () => {
            formChanged = false;
        });
        window.addEventListener('beforeunload', (e) => {
            if (formChanged) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    });
});

// Utility function to show loading state
function showLoading(button) {
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
}

// Utility function to hide loading state
function hideLoading(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}