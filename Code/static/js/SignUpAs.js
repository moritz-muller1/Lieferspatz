
// Function to add the 'show' class to elements with the 'fade-element' class
function fadeInElements() {
    const elements = document.querySelectorAll('.fade-element');
    let delay = 0;
    
    elements.forEach(element => {
      setTimeout(() => {
        element.classList.add('show');
      }, delay);
      delay += 250; // Delay in milliseconds
    });
  }
  
  // Event listener for DOMContentLoaded to start animations after the DOM is ready
  document.addEventListener('DOMContentLoaded', fadeInElements);
  