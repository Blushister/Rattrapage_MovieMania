class FormHandler {
    constructor() {
        this.init();
    }

    init() {
        this.setupForms();
        this.setupStepNavigation();
    }

    setupForms() {
        const forms = document.querySelectorAll('form[id$="Form"]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit(form);
            });
        });
    }

    setupStepNavigation() {
        const nextStepBtn = document.getElementById('nextStepBtn');
        if (nextStepBtn) {
            nextStepBtn.addEventListener('click', () => {
                this.goToStep2();
            });
        }

        const backStepBtn = document.getElementById('backStepBtn');
        if (backStepBtn) {
            backStepBtn.addEventListener('click', () => {
                this.goToStep1();
            });
        }
    }

    goToStep2() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            alert('Please fill in all required fields.');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address.');
            return;
        }

        document.getElementById('hiddenEmail').value = email;
        document.getElementById('hiddenPassword').value = password;

        document.getElementById('step1').classList.remove('active');
        document.getElementById('step2').classList.add('active');
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step2').style.display = 'block';
    }

    goToStep1() {
        document.getElementById('step2').classList.remove('active');
        document.getElementById('step1').classList.add('active');
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step1').style.display = 'block';
    }

    getCSRFToken() {
        const formToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (formToken) {
            return formToken.value;
        }
        
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }

    async handleSubmit(form) {
        const formData = new FormData(form);
        const csrfToken = this.getCSRFToken();
        const formId = form.id;

        console.log('=== DEBUG SUBMIT ===');
        console.log('Form ID:', formId);
        console.log('Form action:', form.action);
        console.log('Current URL:', window.location.href);
        console.log('CSRF Token:', csrfToken);
        console.log('Form data entries:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}: ${value}`);
        }
        console.log('==================');

        try {
            const response = await fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            const data = await this.parseResponse(response);
            
            if (data.success) {
                this.handleSuccess(data, formId);
            } else {
                this.handleError(data.error);
            }
        } catch (error) {
            this.handleError('Erreur de connexion: ' + error.message);
        }
    }

    async parseResponse(response) {
        const text = await response.text();
        console.log('=== DEBUG RESPONSE ===');
        console.log('Status:', response.status);
        console.log('Headers:', response.headers);
        console.log('Full response text:', text);
        console.log('=====================');
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error('Failed to parse JSON:', e);
            console.error('Response text was:', text);
            throw new Error('Non-JSON response received: ' + text.substring(0, 200));
        }
    }

    handleSuccess(data, formId) {
        if (data.access_token) {
            localStorage.setItem('jwt_token', data.access_token);
        }
        
        if (formId === 'signupForm') {
            alert('Account created successfully!');
            setTimeout(() => {
                window.location.href = data.redirect || '/';
            }, 1000);
        } else if (data.redirect) {
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            alert(data.message || 'Success!');
        }
    }

    handleError(error) {
        alert('Error: ' + error);
    }
}

class GenreHandler {
    constructor() {
        this.selectedGenres = new Set();
        this.minSelections = 3;
        this.maxSelections = 5;
        this.init();
    }

    init() {
        this.setupGenreCards();
        this.updateSelectionCount();
        this.updateCreateButton();
    }

    setupGenreCards() {
        const genreCards = document.querySelectorAll('.genre-card');
        
        genreCards.forEach(card => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleGenre(card);
            });
        });
    }

    toggleGenre(card) {
        const genreId = card.dataset.genreId;
        const checkbox = card.querySelector('input[type="checkbox"]');
        
        if (this.selectedGenres.has(genreId)) {
            this.selectedGenres.delete(genreId);
            card.classList.remove('selected');
            checkbox.checked = false;
        } else {
            if (this.selectedGenres.size < this.maxSelections) {
                this.selectedGenres.add(genreId);
                card.classList.add('selected');
                checkbox.checked = true;
            } else {
                this.showLimitMessage();
            }
        }
        
        this.updateSelectionCount();
        this.updateCreateButton();
    }

    showLimitMessage() {
        const message = document.createElement('div');
        message.className = 'error';
        message.textContent = `You can select a maximum of ${this.maxSelections} genres.`;
        message.style.position = 'fixed';
        message.style.top = '20px';
        message.style.left = '50%';
        message.style.transform = 'translateX(-50%)';
        message.style.zIndex = '1000';
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 3000);
    }

    updateSelectionCount() {
        const countElement = document.querySelector('.selection-count');
        if (countElement) {
            countElement.textContent = `${this.selectedGenres.size} genres selected`;
        }
    }

    updateCreateButton() {
        const createButton = document.getElementById('createAccountBtn');
        if (createButton) {
            if (this.selectedGenres.size >= this.minSelections) {
                createButton.disabled = false;
                createButton.textContent = 'Create Account';
            } else {
                createButton.disabled = true;
                createButton.textContent = `Select at least ${this.minSelections} genres`;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    new FormHandler();
    new GenreHandler();
});