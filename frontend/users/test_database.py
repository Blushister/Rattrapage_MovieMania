import json
import unittest.mock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
import mysql.connector
import datetime


class DatabaseViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Set up authenticated session
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()

    @patch('users.views.mysql.connector.connect')
    def test_get_movie_details_success(self, mock_connect):
        """Test successful movie details retrieval"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock movie data
        mock_cursor.fetchone.side_effect = [
            {  # Movie data
                'movie_id': 1,
                'title': 'Test Movie',
                'overview': 'Test overview',
                'poster_path': '/test.jpg',
                'backdrop_path': '/test_bg.jpg',
                'release_date': datetime.date(2023, 1, 1),
                'runtime': 120,
                'vote_average': 7.5,
                'vote_count': 1000,
                'budget': 1000000,
                'revenue': 2000000,
                'tagline': 'Test tagline',
                'genres': 'Action,Comedy'
            },
            {'note': 4}  # User rating
        ]
        
        # Mock cast and crew data
        mock_cursor.fetchall.side_effect = [
            [  # Cast
                {
                    'name': 'Actor One',
                    'photo': '/actor1.jpg',
                    'character_name': 'Character 1',
                    'cast_order': 0
                }
            ],
            [  # Crew
                {
                    'name': 'Director One',
                    'photo': '/director1.jpg',
                    'job': 'Director'
                }
            ]
        ]
        
        url = reverse('users:movie_details', args=[1])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['movie']['title'], 'Test Movie')
        self.assertEqual(data['movie']['user_rating'], 4)
        self.assertEqual(len(data['cast']), 1)
        self.assertEqual(len(data['crew']), 1)

    def test_get_movie_details_unauthenticated(self):
        """Test movie details access without authentication"""
        # Clear session
        self.client.session.flush()
        
        url = reverse('users:movie_details', args=[1])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Not authenticated')

    @patch('users.views.mysql.connector.connect')
    def test_get_movie_details_not_found(self, mock_connect):
        """Test movie details for non-existent movie"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock no movie found
        mock_cursor.fetchone.return_value = None
        
        url = reverse('users:movie_details', args=[999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Movie not found')

    @patch('users.views.mysql.connector.connect')
    def test_rate_movie_success(self, mock_connect):
        """Test successful movie rating"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        url = reverse('users:rate_movie')
        response = self.client.post(
            url,
            json.dumps({'movie_id': 1, 'rating': 5}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Rating saved successfully')
        
        # Verify database call
        mock_cursor.execute.assert_called()

    def test_rate_movie_invalid_rating(self):
        """Test movie rating with invalid rating value"""
        url = reverse('users:rate_movie')
        response = self.client.post(
            url,
            json.dumps({'movie_id': 1, 'rating': 6}),  # Rating > 5
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Rating must be between 1 and 5')

    def test_rate_movie_missing_data(self):
        """Test movie rating with missing data"""
        url = reverse('users:rate_movie')
        response = self.client.post(
            url,
            json.dumps({'movie_id': 1}),  # Missing rating
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'movie_id and rating required')

    def test_rate_movie_get_method(self):
        """Test movie rating with GET method (should fail)"""
        url = reverse('users:rate_movie')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'POST method required')

    @patch('users.views.mysql.connector.connect')
    def test_profile_view_success(self, mock_connect):
        """Test successful profile view"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock user data - side_effect pour les 2 appels fetchone
        mock_cursor.fetchone.side_effect = [
            {  # User data (1er appel)
                'nom': 'Doe',
                'prenom': 'John', 
                'email': 'john@example.com',
                'birthday': '1990-01-01',
                'sexe': 'M'
            },
            {  # Counts data (2ème appel)
                'total_ratings': 1,
                'total_saved': 0
            },
            None  # Sécurité pour appels supplémentaires
        ]
        
        mock_cursor.fetchall.return_value = [    # Rated movies (not empty to avoid the count issue)
            {
                'movie_id': 1,
                'title': 'Rated Movie',
                'poster_path': '/rated.jpg',
                'note': 4
            }
        ]
        
        url = reverse('users:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')  # Display name
        self.assertContains(response, 'Rated Movie')

    @patch('users.views.mysql.connector.connect')
    def test_get_profile_data_success(self, mock_connect):
        """Test successful profile data API"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        from datetime import date
        mock_cursor.fetchone.return_value = {
            'user_id': 123,
            'nom': 'Doe',
            'prenom': 'John',
            'email': 'john@example.com',
            'birthday': date(1990, 1, 1),
            'sexe': 'M'
        }
        
        url = reverse('users:profile_data')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['prenom'], 'John')
        self.assertEqual(data['nom'], 'Doe')
        self.assertEqual(data['birthday'], '1990-01-01')

    @patch('users.views.mysql.connector.connect')
    def test_update_profile_success(self, mock_connect):
        """Test successful profile update"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = ('Updated', 'John', '1990-01-01', 'M')
        
        url = reverse('users:update_profile')
        response = self.client.post(
            url,
            json.dumps({
                'nom': 'Updated',
                'prenom': 'John',
                'birthday': '1990-01-01',
                'sexe': 'M'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Profile updated successfully')
        
        # Check session was updated
        self.assertEqual(self.client.session['user_prenom'], 'John')
        self.assertEqual(self.client.session['user_nom'], 'Updated')

    @patch('users.views.mysql.connector.connect')
    @patch('users.views.bcrypt.checkpw')
    @patch('users.views.bcrypt.hashpw')
    def test_change_password_success(self, mock_hashpw, mock_checkpw, mock_connect):
        """Test successful password change"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock password verification and hashing
        mock_cursor.fetchone.return_value = {'password': 'old_hash'}
        mock_checkpw.return_value = True
        mock_hashpw.return_value = b'new_hash'
        
        url = reverse('users:change_password')
        response = self.client.post(
            url,
            json.dumps({
                'current_password': 'oldpass',
                'new_password': 'newpass'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Password changed successfully')

    @patch('users.views.mysql.connector.connect')
    @patch('users.views.bcrypt.checkpw')
    def test_change_password_wrong_current(self, mock_checkpw, mock_connect):
        """Test password change with wrong current password"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'password': 'old_hash'}
        mock_checkpw.return_value = False  # Wrong password
        
        url = reverse('users:change_password')
        response = self.client.post(
            url,
            json.dumps({
                'current_password': 'wrongpass',
                'new_password': 'newpass'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Current password is incorrect')


class DatabaseUtilsTestCase(TestCase):
    """Test database utility functions"""
    
    @patch('users.views.mysql.connector.connect')
    def test_get_genres_from_db_success(self, mock_connect):
        """Test successful genre retrieval"""
        from users.views import get_genres_from_db
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {'genre_id': 1, 'name': 'Action'},
            {'genre_id': 2, 'name': 'Comedy'}
        ]
        
        genres = get_genres_from_db()
        
        self.assertEqual(len(genres), 2)
        self.assertEqual(genres[0]['name'], 'Action')
        self.assertEqual(genres[1]['name'], 'Comedy')

    @patch('users.views.mysql.connector.connect')
    def test_get_genres_from_db_error(self, mock_connect):
        """Test genre retrieval with database error"""
        from users.views import get_genres_from_db
        
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        genres = get_genres_from_db()
        
        self.assertEqual(genres, [])

    @patch('users.views.requests.get')
    def test_get_user_id_from_api_success(self, mock_get):
        """Test successful user ID retrieval from API"""
        from users.views import get_user_id_from_api
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'id': 123}
        
        user_id = get_user_id_from_api('test_token')
        
        self.assertEqual(user_id, 123)
        mock_get.assert_called_with(
            f"{settings.USERS_API_URL}/me",
            headers={'Authorization': 'Bearer test_token'}
        )

    @patch('users.views.requests.get')
    def test_get_user_id_from_api_error(self, mock_get):
        """Test user ID retrieval with API error"""
        from users.views import get_user_id_from_api
        
        mock_get.return_value.status_code = 401
        
        user_id = get_user_id_from_api('invalid_token')
        
        self.assertIsNone(user_id)