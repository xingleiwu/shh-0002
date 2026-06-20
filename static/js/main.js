function confirmDelete(message) {
    return confirm(message || '确定要删除吗？此操作不可恢复。');
}

function confirmAction(message) {
    return confirm(message || '确定执行此操作吗？');
}

document.addEventListener('DOMContentLoaded', function() {
    var deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var message = form.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    var tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function(tooltip) {
        new bootstrap.Tooltip(tooltip);
    });

    var autoDismissAlerts = document.querySelectorAll('.alert-auto-dismiss');
    autoDismissAlerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 3000);
    });

    var filterResetBtns = document.querySelectorAll('.btn-filter-reset');
    filterResetBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var form = btn.closest('form');
            if (form) {
                var inputs = form.querySelectorAll('input, select');
                inputs.forEach(function(input) {
                    if (input.type !== 'hidden') {
                        input.value = '';
                    }
                });
                form.submit();
            }
        });
    });
});

function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    var date = new Date(dateStr);
    var year = date.getFullYear();
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    return year + '-' + month + '-' + day;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    var date = new Date(dateStr);
    var year = date.getFullYear();
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    var hours = String(date.getHours()).padStart(2, '0');
    var minutes = String(date.getMinutes()).padStart(2, '0');
    return year + '-' + month + '-' + day + ' ' + hours + ':' + minutes;
}
