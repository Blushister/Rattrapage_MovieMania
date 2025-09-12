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
    """Page de connexion"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Call API users
            response = requests.post(f"{settings.USERS_API_URL}/api/v1/login/access-token", 
                                   data={'username': email, 'password': password},
                                   headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            if response.status_code == 200:
                data = response.json()
                # Store token in session
                request.session['access_token'] = data.get('access_token')
                request.session['user_id'] = data.get('user_id')
                
                # Return JSON for AJAX
                return JsonResponse({'success': True, 'message': 'Connexion réussie !'})
            else:
                error_data = response.json() if response.content else {}
                return JsonResponse({'success': False, 'error': error_data.get('detail', 'Email ou mot de passe incorrect.')})
                
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion à l'API: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur de connexion. Veuillez réessayer.'})
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur inattendue.'})
    
    # Get request, return HTML page
    return render(request, 'users/login.html')

def logout_view(request):
    """Déconnexion"""
    request.session.flush()
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('movies:movie_list')

@ensure_csrf_cookie
def register_view(request):
    """Page d'inscription"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Call API users
            response = requests.post(f"{settings.USERS_API_URL}/api/v1/users/open", 
                                   json={
                                       'email': email,
                                       'password': password,
                                       'first_name': '',
                                       'last_name': ''
                                   })
            
            if response.status_code == 200:
                # Return JSON for AJAX
                return JsonResponse({'success': True, 'message': 'Compte créé avec succès !'})
            else:
                error_data = response.json() if response.content else {}
                return JsonResponse({'success': False, 'error': error_data.get('detail', 'Erreur lors de l\'inscription.')})
                
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion à l'API: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur de connexion. Veuillez réessayer.'})
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return JsonResponse({'success': False, 'error': 'Erreur inattendue.'})
    
    # Get request, return HTML page
    return render(request, 'users/register.html')

@login_required
def profile_view(request):
    """Profil utilisateur"""
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
        logger.error(f"Erreur de connexion à l'API: {e}")
        user_data = None
    
    context = {
        'user': user_data,
        'title': 'Mon Profil'
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile_view(request):
    """Modification du profil"""
    user_id = request.session.get('user_id')
    access_token = request.session.get('access_token')
    
    if not user_id or not access_token:
        messages.error(request, 'Session expirée. Veuillez vous reconnecter.')
        return redirect('users:login')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.put(f"{settings.USERS_API_URL}/users/{user_id}", 
                                  json={'first_name': first_name, 'last_name': last_name},
                                  headers=headers)
            
            if response.status_code == 200:
                messages.success(request, 'Profil mis à jour avec succès !')
                return redirect('users:profile')
            else:
                messages.error(request, 'Erreur lors de la mise à jour.')
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion à l'API: {e}")
            messages.error(request, 'Erreur de connexion. Veuillez réessayer.')
    
    # Load current data
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{settings.USERS_API_URL}/users/{user_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
        else:
            user_data = None
    except requests.RequestException as e:
        logger.error(f"Erreur de connexion à l'API: {e}")
        user_data = None
    
    context = {
        'user': user_data,
        'title': 'Modifier mon Profil'
    }
    return render(request, 'users/edit_profile.html', context)
