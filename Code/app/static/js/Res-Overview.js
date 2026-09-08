document.addEventListener('DOMContentLoaded', () => {
    // Select all restaurant cards
    const cards = document.querySelectorAll('.restaurant-card');
    
    // Function to add the fade-in class with a delay
    const fadeIn = (element, delay) => {
      setTimeout(() => {
        element.classList.add('fade-in');
      }, delay);
    };
    
    // Iterate over each card and apply the animation with incremental delays
    cards.forEach((card, index) => {
      fadeIn(card, index * 150); // 150ms delay for each card
    });
  });
  