// static/js/script.js

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

    // DOM Element Selections
    const companySelect = document.getElementById('company');
    const modelSelect = document.getElementById('car_models');
    const form = document.querySelector('.prediction-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const yearInput = document.getElementById('year');
    const kiloInput = document.getElementById('kilo_driven');
    const allSelects = form.querySelectorAll('select');
    const allInputs = form.querySelectorAll('input[type="number"]');

    // --- Dynamic Car Model Loading ---
    companySelect.addEventListener('change', async function() {
        const company = this.value;
        modelSelect.innerHTML = '<option value="">Loading Models...</option>';
        modelSelect.disabled = true;
        modelSelect.classList.remove('invalid');

        if (company) {
            try {
                const fetchURL = `/get_models/${encodeURIComponent(company)}`;
                const response = await fetch(fetchURL);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                modelSelect.innerHTML = '<option value="">Select Model</option>';
                if (data && data.length > 0) {
                    data.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                    modelSelect.disabled = false;
                } else {
                    modelSelect.innerHTML = '<option value="">No models found</option>';
                }
            } catch (error) {
                console.error('Error fetching car models:', error);
                modelSelect.innerHTML = '<option value="">Error loading models</option>';
            }
        } else {
            modelSelect.innerHTML = '<option value="">Select Brand First</option>';
            modelSelect.disabled = true;
        }
        validateInputStyle(companySelect, company !== '');
    });

    // --- Form Submission and Loading Overlay ---
    form.addEventListener('submit', function(event) {
        let formIsValid = true;

        form.querySelectorAll('[required]').forEach(input => {
            if (input.id === 'car_models' && input.disabled) {
               formIsValid = false;
               if(companySelect.value === ''){
                   validateInputStyle(companySelect, false);
               } else {
                   validateInputStyle(input, false);
               }
            } else if (!input.value) {
                formIsValid = false;
                validateInputStyle(input, false);
                console.log(`Input required: ${input.name || input.id}`);
            } else {
                 validateInputStyle(input, true);
            }
        });

        if (!validateNumberInput(yearInput)) formIsValid = false;
        if (!validateNumberInput(kiloInput)) formIsValid = false;

        if (formIsValid) {
            loadingOverlay.classList.remove('hidden');
        } else {
            event.preventDefault();
            console.log("Form submission prevented due to validation errors.");
            const firstInvalid = form.querySelector('.invalid');
            if (firstInvalid) {
                firstInvalid.focus();
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });

    // --- Input Validation Styling Feedback ---
     yearInput.addEventListener('input', function() { validateNumberInput(this); });
     kiloInput.addEventListener('input', function() { validateNumberInput(this); });

    allSelects.forEach(select => {
        select.addEventListener('change', function() {
             if (select.id !== 'company'){
                 validateInputStyle(this, this.value !== '');
             }
        });
         validateInputStyle(select, select.value !== '');
    });

    validateNumberInput(yearInput);
    validateNumberInput(kiloInput);

     function validateNumberInput(inputElement) {
        const value = inputElement.value;
        if (!inputElement.hasAttribute('required') && value === '') {
            inputElement.classList.remove('invalid');
            return true;
        }
         if (inputElement.hasAttribute('required') && value === '') {
            inputElement.classList.add('invalid');
            return false;
        }

        const numValue = parseInt(value);
        const min = inputElement.hasAttribute('min') ? parseInt(inputElement.min) : -Infinity;
        const max = inputElement.hasAttribute('max') ? parseInt(inputElement.max) : Infinity;

        if (isNaN(numValue) || numValue < min || numValue > max) {
            inputElement.classList.add('invalid');
             return false;
        } else {
            inputElement.classList.remove('invalid');
            return true;
        }
    }

    function validateInputStyle(inputElement, isValid) {
        if (inputElement.hasAttribute('required') && !inputElement.value && !inputElement.disabled) { // Add check for disabled
            inputElement.classList.add('invalid');
        } else if (isValid) {
            inputElement.classList.remove('invalid');
        } else {
            if ((inputElement.value !== '' || inputElement.hasAttribute('required')) && !inputElement.disabled) { // Add check for disabled
               inputElement.classList.add('invalid');
            } else {
               inputElement.classList.remove('invalid');
            }
        }
    }

    // --- Smooth Scroll for Navigation Links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');

            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    // Calculate offset for fixed navbar
                    const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - navbarHeight - 20; // Added extra 20px buffer

                    window.scrollTo({
                         top: offsetPosition,
                         behavior: "smooth"
                    });

                    // Update active class in navbar
                    document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));
                     if (this.closest('.nav-links')) {
                        this.classList.add('active');
                     } else { // Try to find matching nav link if clicked elsewhere
                         const matchingNavLink = document.querySelector(`.nav-links a[href="${targetId}"]`);
                         if(matchingNavLink) matchingNavLink.classList.add('active');
                     }
                }
            }
            else if (targetId === '#') {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth'});
                document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));
                 const homeLink = document.querySelector('.nav-links a[href="#"]');
                 if(homeLink) homeLink.classList.add('active');
            }
        });
    });

    // Set initial active state based on hash or default to Home
    const updateActiveNav = () => {
        const currentHash = window.location.hash;
        let activeLinkFound = false;
        document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));

        if (currentHash && currentHash !== '#') {
            const activeLink = document.querySelector(`.nav-links a[href="${currentHash}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
                activeLinkFound = true;
            }
        }
        if (!activeLinkFound) {
             const homeLink = document.querySelector('.nav-links a[href="#"]');
             if(homeLink) homeLink.classList.add('active');
        }
    };
    updateActiveNav(); // Run on load
    window.addEventListener('hashchange', updateActiveNav); // Run on hash change

     // If there's a prediction result on page load, scroll to it smoothly
     const predictionElement = document.querySelector('.prediction');
     if (predictionElement) {
         const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
         const elementPosition = predictionElement.getBoundingClientRect().top;
         const offsetPosition = elementPosition + window.pageYOffset - navbarHeight - 20; // Added extra 20px buffer

         // Use timeout to allow page rendering before scrolling
         setTimeout(() => {
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
         }, 100); // Small delay
     }

}); // End DOMContentLoaded