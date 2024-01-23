document.addEventListener("DOMContentLoaded", function() {
    const modules = document.querySelectorAll('.module');
    const contents = document.querySelectorAll('.module-content');

    modules.forEach((module, index) => {
      module.addEventListener('click', function() {
        // Remove 'current' class from all modules and hide all contents
        modules.forEach(m => m.classList.remove('current'));
        contents.forEach(c => c.classList.remove('active'));

        // Add 'current' class to the clicked module and show the corresponding content
        module.classList.add('current');
        contents[index].classList.add('active');
      });
    });
  });