document.addEventListener('DOMContentLoaded', function() {
    let API_BASE_URL = 'http://localhost:8000';
    const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/original';
    
    const FALLBACK_IMAGES = [
        '/f4KiaxSD5B8bcg5VLsvrDhaZlFu.jpg',
        '/r5xT55Era1XrpAq6XNsrPpozNjM.jpg',
        '/5tKiuZvvV1lic7v65rdoGPmoOvf.jpg',
        '/dqK9Hag1054tghRQSqLSfrkvQnA.jpg',
        '/bXH4lyFS6tctnBgxK1eYRuwekR0.jpg',
        '/y8yvIrmoM2PLuJcSto7OmOfsXQj.jpg',
        '/3lrNJ5jNqKq9UpQrXo8FNFzyoE4.jpg',
        '/yajM2akz8QKOx0RdvN6OYaxe3GN.jpg',
        '/pkxPkHOPJjOvzfQOclANEBT8OfK.jpg',
        '/nu9nyVoyHecM6Zj6nTeTRgv54mb.jpg'
    ];
    
    function getRandomFallbackImage() {
        const randomIndex = Math.floor(Math.random() * FALLBACK_IMAGES.length);
        return TMDB_IMAGE_BASE + FALLBACK_IMAGES[randomIndex];
    }
    const genreRecommendationsContainer = document.getElementById('genre-recommendations');
    const trendingRecommendationsContainer = document.getElementById('trending-recommendations');
    const newMoviesContainer = document.getElementById('new-movies');
    const movieCardTemplate = document.getElementById('movie-card-template');
    
    function getAuthToken() {
        return localStorage.getItem('jwt_token');
    }
    function createMovieCard(movie) {
        const template = movieCardTemplate.content.cloneNode(true);
        const card = template.querySelector('.movie-card');
        const img = template.querySelector('.movie-poster img');
        const title = template.querySelector('.movie-title');
        const year = template.querySelector('.movie-year');
        const rating = template.querySelector('.rating-value');
        
        card.dataset.movieId = movie.movie_id;
        
        card.addEventListener('click', () => {
            try {
                openMovieModal(movie.movie_id);
            } catch (error) {
                console.error('Error opening movie modal:', error);
            }
        });
        
        if (movie.backdrop_path && movie.backdrop_path !== null) {
            img.src = `${TMDB_IMAGE_BASE}${movie.backdrop_path}`;
        } else {
            img.src = getRandomFallbackImage();
        }
        
        img.alt = movie.title;
        
        img.onerror = function() {
            this.onerror = null;
            this.src = getRandomFallbackImage();
        };
        title.textContent = movie.title;
        
        if (movie.release_date) {
            const releaseDate = new Date(movie.release_date);
            year.textContent = releaseDate.getFullYear();
        } else {
            year.textContent = '-';
        }
        
        if (movie.vote_average) {
            rating.textContent = movie.vote_average.toFixed(1);
        } else {
            rating.textContent = '-';
        }
        
        
        return template;
    }
    
    
    async function loadRecommendations() {
        const token = getAuthToken();
        
        if (!token) {
            console.error('Missing authentication token');
            window.location.href = '/login/';
            return;
        }
        
        try {
            showLoadingState();
            
            const response = await fetch(`${API_BASE_URL}/recommendations/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                if (response.status === 403) {
                    localStorage.removeItem('jwt_token');
                    window.location.href = '/login/';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const recommendations = await response.json();
            displayRecommendations(recommendations);
            
        } catch (error) {
            console.error('Error loading recommendations:', error);
            showErrorState();
        }
    }
    
    function showLoadingState() {
        const containers = [genreRecommendationsContainer, trendingRecommendationsContainer, newMoviesContainer];
        containers.forEach(container => {
            if (container) {
                container.innerHTML = '<div class="loading">Loading...</div>';
            }
        });
    }
    
    function showErrorState() {
        const containers = [genreRecommendationsContainer, trendingRecommendationsContainer, newMoviesContainer];
        containers.forEach(container => {
            if (container) {
                container.innerHTML = '<div class="error-message">Error loading recommendations</div>';
            }
        });
    }
    
    function displayRecommendations(recommendations) {
        if (genreRecommendationsContainer) genreRecommendationsContainer.innerHTML = '';
        if (trendingRecommendationsContainer) trendingRecommendationsContainer.innerHTML = '';
        if (newMoviesContainer) newMoviesContainer.innerHTML = '';
        
        Object.keys(recommendations).forEach(key => {
            const movies = recommendations[key];
            
            if (!Array.isArray(movies)) {
                return;
            }
            
            let targetContainer;
            if (key.startsWith('genre_')) {
                targetContainer = genreRecommendationsContainer;
            } else if (key.includes('trending') || key.includes('popular') || key === 'trending_carousel') {
                targetContainer = trendingRecommendationsContainer;
            } else {
                targetContainer = newMoviesContainer;
            }
            
            if (targetContainer) {
                movies.forEach(movie => {
                    const movieCard = createMovieCard(movie);
                    targetContainer.appendChild(movieCard);
                });
            }
        });
        
        if (!genreRecommendationsContainer?.children.length && trendingRecommendationsContainer?.children.length) {
            const trendingMovies = Array.from(trendingRecommendationsContainer.children).slice(0, 10);
            trendingMovies.forEach(movie => {
                const clonedMovie = movie.cloneNode(true);
                const clonedCard = clonedMovie.querySelector('.movie-card');
                if (clonedCard) {
                    clonedCard.addEventListener('click', () => {
                        openMovieModal(clonedCard.dataset.movieId);
                    });
                }
                genreRecommendationsContainer?.appendChild(clonedMovie);
            });
        }
        
        if (!newMoviesContainer?.children.length && trendingRecommendationsContainer?.children.length) {
            const trendingMovies = Array.from(trendingRecommendationsContainer.children).slice(5, 13);
            trendingMovies.forEach(movie => {
                const clonedMovie = movie.cloneNode(true);
                const clonedCard = clonedMovie.querySelector('.movie-card');
                if (clonedCard) {
                    clonedCard.addEventListener('click', () => {
                        openMovieModal(clonedCard.dataset.movieId);
                    });
                }
                newMoviesContainer?.appendChild(clonedMovie);
            });
        }
    }
    
    function setupSearch() {
        const searchInput = document.querySelector('.search-input');
        const searchBtn = document.querySelector('.search-btn');
        
        if (searchInput && searchBtn) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    performSearch(e.target.value);
                }, 300);
            });
            
            searchBtn.addEventListener('click', () => {
                performSearch(searchInput.value);
            });
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch(searchInput.value);
                }
            });
        }
    }
    
    async function performSearch(query) {
        if (!query.trim()) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/movies/search/?title=${encodeURIComponent(query)}&limit=20`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const movies = await response.json();
            displaySearchResults(movies);
            
        } catch (error) {
            console.error('Search error:', error);
        }
    }
    
    function displaySearchResults(movies) {
        console.log('Search results:', movies);
    }
    
    function setupCarouselInteractions() {
        const carousels = document.querySelectorAll('.movie-carousel');
        
        carousels.forEach(carousel => {
            if (!('ontouchstart' in window)) {
                carousel.addEventListener('wheel', (e) => {
                    if (e.deltaY !== 0) {
                        e.preventDefault();
                        carousel.scrollLeft += e.deltaY;
                    }
                });
            }
            
            const cards = carousel.querySelectorAll('.movie-card');
            cards.forEach((card, index) => {
                card.setAttribute('tabindex', '0');
                
                card.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft' && index > 0) {
                        e.preventDefault();
                        cards[index - 1].focus();
                        cards[index - 1].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    } else if (e.key === 'ArrowRight' && index < cards.length - 1) {
                        e.preventDefault();
                        cards[index + 1].focus();
                        cards[index + 1].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    } else if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        card.click();
                    }
                });
            });
        });
    }
    
    function setupUserMenu() {
        const userAvatar = document.querySelector('.user-avatar');
        
        if (userAvatar) {
            userAvatar.addEventListener('click', () => {
                console.log('User menu clicked');
            });
        }
    }
    
    async function loadApiConfig() {
        try {
            const response = await fetch('/api-config/');
            if (response.ok) {
                const config = await response.json();
                API_BASE_URL = config.recommendations_api_url || API_BASE_URL;
            }
        } catch (error) {
            console.warn('Unable to load API configuration, using defaults');
        }
    }

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
            
            const response = await fetch(`/users/movie/${movieId}/`, {
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
            const response = await fetch('/users/rate-movie/', {
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

    document.addEventListener('click', (e) => {
        const modal = document.getElementById('movieModal');
        if (e.target === modal || e.target.classList.contains('modal-close')) {
            closeMovieModal();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('movieModal');
            if (modal && modal.classList.contains('show')) {
                closeMovieModal();
            }
        }
    });

    window.closeMovieModal = closeMovieModal;

    async function init() {
        await loadApiConfig();
        setupSearch();
        setupCarouselInteractions();
        setupUserMenu();
        loadRecommendations();
    }
    
    init();
});