// Main JavaScript for Mauricio PDQ ERP System

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Confirmation for delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Dynamic calculation for financial forms
    const calculateForms = document.querySelectorAll('.auto-calculate');
    calculateForms.forEach(form => {
        const inputs = form.querySelectorAll('input[type="number"]');
        const totalField = form.querySelector('.total-amount');
        
        if (inputs.length && totalField) {
            inputs.forEach(input => {
                input.addEventListener('input', updateTotal);
            });
            
            function updateTotal() {
                let total = 0;
                inputs.forEach(input => {
                    total += parseFloat(input.value || 0);
                });
                totalField.textContent = total.toFixed(2);
            }
        }
    });

    // Date picker initialization
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(picker => {
        picker.addEventListener('focus', function() {
            this.type = 'date';
        });
        picker.addEventListener('blur', function() {
            if (!this.value) {
                this.type = 'text';
            }
        });
    });
});
