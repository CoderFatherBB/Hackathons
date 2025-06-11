// mobile-enhancements.js
document.addEventListener('DOMContentLoaded', function() {
    // Prevent zoom on input focus for iOS
    const metaViewport = document.querySelector('meta[name=viewport]');
    metaViewport.content = 'width=device-width, initial-scale=1, maximum-scale=1';

    // Handle mobile keyboard appearance
    const inputs = document.querySelectorAll('input');
    const form = document.querySelector('form');
    let viewportHeight = window.innerHeight;

    // Adjust layout when mobile keyboard appears
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            if (window.innerWidth <= 768) {
                window.scrollTo(0, 0);
                document.body.scrollTop = 0;
                setTimeout(() => {
                    const inputRect = input.getBoundingClientRect();
                    if (inputRect.bottom > viewportHeight) {
                        window.scrollTo(0, inputRect.top - 20);
                    }
                }, 300);
            }
        });
    });

    // Handle form submission on mobile
    form.addEventListener('submit', function(e) {
        if (window.innerWidth <= 768) {
            inputs.forEach(input => input.blur()); // Hide keyboard
        }
    });

    // Improve touch response
    document.addEventListener('touchstart', function() {}, {passive: true});
});