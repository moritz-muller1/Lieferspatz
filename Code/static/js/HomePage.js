
document.addEventListener('DOMContentLoaded', (event) => {
    // Get all elements with the 'fade-in' class
    const fadeElements = document.querySelectorAll('.fade-in');
  
    // Set a delay factor to stagger the fade-ins
    let delay = 0;
    fadeElements.forEach(element => {
      // Apply the delay based on the order of the elements
      element.style.animationDelay = `${delay}s`;
      delay += 0.5; // Increment the delay for the next element
  
      // Remove the 'fade-in' class after the animation completes
      element.addEventListener('animationend', () => {
        element.classList.remove('fade-in');
      });
    });
  });
  