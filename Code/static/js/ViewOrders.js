document.addEventListener('DOMContentLoaded', function() {
    const orderCards = document.querySelectorAll('.order-card');
    let delay = 0;

    orderCards.forEach(card => {
        setTimeout(() => {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, delay);
        delay += 100; // Increase delay for each card to create a staggered effect
    });
});
