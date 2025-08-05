document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS for animations
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true
        });
    }

    // Update year in footer
    const yearEl = document.getElementById('current-year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    // Initialize Particles.js if element exists
    if (typeof particlesJS !== 'undefined' && document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            "particles": {
                "number": {
                    "value": 80,
                    "density": {
                        "enable": true,
                        "value_area": 800
                    }
                },
                "color": {
                    "value": "#8a2be2"
                },
                "shape": {
                    "type": "circle",
                    "stroke": {
                        "width": 0,
                        "color": "#000000"
                    }
                },
                "opacity": {
                    "value": 0.5,
                    "random": false,
                    "anim": {
                        "enable": false,
                        "speed": 1,
                        "opacity_min": 0.1,
                        "sync": false
                    }
                },
                "size": {
                    "value": 3,
                    "random": true,
                    "anim": {
                        "enable": false,
                        "speed": 40,
                        "size_min": 0.1,
                        "sync": false
                    }
                },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#8a2be2",
                    "opacity": 0.4,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 3,
                    "direction": "none",
                    "random": false,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false,
                    "attract": {
                        "enable": false,
                        "rotateX": 600,
                        "rotateY": 1200
                    }
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {
                        "enable": true,
                        "mode": "grab"
                    },
                    "onclick": {
                        "enable": true,
                        "mode": "push"
                    },
                    "resize": true
                },
                "modes": {
                    "grab": {
                        "distance": 140,
                        "line_linked": {
                            "opacity": 1
                        }
                    },
                    "bubble": {
                        "distance": 400,
                        "size": 40,
                        "duration": 2,
                        "opacity": 8,
                        "speed": 3
                    },
                    "repulse": {
                        "distance": 200,
                        "duration": 0.4
                    },
                    "push": {
                        "particles_nb": 4
                    },
                    "remove": {
                        "particles_nb": 2
                    }
                }
            },
            "retina_detect": true
        });
    }

    // Counter animation
    const counters = document.querySelectorAll('.counter');
    if (counters.length > 0) {
        const speed = 200;

        counters.forEach(counter => {
            const animate = () => {
                const value = +counter.getAttribute('data-target');
                const data = +counter.innerText;

                const time = value / speed;
                if(data < value) {
                    counter.innerText = Math.ceil(data + time);
                    setTimeout(animate, 1);
                } else {
                    counter.innerText = value;
                }
            }

            animate();
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();

                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Navbar scroll effect
    const header = document.querySelector('header');
    if (header) {
        window.addEventListener('scroll', function() {
            header.classList.toggle('scrolled', window.scrollY > 50);

            // Back to top button visibility
            const backToTop = document.querySelector('.back-to-top');
            if (backToTop) {
                backToTop.classList.toggle('active', window.scrollY > 200);
            }
        });
    }

    // Back to top button click event
    const backToTopButton = document.querySelector('.back-to-top');
    if (backToTopButton) {
        backToTopButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({top: 0, behavior: 'smooth'});
        });
    }

    // Toggle sidebar in admin layout
    const toggleSidebarButton = document.querySelector('.toggle-sidebar');
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', function() {
            document.querySelector('.admin-layout').classList.toggle('sidebar-collapsed');
        });

        // Adjust sidebar based on screen size
        function adjustSidebar() {
            if (window.innerWidth < 992) {
                document.querySelector('.admin-layout').classList.add('sidebar-collapsed');
            } else {
                document.querySelector('.admin-layout').classList.remove('sidebar-collapsed');
            }
        }

        // Call on load and resize
        adjustSidebar();
        window.addEventListener('resize', adjustSidebar);
    }

    // Initialize date pickers
    const datePickers = document.querySelectorAll('.datepicker');
    if (datePickers.length > 0 && typeof flatpickr !== 'undefined') {
        flatpickr(datePickers, {
            dateFormat: "Y-m-d",
            allowInput: true
        });
    }

    // File input preview
    const fileInputs = document.querySelectorAll('.custom-file-input');
    if (fileInputs.length > 0) {
        fileInputs.forEach(input => {
            input.addEventListener('change', function(e) {
                const fileName = this.files[0]?.name || 'No file chosen';
                const label = this.nextElementSibling;
                if (label) {
                    label.textContent = fileName;
                }
            });
        });
    }

    // Handle loan type selection to show/hide specific fields
    const loanTypeSelect = document.getElementById('loan_type');
    if (loanTypeSelect) {
        const toggleLoanTypeFields = () => {
            const selectedType = loanTypeSelect.value;
            const goldFields = document.getElementById('gold_loan_fields');
            const landFields = document.getElementById('land_loan_fields');

            if (goldFields && landFields) {
                if (selectedType === 'gold') {
                    goldFields.style.display = 'block';
                    landFields.style.display = 'none';
                } else if (selectedType === 'land') {
                    goldFields.style.display = 'none';
                    landFields.style.display = 'block';
                } else {
                    goldFields.style.display = 'none';
                    landFields.style.display = 'none';
                }
            }
        };

        loanTypeSelect.addEventListener('change', toggleLoanTypeFields);

        // Call initially to set correct state
        toggleLoanTypeFields();
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0 && typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize customer search select2
    const customerSelect = document.getElementById('customer_id');
    if (customerSelect && typeof $.fn.select2 !== 'undefined') {
        $(customerSelect).select2({
            placeholder: 'Search for a customer...',
            minimumInputLength: 2,
            ajax: {
                url: '/api/customers/search',
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        query: params.term
                    };
                },
                processResults: function(data) {
                    return {
                        results: data
                    };
                },
                cache: true
            }
        });
    }
});

// Utility function to format currency
function formatCurrency(amount, symbol = '₹') {
    return `${symbol} ${parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')}`;
}

// Utility function to confirm actions
function confirmAction(message = 'Are you sure you want to perform this action?') {
    return confirm(message);
}