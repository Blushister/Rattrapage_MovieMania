from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
import requests
import logging

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(f"{settings.USERS_API_LOGIN_URL}/login/access-token", 
                                   data={'username': email, 'password': password},
                                   headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            if response.status_code == 200:
                data = response.json()
                request.session['access_token'] = data.get('access_token')
                request.session['user_id'] = data.get('user_id')
                return JsonResponse({'success': True, 'message': 'Connexion réussie !'})
            else:
                error_data = response.json() if response.content else {}
                return JsonResponse({'success': False, 'error': error_data.get('detail', 'Email ou mot de passe incorrect.')})
                
        except requests.RequestException as e:
            logger.error(f"API connection error: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur de connexion. Veuillez réessayer.'})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur inattendue.'})
    
    return render(request, 'users/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('users:login')

@ensure_csrf_cookie
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Store registration data temporarily
        request.session['temp_email'] = email
        request.session['temp_password'] = password
        request.session['registration_step'] = 'genres'
        
        return JsonResponse({'success': True, 'message': 'Étape suivante : sélection des genres !'})
    
    return render(request, 'users/register.html')

@ensure_csrf_cookie
def genre_selection_view(request):
    # Check if user is in registration flow
    if not request.session.get('temp_email') or not request.session.get('registration_step') == 'genres':
        messages.error(request, 'Vous devez d\'abord vous inscrire pour accéder à cette page.')
        return redirect('users:register')
    
    if request.method == 'POST':
        selected_genres = request.POST.getlist('genres')
        
        # Validate minimum 3 genres
        if len(selected_genres) < 3:
            return JsonResponse({'success': False, 'error': 'Vous devez sélectionner au moins 3 genres.'})
        
        try:
            email = request.session.get('temp_email')
            password = request.session.get('temp_password')
            
            if email and password:
                # Create account
                create_response = requests.post(f"{settings.USERS_API_URL}/open", 
                                              json={
                                                  'email': email,
                                                  'password': password,
                                                  'genres': []
                                              })
                
                logger.info(f"Account creation attempt for {email}")
                logger.info(f"Creation response: {create_response.status_code}")
                
                if create_response.status_code == 200:
                    logger.info("Account created successfully, attempting login")
                    
                    # Login user
                    login_response = requests.post(f"{settings.USERS_API_LOGIN_URL}/login/access-token", 
                                                  data={'username': email, 'password': password},
                                                  headers={'Content-Type': 'application/x-www-form-urlencoded'})
                    
                    logger.info(f"Login response: {login_response.status_code}")
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        access_token = login_data.get('access_token')
                        
                        # Get user info for user_id
                        user_info_response = requests.post(f"{settings.USERS_API_LOGIN_URL}/login/test-token",
                                                         headers={'Authorization': f'Bearer {access_token}'})
                        
                        logger.info(f"Test-token response: {user_info_response.status_code}")
                        
                        if user_info_response.status_code == 200:
                            user_info = user_info_response.json()
                            user_id = user_info.get('user_id')
                            
                            logger.info(f"Login successful, user_id: {user_id}")
                            
                            # Save genres
                            headers = {'Authorization': f'Bearer {access_token}'}
                            genres_response = requests.post(f"{settings.GENREUSERS_API_URL}/", 
                                                           json={'genre_ids': [int(g) for g in selected_genres]},
                                                           headers=headers)
                            
                            logger.info(f"Genres response: {genres_response.status_code}")
                            
                            if genres_response.status_code == 200:
                                # Clean temporary session
                                request.session.pop('temp_email', None)
                                request.session.pop('temp_password', None)
                                request.session.pop('registration_step', None)
                                
                                logger.info("Complete registration successful")
                                return JsonResponse({'success': True, 'message': 'Inscription terminée ! Vous pouvez maintenant vous connecter.'})
                            else:
                                logger.error(f"Genres save error: {genres_response.text}")
                                return JsonResponse({'success': False, 'error': 'Erreur lors de la sauvegarde des genres.'})
                        else:
                            logger.error(f"Test-token error: {user_info_response.text}")
                            return JsonResponse({'success': False, 'error': 'Erreur lors de la récupération des informations utilisateur.'})
                    else:
                        logger.error(f"Login error: {login_response.text}")
                        return JsonResponse({'success': False, 'error': 'Erreur lors de la connexion.'})
                else:
                    error_data = create_response.json() if create_response.content else {}
                    logger.error(f"Account creation error: {error_data}")
                    return JsonResponse({'success': False, 'error': error_data.get('detail', 'Erreur lors de la création du compte.')})
            else:
                return JsonResponse({'success': False, 'error': 'Session expirée.'})
                
        except requests.RequestException as e:
            logger.error(f"API connection error: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur de connexion. Veuillez réessayer.'})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur inattendue.'})
    
    # Default genres based on Users API
    genres = [
        {"genre_id": 1, "name": "Action"},
        {"genre_id": 2, "name": "Adventure"},
        {"genre_id": 3, "name": "Animation"},
        {"genre_id": 4, "name": "Comedy"},
        {"genre_id": 5, "name": "Crime"},
        {"genre_id": 6, "name": "Documentary"},
        {"genre_id": 7, "name": "Drama"},
        {"genre_id": 8, "name": "Family"},
        {"genre_id": 9, "name": "Fantasy"},
        {"genre_id": 10, "name": "History"},
        {"genre_id": 11, "name": "Horror"},
        {"genre_id": 12, "name": "Music"},
        {"genre_id": 13, "name": "Mystery"},
        {"genre_id": 14, "name": "Romance"},
        {"genre_id": 15, "name": "Science Fiction"},
        {"genre_id": 16, "name": "TV Movie"},
        {"genre_id": 17, "name": "Thriller"},
        {"genre_id": 18, "name": "War"},
        {"genre_id": 19, "name": "Western"}
    ]
    
    context = {
        'genres': genres,
        'title': 'Sélection des genres'
    }
    return render(request, 'users/genre_selection.html', context)

@login_required
def profile_view(request):
    user_id = request.session.get('user_id')
    access_token = request.session.get('access_token')
    
    if not user_id or not access_token:
        messages.error(request, 'Session expirée. Veuillez vous reconnecter.')
        return redirect('users:login')
    
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{settings.USERS_API_URL}/users/{user_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
        else:
            user_data = None
            messages.error(request, 'Erreur lors du chargement du profil.')
    except requests.RequestException as e:
        logger.error(f"API connection error: {e}")
        user_data = None
    
    context = {
        'user': user_data,
        'title': 'Mon Profil'
    }
    return render(request, 'users/profile.html', context)