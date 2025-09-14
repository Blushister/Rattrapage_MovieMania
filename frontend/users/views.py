from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
import logging
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


def get_genres_from_db():
    try:
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword'
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT genre_id, name FROM Genres ORDER BY name")
            genres = cursor.fetchall()
            cursor.close()
            connection.close()
            return genres
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return []
    return []


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
                access_token = data.get('access_token')
                request.session['access_token'] = access_token
                request.session['user_id'] = data.get('user_id')
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful!', 
                    'redirect': '/users/home/',
                    'access_token': access_token
                })
            else:
                error_data = response.json() if response.content else {}
                return JsonResponse({'success': False, 'error': error_data.get('detail', 'Invalid email or password.')})
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JsonResponse({'success': False, 'error': 'Connection error.'})
    
    return render(request, 'users/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('users:login')


@ensure_csrf_cookie
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_genres = request.POST.getlist('genres')
        
        if not email or not password:
            return JsonResponse({'success': False, 'error': 'Email and password required.'})
        
        if len(selected_genres) < 3:
            return JsonResponse({'success': False, 'error': 'Please select at least 3 genres.'})
        
        try:
            # Create user account with empty genres list initially
            create_response = requests.post(f"{settings.USERS_API_URL}/open", 
                                          json={'email': email, 'password': password, 'genres': []})
            
            if create_response.status_code == 200:
                login_response = requests.post(f"{settings.USERS_API_LOGIN_URL}/login/access-token", 
                                             data={'username': email, 'password': password},
                                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data.get('access_token')
                    
                    # Save user genre preferences after account creation
                    headers = {'Authorization': f'Bearer {access_token}'}
                    genres_response = requests.post(f"{settings.GENREUSERS_API_URL}/", 
                                                   json={'genre_ids': [int(g) for g in selected_genres]},
                                                   headers=headers)
                    
                    if genres_response.status_code == 200:
                        request.session['access_token'] = access_token
                        request.session['user_id'] = login_data.get('user_id')
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Account created successfully!', 
                            'redirect': '/users/home/',
                            'access_token': access_token
                        })
                    else:
                        logger.error(f"Failed to save user preferences: {genres_response.text}")
                        return JsonResponse({'success': False, 'error': 'Failed to save genre preferences.'})
                else:
                    logger.error(f"Post-registration authentication failed: {login_response.text}")
                    return JsonResponse({'success': False, 'error': 'Login failed after account creation.'})
            else:
                logger.error(f"User registration failed: {create_response.text}")
                return JsonResponse({'success': False, 'error': 'User account creation failed.'})
                
        except Exception as e:
            logger.error(f"Registration process failed: {e}")
            return JsonResponse({'success': False, 'error': 'Unexpected error occurred.'})
    
    genres = get_genres_from_db()
    return render(request, 'users/register.html', {'genres': genres})


def home_view(request):
    # Authentication check via session token
    if 'access_token' not in request.session:
        return redirect('users:login')
    
    context = {
        'recommendations_api_url': settings.RECOMMENDATIONS_API_URL,
    }
    return render(request, 'users/home.html', context)


def api_config(request):
    config = {
        'recommendations_api_url': settings.RECOMMENDATIONS_API_URL,
    }
    return JsonResponse(config)




