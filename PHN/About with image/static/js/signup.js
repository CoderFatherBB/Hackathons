// signup.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('signupForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const strengthIndicator = document.querySelector('.password-strength');

    // Password strength checker
    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
        if (password.match(/\d/)) strength++;
        if (password.match(/[^a-zA-Z\d]/)) strength++;
        
        return strength;
    }

    passwordInput.addEventListener('input', function(e) {
        const strength = checkPasswordStrength(e.target.value);
        strengthIndicator.className = 'password-strength';
        
        if (strength >= 4) {
            strengthIndicator.classList.add('strong');
        } else if (strength >= 2) {
            strengthIndicator.classList.add('medium');
        } else if (strength >= 1) {
            strengthIndicator.classList.add('weak');
        }
    });

    // Form validation
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        let isValid = true;

        // Clear previous errors
        document.querySelectorAll('.input-group').forEach(group => {
            group.classList.remove('error');
        });

        // Validate password match
        if (passwordInput.value !== confirmPasswordInput.value) {
            confirmPasswordInput.parentElement.classList.add('error');
            confirmPasswordInput.parentElement.setAttribute('data-error', 'Passwords do not match');
            isValid = false;
        }

        // Validate password strength
        if (checkPasswordStrength(passwordInput.value) < 3) {
            passwordInput.parentElement.classList.add('error');
            passwordInput.parentElement.setAttribute('data-error', 'Password is not strong enough');
            isValid = false;
        }

        // Validate email format
        const email = document.getElementById('email').value;
        if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            document.getElementById('email').parentElement.classList.add('error');
            document.getElementById('email').parentElement.setAttribute('data-error', 'Invalid email format');
            isValid = false;
        }

        if (isValid) {
            // Here you would typically send the form data to your server
            console.log('Form is valid, ready to submit');
            alert('Account created successfully!'); // Replace with actual form submission
        }
    });
});