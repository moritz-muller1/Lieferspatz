// OrderDetails.js
document.addEventListener('DOMContentLoaded', () => {
    let delay = 0;
    document.querySelectorAll('.fade-in').forEach(element => {
        setTimeout(() => element.classList.add('visible'), delay);
        delay += 500; // Increment delay for a cascading effect
    });
});
