let currentMovieRating = 0;

async function openMovieModal(movieId) {
    const modal = document.getElementById('movieModal');
    
    if (!modal) {
        console.error('Movie modal element not found in DOM');
        return;
    }
    
    try {
        window.lastFocusedElement = document.activeElement;
        
        modal.classList.add('show');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        modal.focus();
        
        resetModalContent();
        
        const response = await fetch(`/movie/${movieId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        populateModal(data);
        
    } catch (error) {
        console.error('Error loading movie details:', error);
        closeMovieModal();
    }
}

function closeMovieModal() {
    const modal = document.getElementById('movieModal');
    if (modal) {
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = 'auto';
        currentMovieRating = 0;
        
        if (window.lastFocusedElement && window.lastFocusedElement.focus) {
            window.lastFocusedElement.focus();
        }
    }
}

function resetModalContent() {
    document.getElementById('modalTitle').textContent = 'Loading...';
    document.getElementById('modalPoster').src = '';
    document.getElementById('modalOverview').textContent = 'Loading...';
    document.getElementById('modalCast').innerHTML = '<p>Loading cast information...</p>';
    document.getElementById('modalCrew').innerHTML = '<p>Loading crew information...</p>';
    resetStarRating();
}

function populateModal(data) {
    const movie = data.movie;
    const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';
    
    document.getElementById('modalTitle').textContent = movie.title;
    document.getElementById('modalOverview').textContent = movie.overview || 'No synopsis available';
    document.getElementById('modalReleaseDate').textContent = formatDate(movie.release_date);
    document.getElementById('modalRuntime').textContent = formatRuntime(movie.runtime);
    document.getElementById('modalRating').textContent = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
    document.getElementById('modalBudget').textContent = formatBudget(movie.budget);
    document.getElementById('modalRevenue').textContent = formatBudget(movie.revenue);
    
    const posterImg = document.getElementById('modalPoster');
    posterImg.alt = `Movie poster for ${movie.title}`;
    if (movie.poster_path) {
        posterImg.src = TMDB_IMAGE_BASE + movie.poster_path;
    } else {
        posterImg.src = '/static/images/no-poster.svg';
        posterImg.alt = `No poster available for ${movie.title}`;
    }
    
    const taglineElement = document.getElementById('modalTagline');
    if (movie.tagline && movie.tagline.trim()) {
        taglineElement.textContent = movie.tagline;
        taglineElement.parentElement.style.display = 'block';
    } else {
        taglineElement.textContent = '';
        taglineElement.parentElement.style.display = 'none';
    }
    
    const genresContainer = document.getElementById('modalGenres');
    genresContainer.innerHTML = '';
    if (movie.genres && movie.genres.length) {
        movie.genres.forEach(genre => {
            if (genre && genre.trim()) {
                const genreTag = document.createElement('span');
                genreTag.className = 'genre-tag';
                genreTag.textContent = genre;
                genresContainer.appendChild(genreTag);
            }
        });
    }
    
    if (movie.user_rating) {
        setStarRating(movie.user_rating);
    }
    
    populateCast(data.cast);
    
    populateCrew(data.crew);
    
    setupStarRating(movie.id);
}

function populateCast(cast) {
    const castContainer = document.getElementById('modalCast');
    castContainer.innerHTML = '';
    
    if (!cast || cast.length === 0) {
        castContainer.innerHTML = '<p>No cast information available</p>';
        return;
    }
    
    cast.forEach(actor => {
        const castMember = document.createElement('div');
        castMember.className = 'cast-member';
        
        const photoUrl = actor.photo ? `https://image.tmdb.org/t/p/w185${actor.photo}` : '/static/images/no-person.svg';
        
        castMember.setAttribute('role', 'listitem');
        castMember.innerHTML = `
            <img src="${photoUrl}" alt="Photo de ${actor.name}" onerror="this.src='/static/images/no-person.svg'">
            <div class="cast-member-name">${actor.name}</div>
            <div class="cast-character">${actor.character_name || ''}</div>
        `;
        
        castContainer.appendChild(castMember);
    });
}

function populateCrew(crew) {
    const crewContainer = document.getElementById('modalCrew');
    crewContainer.innerHTML = '';
    
    if (!crew || crew.length === 0) {
        crewContainer.innerHTML = '<p>No crew information available</p>';
        return;
    }
    
    crew.forEach(member => {
        const crewMember = document.createElement('div');
        crewMember.className = 'crew-member';
        
        const photoUrl = member.photo ? `https://image.tmdb.org/t/p/w185${member.photo}` : '/static/images/no-person.svg';
        
        crewMember.setAttribute('role', 'listitem');
        crewMember.innerHTML = `
            <img src="${photoUrl}" alt="Photo de ${member.name}" onerror="this.src='/static/images/no-person.svg'">
            <div class="crew-member-name">${member.name}</div>
            <div class="crew-job">${member.job}</div>
        `;
        
        crewContainer.appendChild(crewMember);
    });
}

function setupStarRating(movieId) {
    const stars = document.querySelectorAll('#starRating .star');
    const ratingFeedback = document.getElementById('ratingFeedback');
    
    stars.forEach((star, index) => {
        const rating = index + 1;
        
        star.setAttribute('tabindex', index === 0 ? '0' : '-1');
        
        if (!('ontouchstart' in window)) {
            star.addEventListener('mouseenter', () => {
                highlightStars(rating);
            });
            
            star.addEventListener('mouseleave', () => {
                highlightStars(currentMovieRating);
            });
        }
        
        star.addEventListener('click', () => {
            submitRating(movieId, rating);
        });
        
        star.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && index > 0) {
                e.preventDefault();
                stars[index - 1].focus();
                stars[index - 1].setAttribute('tabindex', '0');
                star.setAttribute('tabindex', '-1');
            } else if (e.key === 'ArrowRight' && index < stars.length - 1) {
                e.preventDefault();
                stars[index + 1].focus();
                stars[index + 1].setAttribute('tabindex', '0');
                star.setAttribute('tabindex', '-1');
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                submitRating(movieId, rating);
            }
        });
        
        star.addEventListener('focus', () => {
            if (!('ontouchstart' in window)) {
                highlightStars(rating);
            }
        });
        
        star.addEventListener('blur', () => {
            if (!('ontouchstart' in window)) {
                highlightStars(currentMovieRating);
            }
        });
    });
}

function highlightStars(rating) {
    const stars = document.querySelectorAll('#starRating .star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('filled');
            star.setAttribute('aria-checked', 'true');
        } else {
            star.classList.remove('filled');
            star.setAttribute('aria-checked', 'false');
        }
    });
}

function setStarRating(rating) {
    currentMovieRating = rating;
    highlightStars(rating);
    document.getElementById('ratingFeedback').textContent = `Your rating: ${rating}/5`;
}

function resetStarRating() {
    currentMovieRating = 0;
    highlightStars(0);
    document.getElementById('ratingFeedback').textContent = 'Click stars to rate this movie';
}

async function submitRating(movieId, rating) {
    try {
        const response = await fetch('/rate-movie/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                movie_id: movieId,
                rating: rating
            })
        });
        
        if (response.ok) {
            setStarRating(rating);
        } else {
            throw new Error('Failed to save rating');
        }
    } catch (error) {
        console.error('Error saving rating:', error);
        alert('Error saving rating. Please try again.');
    }
}

function getCookie(name) {
    if (name === 'csrftoken' && window.csrfToken) {
        return window.csrfToken;
    }
    
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatRuntime(minutes) {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}min`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatBudget(budget) {
    if (!budget) return 'Not available';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(budget);
}

function openEditProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.classList.add('show');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        loadCurrentUserData();
    }
}

function closeEditProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = 'auto';
    }
}

async function loadCurrentUserData() {
    try {
        const response = await fetch('/profile-data/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            document.getElementById('firstName').value = data.prenom || '';
            document.getElementById('lastName').value = data.nom || '';
            document.getElementById('birthday').value = data.birthday || '';
            document.getElementById('gender').value = data.sexe || '';
            document.getElementById('email').value = data.email || '';
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

async function submitProfileForm() {
    const profileForm = document.getElementById('profileForm');
    if (!profileForm) return;
    
    const formData = new FormData(profileForm);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
            
            try {
                const response = await fetch('/update-profile/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(data)
                });
                
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                console.log('Response URL:', response.url);
                console.log('Response redirected:', response.redirected);
                
                const responseText = await response.text();
                console.log('Raw response text:', responseText);
                
                if (response.ok) {
                    try {
                        const responseData = JSON.parse(responseText);
                        console.log('Parsed JSON response:', responseData);
                        alert('Profile updated successfully!');
                        
                        const displayName = (data.prenom || '') + ' ' + (data.nom || '');
                        const usernameElement = document.querySelector('.hero-title');
                        if (usernameElement && displayName.trim()) {
                            usernameElement.textContent = displayName.trim();
                        }
                        
                        closeEditProfileModal();
                    } catch (jsonError) {
                        console.error('JSON parse error:', jsonError);
                        console.error('Response that failed to parse:', responseText);
                        alert('Error: Response was successful but not valid JSON');
                    }
                } else {
                    console.error('HTTP error response:', responseText);
                    try {
                        const errorData = JSON.parse(responseText);
                        alert('Error updating profile: ' + (errorData.error || 'Unknown error'));
                    } catch (jsonError) {
                        console.error('Error response is not JSON:', responseText.substring(0, 500));
                        alert('Server error: Received non-JSON error response');
                    }
                }
            } catch (error) {
                console.error('Error updating profile:', error);
                alert('Error updating profile. Please try again.');
            }
}

async function submitPasswordForm() {
    const passwordForm = document.getElementById('passwordForm');
    if (!passwordForm) return;
    
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match!');
        return;
    }
    
    const formData = new FormData(passwordForm);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    try {
        const response = await fetch('/change-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('Password changed successfully!');
            passwordForm.reset();
            closeEditProfileModal();
        } else {
            const errorData = await response.json();
            alert('Error changing password: ' + (errorData.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error changing password:', error);
        alert('Error changing password. Please try again.');
    }
}

document.addEventListener('click', (e) => {
    const modal = document.getElementById('movieModal');
    if (e.target === modal || e.target.classList.contains('modal-close')) {
        closeMovieModal();
    }
    
    const editModal = document.getElementById('editProfileModal');
    if (e.target === editModal) {
        closeEditProfileModal();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('movieModal');
        if (modal && modal.classList.contains('show')) {
            closeMovieModal();
        }
        
        const editModal = document.getElementById('editProfileModal');
        if (editModal && editModal.classList.contains('show')) {
            closeEditProfileModal();
        }
    }
});

window.closeMovieModal = closeMovieModal;
window.openEditProfileModal = openEditProfileModal;
window.closeEditProfileModal = closeEditProfileModal;

document.addEventListener('DOMContentLoaded', function() {
    const movieCards = document.querySelectorAll('.movie-card');
    movieCards.forEach(card => {
        card.addEventListener('click', function() {
            const movieId = this.dataset.movieId;
            openMovieModal(movieId);
        });
    });

    const carousel = document.querySelector('.movie-carousel');
    if (carousel && !('ontouchstart' in window)) {
        carousel.addEventListener('wheel', (e) => {
            if (e.deltaY !== 0) {
                e.preventDefault();
                carousel.scrollLeft += e.deltaY;
            }
        });
    }
});