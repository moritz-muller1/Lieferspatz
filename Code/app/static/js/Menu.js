
document.addEventListener('DOMContentLoaded', () => {
    const menuItems = document.querySelectorAll('.menu-item');
  
    menuItems.forEach((item, index) => {
      // Give each menu item a slight delay based on its position in the list
      setTimeout(() => {
        item.style.opacity = 1;
        item.style.transform = 'translateY(0)';
      }, 100 * index);
    });
  });
  