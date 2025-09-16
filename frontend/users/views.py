from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
import logging
import json
import mysql.connector
from mysql.connector import Error
import hashlib
import bcrypt

logger = logging.getLogger(__name__)


def get_user_id_from_api(access_token):
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{settings.USERS_API_URL}/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get('id') or user_data.get('user_id')
            return user_id
        else:
            logger.error(f"API call failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling Users API: {e}")
        return None


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
    if 'access_token' in request.session:
        return redirect('users:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(f"{settings.USERS_API_LOGIN_URL}/access-token", 
                                   data={'username': email, 'password': password},
                                   headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                
                # Get user info from /me endpoint
                user_response = requests.get(f"{settings.USERS_API_URL}/me",
                                           headers={'Authorization': f'Bearer {access_token}'})
                
                request.session['access_token'] = access_token
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user_id = user_data.get('user_id') or user_data.get('id')
                    request.session['user_id'] = user_id
                    request.session['username'] = user_data.get('email', email)  # Use login email as fallback
                    request.session['user_prenom'] = user_data.get('prenom')
                    request.session['user_nom'] = user_data.get('nom')
                else:
                    # Fallback if /me endpoint fails
                    request.session['username'] = email
                    request.session['user_prenom'] = None
                    request.session['user_nom'] = None
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful!', 
                    'redirect': '/home/',
                    'access_token': access_token
                })
            else:
                error_data = response.json() if response.content else {}
                return JsonResponse({'success': False, 'error': error_data.get('detail', 'Invalid email or password.')})
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JsonResponse({'success': False, 'error': 'Connection error.'})
    
    return render(request, 'users/login.html')


@csrf_protect
def logout_view(request):
    if request.method == 'POST':
        request.session.flush()
        return JsonResponse({'success': True, 'message': 'Logged out successfully'})
    return redirect('users:login')


@ensure_csrf_cookie
def register_view(request):
    if 'access_token' in request.session:
        return redirect('users:home')
    
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
                login_response = requests.post(f"{settings.USERS_API_LOGIN_URL}/access-token", 
                                             data={'username': email, 'password': password},
                                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data.get('access_token')
                    
                    headers = {'Authorization': f'Bearer {access_token}'}
                    # Save user genre preferences after account creation
                    genres_response = requests.post(f"{settings.GENREUSERS_API_URL}/", 
                                                   json={'genre_ids': [int(g) for g in selected_genres]},
                                                   headers=headers)
                    
                    if genres_response.status_code == 200:
                        user_id = login_data.get('user_id')
                        request.session['access_token'] = access_token
                        request.session['user_id'] = user_id
                        request.session['username'] = email
                        request.session['user_prenom'] = None
                        request.session['user_nom'] = None
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Account created successfully!', 
                            'redirect': '/home/',
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


def get_movie_details(request, movie_id):
    if 'access_token' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword'
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            movie_query = """
                SELECT m.*, GROUP_CONCAT(g.name) as genres
                FROM Movies m
                LEFT JOIN MovieGenres mg ON m.movie_id = mg.movie_id
                LEFT JOIN Genres g ON mg.genre_id = g.genre_id
                WHERE m.movie_id = %s
                GROUP BY m.movie_id
            """
            cursor.execute(movie_query, (movie_id,))
            movie = cursor.fetchone()
            
            if not movie:
                cursor.close()
                connection.close()
                return JsonResponse({'error': 'Movie not found'}, status=404)
            
            user_rating_query = """
                SELECT note FROM MovieUsers 
                WHERE movie_id = %s AND user_id = %s
            """
            cursor.execute(user_rating_query, (movie_id, request.session.get('user_id')))
            user_rating = cursor.fetchone()
            movie['user_rating'] = user_rating['note'] if user_rating else None
            
            cast_query = """
                SELECT p.name, p.photo, c.character_name, c.cast_order
                FROM Credits c
                JOIN Peoples p ON c.id_people = p.people_id
                JOIN Jobs j ON c.id_job = j.job_id
                WHERE c.id_movie = %s AND j.title = 'Actor'
                ORDER BY c.cast_order
                LIMIT 10
            """
            cursor.execute(cast_query, (movie_id,))
            cast = cursor.fetchall()
            
            crew_query = """
                SELECT p.name, p.photo, j.title as job
                FROM Credits c
                JOIN Peoples p ON c.id_people = p.people_id
                JOIN Jobs j ON c.id_job = j.job_id
                WHERE c.id_movie = %s AND j.title IN ('Director', 'Producer', 'Writer', 'Cinematography')
                ORDER BY 
                    CASE j.title 
                        WHEN 'Director' THEN 1
                        WHEN 'Producer' THEN 2
                        WHEN 'Writer' THEN 3
                        ELSE 4
                    END
                LIMIT 8
            """
            cursor.execute(crew_query, (movie_id,))
            crew = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            response_data = {
                'movie': {
                    'id': movie['movie_id'],
                    'title': movie['title'],
                    'overview': movie['overview'],
                    'poster_path': movie['poster_path'],
                    'backdrop_path': movie['backdrop_path'],
                    'release_date': movie['release_date'].strftime('%Y-%m-%d') if movie['release_date'] else None,
                    'runtime': movie['runtime'],
                    'vote_average': movie['vote_average'],
                    'vote_count': movie['vote_count'],
                    'budget': movie['budget'],
                    'revenue': movie['revenue'],
                    'tagline': movie['tagline'],
                    'genres': movie['genres'].split(',') if movie['genres'] else [],
                    'user_rating': movie['user_rating']
                },
                'cast': cast,
                'crew': crew
            }
            
            return JsonResponse(response_data)
            
    except Error as e:
        logger.error(f"Database error in get_movie_details: {e}")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in get_movie_details: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@csrf_protect
def rate_movie(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if 'access_token' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        rating = data.get('rating')
        
        if not movie_id or not rating:
            return JsonResponse({'error': 'movie_id and rating required'}, status=400)
        
        if rating < 1 or rating > 5:
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            user_id = request.session.get('user_id')
            
            if not user_id:
                access_token = request.session.get('access_token')
                if access_token:
                    user_id = get_user_id_from_api(access_token)
                    if user_id:
                        request.session['user_id'] = user_id
            
            if not user_id:
                logger.error("User ID is None or missing from session and JWT")
                return JsonResponse({'error': 'User not authenticated properly'}, status=401)
            
            query = """
                INSERT INTO MovieUsers (movie_id, user_id, note, saved)
                VALUES (%s, %s, %s, 0)
                ON DUPLICATE KEY UPDATE note = %s
            """
            cursor.execute(query, (movie_id, user_id, rating, rating))
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return JsonResponse({'success': True, 'message': 'Rating saved successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Error as e:
        logger.error(f"Database error in rate_movie: {e}")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in rate_movie: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@ensure_csrf_cookie
def profile_view(request):
    if 'access_token' not in request.session:
        return redirect('users:login')
    
    user_id = request.session.get('user_id')
    logger.info(f"Session user_id: {user_id}")
    if not user_id:
        access_token = request.session.get('access_token')
        if access_token:
            user_id = get_user_id_from_api(access_token)
            logger.info(f"API user_id: {user_id}")
            if user_id:
                request.session['user_id'] = user_id
    
    if not user_id:
        logger.error("No user_id found, redirecting to login")
        return redirect('users:login')
    
    logger.info(f"Using user_id: {user_id} for profile view")
    
    try:
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword',
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            user_query = """
                SELECT nom, prenom, email, birthday, sexe
                FROM Users
                WHERE user_id = %s
            """
            cursor.execute(user_query, (user_id,))
            user_data = cursor.fetchone()
            logger.info(f"User data retrieved: {user_data}")
            
            saved_query = """
                SELECT m.*
                FROM MovieUsers mu
                JOIN Movies m ON mu.movie_id = m.movie_id
                WHERE mu.user_id = %s AND mu.saved = 1
                ORDER BY m.movie_id DESC
                LIMIT 10
            """
            cursor.execute(saved_query, (user_id,))
            saved_movies = cursor.fetchall()
            
            rated_query = """
                SELECT m.*, mu.note
                FROM MovieUsers mu
                JOIN Movies m ON mu.movie_id = m.movie_id
                WHERE mu.user_id = %s AND mu.note IS NOT NULL
                ORDER BY m.movie_id DESC
                LIMIT 10
            """
            cursor.execute(rated_query, (user_id,))
            rated_movies = cursor.fetchall()
            logger.info(f"Found {len(rated_movies)} rated movies for user {user_id}")
            
            if not rated_movies:
                debug_query = "SELECT COUNT(*) as count FROM MovieUsers WHERE user_id = %s"
                cursor.execute(debug_query, (user_id,))
                user_count = cursor.fetchone()
                logger.info(f"User {user_id} has {user_count['count']} total entries in MovieUsers table")
                
                if user_count['count'] == 0:
                    logger.info(f"Adding test data for user {user_id}")
                    test_insert = """
                        INSERT INTO MovieUsers (movie_id, user_id, note, saved) 
                        VALUES (13, %s, 5, 0), (745, %s, 4, 0)
                        ON DUPLICATE KEY UPDATE note = VALUES(note)
                    """
                    cursor.execute(test_insert, (user_id, user_id))
                    connection.commit()
                    
                    cursor.execute(rated_query, (user_id,))
                    rated_movies = cursor.fetchall()
                    logger.info(f"After adding test data: Found {len(rated_movies)} rated movies")
            
            count_query = """
                SELECT 
                    COUNT(CASE WHEN note IS NOT NULL THEN 1 END) as total_ratings,
                    COUNT(CASE WHEN saved = 1 THEN 1 END) as total_saved
                FROM MovieUsers
                WHERE user_id = %s
            """
            cursor.execute(count_query, (user_id,))
            counts = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            display_name = request.session.get('username', 'User')
            if user_data and (user_data['prenom'] or user_data['nom']):
                if user_data['prenom'] and user_data['nom']:
                    display_name = f"{user_data['prenom']} {user_data['nom']}"
                elif user_data['prenom']:
                    display_name = user_data['prenom']
                elif user_data['nom']:
                    display_name = user_data['nom']
            
            context = {
                'username': display_name,
                'user_data': user_data,
                'saved_movies': saved_movies,
                'rated_movies': rated_movies,
                'total_ratings': counts['total_ratings'] if counts else 0,
                'total_saved': counts['total_saved'] if counts else 0,
            }
            
            return render(request, 'users/profile.html', context)
            
    except Error as e:
        logger.error(f"Database error in profile_view: {e}")
        
    return render(request, 'users/profile.html', {
        'username': request.session.get('username', 'User'),
        'saved_movies': [],
        'rated_movies': [],
        'total_ratings': 0,
        'total_saved': 0,
    })


def get_profile_data(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)
    
    if 'access_token' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user_id = request.session.get('user_id')
    if not user_id:
        access_token = request.session.get('access_token')
        if access_token:
            user_id = get_user_id_from_api(access_token)
            if user_id:
                request.session['user_id'] = user_id
    
    if not user_id:
        return JsonResponse({'error': 'User not found'}, status=401)
    
    try:
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword',
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            user_query = """
                SELECT user_id, nom, prenom, birthday, sexe, email
                FROM Users
                WHERE user_id = %s
            """
            cursor.execute(user_query, (user_id,))
            user_data = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if user_data:
                if user_data['birthday']:
                    user_data['birthday'] = user_data['birthday'].strftime('%Y-%m-%d')
                return JsonResponse(user_data)
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
                
    except Error as e:
        logger.error(f"Database error in get_profile_data: {e}")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in get_profile_data: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@csrf_protect
def update_profile(request):
    logger.info(f"update_profile called with method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Session keys: {list(request.session.keys())}")
    
    if request.method != 'POST':
        logger.error(f"Invalid method: {request.method}")
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if 'access_token' not in request.session:
        logger.error("No access_token in session")
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user_id = request.session.get('user_id')
    if not user_id:
        access_token = request.session.get('access_token')
        if access_token:
            user_id = get_user_id_from_api(access_token)
            if user_id:
                request.session['user_id'] = user_id
    
    if not user_id:
        return JsonResponse({'error': 'User not found'}, status=401)
    
    try:
        logger.info(f"Request body: {request.body}")
        data = json.loads(request.body)
        logger.info(f"Parsed data: {data}")
        
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword',
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            update_query = """
                UPDATE Users 
                SET nom = %s, prenom = %s, birthday = %s, sexe = %s
                WHERE user_id = %s
            """
            
            values = (
                data.get('nom'),
                data.get('prenom'),
                data.get('birthday') if data.get('birthday') else None,
                data.get('sexe'),
                user_id
            )
            
            logger.info(f"Executing update with values: {values}")
            cursor.execute(update_query, values)
            
            verify_query = "SELECT nom, prenom, birthday, sexe FROM Users WHERE user_id = %s"
            cursor.execute(verify_query, (user_id,))
            updated_data = cursor.fetchone()
            logger.info(f"Updated data verification: {updated_data}")
            
            cursor.close()
            connection.close()
            
            request.session['user_prenom'] = data.get('prenom')
            request.session['user_nom'] = data.get('nom')
            
            logger.info("Profile updated successfully")
            response = JsonResponse({'success': True, 'message': 'Profile updated successfully'})
            logger.info(f"Returning JSON response: {response}")
            return response
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in update_profile: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Error as e:
        logger.error(f"Database error in update_profile: {e}")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in update_profile: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'Server error'}, status=500)


@csrf_protect
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if 'access_token' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user_id = request.session.get('user_id')
    if not user_id:
        access_token = request.session.get('access_token')
        if access_token:
            user_id = get_user_id_from_api(access_token)
            if user_id:
                request.session['user_id'] = user_id
    
    if not user_id:
        return JsonResponse({'error': 'User not found'}, status=401)
    
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return JsonResponse({'error': 'Current and new passwords required'}, status=400)
        
        connection = mysql.connector.connect(
            host='mariadb',
            database='moviemania',
            user='root',
            password='rootpassword',
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            get_password_query = "SELECT password FROM Users WHERE user_id = %s"
            cursor.execute(get_password_query, (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            if not bcrypt.checkpw(current_password.encode('utf-8'), user_data['password'].encode('utf-8')):
                return JsonResponse({'error': 'Current password is incorrect'}, status=400)
            
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            update_password_query = "UPDATE Users SET password = %s WHERE user_id = %s"
            cursor.execute(update_password_query, (new_password_hash, user_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return JsonResponse({'success': True, 'message': 'Password changed successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Error as e:
        logger.error(f"Database error in change_password: {e}")
        return JsonResponse({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in change_password: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)




