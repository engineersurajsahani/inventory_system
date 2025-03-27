// Initialize all Materialize components
document.addEventListener('DOMContentLoaded', function() {
    // Auto-init all Materialize components
    M.AutoInit();
    
    // Initialize floating action button
    var elems = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init(elems);
    
    // Initialize tooltips
    var tooltipElems = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(tooltipElems);
    
    // Initialize modals
    var modalElems = document.querySelectorAll('.modal');
    M.Modal.init(modalElems);
});

// Toast notifications
function showToast(message, classes = '') {
    M.toast({html: message, classes: classes});
}

// Confirm before delete
function confirmDelete(event, message = 'Are you sure you want to delete this item?') {
    if (!confirm(message)) {
        event.preventDefault();
    }
}