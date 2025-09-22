let selectedGenres = [];

function toggleGenreTag(tagElement) {
    const genreId = tagElement.getAttribute('data-genre-id');
    const checkbox = tagElement.querySelector('input[type="checkbox"]');
    const icon = tagElement.querySelector('.tag-icon');
    
    if (tagElement.classList.contains('selected')) {
        tagElement.classList.remove('selected');
        checkbox.checked = false;
        icon.textContent = '+';
        selectedGenres = selectedGenres.filter(id => id !== genreId);
    } else {
        tagElement.classList.add('selected');
        checkbox.checked = true;
        icon.textContent = '✓';
        selectedGenres.push(genreId);
    }
    
    updateSelectionCount();
}

function updateSelectionCount() {
    const count = selectedGenres.length;
    const countElement = document.querySelector('.selection-count');
    const createBtn = document.getElementById('createAccountBtn');
    
    if (count === 0) {
        countElement.textContent = '0 genres sélectionnés';
        countElement.classList.remove('valid');
    } else if (count < 3) {
        countElement.textContent = `${count} genres sélectionnés (${3 - count} de plus requis)`;
        countElement.classList.remove('valid');
    } else {
        countElement.textContent = `${count} genres sélectionnés ✓`;
        countElement.classList.add('valid');
    }
    
    createBtn.disabled = count < 3;
}

document.addEventListener('DOMContentLoaded', function() {
    const nextStepBtn = document.getElementById('nextStepBtn');
    const backStepBtn = document.getElementById('backStepBtn');
    
    if (nextStepBtn) {
        nextStepBtn.addEventListener('click', function() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (email && password) {
                document.getElementById('hiddenEmail').value = email;
                document.getElementById('hiddenPassword').value = password;
                
                document.getElementById('step1').classList.remove('active');
                document.getElementById('step2').classList.add('active');
                
                document.querySelector('.card').classList.add('wide-card');
            }
        });
    }
    
    if (backStepBtn) {
        backStepBtn.addEventListener('click', function() {
            document.getElementById('step2').classList.remove('active');
            document.getElementById('step1').classList.add('active');
            
            document.querySelector('.card').classList.remove('wide-card');
        });
    }
    
    updateSelectionCount();
});