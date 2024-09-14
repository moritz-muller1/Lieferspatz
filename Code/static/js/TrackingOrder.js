

document.addEventListener('DOMContentLoaded', function() {
    // Determine the status of the order to set the width of the status bar
    var statusFill = document.getElementById('statusFill');
    var orderStatus = statusFill.classList.contains('pending') ? 25 :
                      statusFill.classList.contains('processing') ? 50 :
                      statusFill.classList.contains('delivered') ? 100 : 0;

    // Animate the status bar fill
    setTimeout(function() {
        statusFill.style.width = orderStatus + '%';
    }, 500); // Start the animation 500ms after the page loads
});
