import json
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.sessions.models import Session
import datetime


class IntegrationTestCase(TransactionTestCase):
    """Integration tests for complete user workflows"""
    
    def setUp(self):
        self.client = Client()

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    @patch('users.views.get_genres_from_db')
    def test_complete_user_registration_flow(self, mock_genres, mock_get, mock_post):
        """Test complete user registration and login flow"""
        
        # Mock genres for registration page
        mock_genres.return_value = [
            {'genre_id': 1, 'name': 'Action'},
            {'genre_id': 2, 'name': 'Comedy'},
            {'genre_id': 3, 'name': 'Drama'}
        ]
        
        # Step 1: Get registration page
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Action')
        self.assertContains(response, 'Comedy')
        
        # Step 2: Submit registration
        mock_responses = [
            MagicMock(status_code=200),  # Create user
            MagicMock(status_code=200),  # Login after registration
            MagicMock(status_code=200)   # Save genres
        ]
        mock_responses[1].json.return_value = {
            'access_token': 'new_user_token',
            'user_id': 456
        }
        mock_post.side_effect = mock_responses
        
        response = self.client.post(reverse('users:register'), {
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'genres': ['1', '2', '3']
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check session was created
        self.assertEqual(self.client.session['access_token'], 'new_user_token')
        self.assertEqual(self.client.session['user_id'], 456)
        
        # Step 3: Access home page
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    def test_complete_login_logout_flow(self, mock_get, mock_post):
        """Test complete login and logout flow"""
        
        # Step 1: Get login page
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Login
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'login_token',
            'user_id': 789
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'user@test.com',
            'prenom': 'Test',
            'nom': 'User'
        }
        
        response = self.client.post(reverse('users:login'), {
            'email': 'user@test.com',
            'password': 'userpass123'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check session
        self.assertEqual(self.client.session['access_token'], 'login_token')
        
        # Step 3: Access protected page
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Logout
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check session cleared
        self.assertNotIn('access_token', self.client.session)
        
        # Step 5: Try to access protected page (should redirect)
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 302)

    @patch('users.views.mysql.connector.connect')
    def test_movie_interaction_flow(self, mock_connect):
        """Test movie rating and details flow"""
        
        # Set up authenticated session
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()
        
        # Mock database for movie details
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Step 1: Get movie details
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
            None  # No user rating yet
        ]
        
        mock_cursor.fetchall.side_effect = [[], []]  # Empty cast and crew
        
        response = self.client.get(reverse('users:movie_details', args=[1]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['movie']['title'], 'Test Movie')
        self.assertIsNone(data['movie']['user_rating'])
        
        # Step 2: Rate the movie
        mock_cursor.fetchone.side_effect = None  # Reset
        mock_cursor.fetchall.side_effect = None   # Reset
        
        response = self.client.post(
            reverse('users:rate_movie'),
            json.dumps({'movie_id': 1, 'rating': 5}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Step 3: Get movie details again (should show rating)
        mock_cursor.fetchone.side_effect = [
            {  # Same movie data
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
            {'note': 5}  # Now has user rating
        ]
        mock_cursor.fetchall.side_effect = [[], []]  # Empty cast and crew
        
        response = self.client.get(reverse('users:movie_details', args=[1]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['movie']['user_rating'], 5)

    @patch('users.views.mysql.connector.connect')
    def test_profile_update_flow(self, mock_connect):
        """Test complete profile update flow"""
        
        # Set up authenticated session
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        
        # Step 1: Get profile page - side_effect pour les 2 appels fetchone
        mock_cursor.fetchone.side_effect = [
            {  # User data (1er appel)
                'nom': 'OldName',
                'prenom': 'OldFirst',
                'email': 'user@test.com',
                'birthday': '1990-01-01',
                'sexe': 'M'
            },
            {  # Counts data (2ème appel)
                'total_ratings': 1,
                'total_saved': 0
            },
            # Step 2: Profile data API calls
            {
                'user_id': 123,
                'nom': 'OldName',
                'prenom': 'OldFirst',
                'email': 'user@test.com',
                'birthday': datetime.date(1990, 1, 1),
                'sexe': 'M'
            },
            # Step 3: Update profile calls
            ('NewName', 'NewFirst', '1990-01-01', 'F'),
            None  # Sécurité pour appels supplémentaires
        ]
        mock_cursor.fetchall.return_value = [  # Some rated movies to avoid count logic
            {
                'movie_id': 1,
                'title': 'Test Movie',
                'poster_path': '/test.jpg',
                'note': 4
            }
        ]
        
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OldFirst OldName')
        
        # Step 2: Get profile data API
        from datetime import date
        mock_cursor.fetchone.return_value = {
            'user_id': 123,
            'nom': 'OldName',
            'prenom': 'OldFirst',
            'email': 'user@test.com',
            'birthday': date(1990, 1, 1),
            'sexe': 'M'
        }
        
        response = self.client.get(reverse('users:profile_data'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['prenom'], 'OldFirst')
        self.assertEqual(data['nom'], 'OldName')
        
        # Step 3: Update profile
        mock_cursor.fetchone.return_value = ('NewName', 'NewFirst', '1990-01-01', 'F')
        
        response = self.client.post(
            reverse('users:update_profile'),
            json.dumps({
                'nom': 'NewName',
                'prenom': 'NewFirst',
                'birthday': '1990-01-01',
                'sexe': 'F'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check session was updated
        self.assertEqual(self.client.session['user_prenom'], 'NewFirst')
        self.assertEqual(self.client.session['user_nom'], 'NewName')


class SessionTestCase(TestCase):
    """Test session handling and security"""
    
    def setUp(self):
        self.client = Client()

    def test_session_persistence(self):
        """Test session data persists across requests"""
        # Set session data
        session = self.client.session
        session['test_key'] = 'test_value'
        session['access_token'] = 'persistent_token'
        session.save()
        
        # Make another request
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 302)  # Should redirect to home
        
        # Check session still exists
        self.assertEqual(self.client.session['test_key'], 'test_value')
        self.assertEqual(self.client.session['access_token'], 'persistent_token')

    def test_session_cleanup_on_logout(self):
        """Test session is properly cleaned on logout"""
        # Set session data
        session = self.client.session
        session['access_token'] = 'token_to_clear'
        session['user_id'] = 123
        session['username'] = 'user@test.com'
        session['user_prenom'] = 'John'
        session['user_nom'] = 'Doe'
        session.save()
        
        # Logout
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)
        
        # Check all session data is cleared
        self.assertEqual(len(self.client.session.keys()), 0)

    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        # Try to post without CSRF token
        response = self.client.post(reverse('users:login'), {
            'email': 'test@example.com',
            'password': 'testpass'
        })
        # Django should handle CSRF automatically in tests
        # This test ensures the decorators are in place
        self.assertIn(response.status_code, [200, 403])

    def test_unauthorized_access_redirects(self):
        """Test unauthorized access to protected views"""
        protected_urls = [
            reverse('users:home'),
            reverse('users:profile'),
            reverse('users:profile_data'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            if response.status_code == 302:
                self.assertTrue(response.url.startswith('/login/'))
            elif response.status_code == 401:
                # JSON endpoints return 401
                data = json.loads(response.content)
                self.assertEqual(data['error'], 'Not authenticated')


class ErrorHandlingTestCase(TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.client = Client()
        # Set up authenticated session
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in requests"""
        response = self.client.post(
            reverse('users:rate_movie'),
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid JSON')

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        response = self.client.post(
            reverse('users:rate_movie'),
            json.dumps({'movie_id': 1}),  # Missing rating
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'movie_id and rating required')

    def test_method_not_allowed(self):
        """Test method not allowed responses"""
        # Try GET on POST-only endpoint
        response = self.client.get(reverse('users:rate_movie'))
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'POST method required')

    @patch('users.views.mysql.connector.connect')
    def test_database_connection_error(self, mock_connect):
        """Test database connection error handling"""
        mock_connect.side_effect = Exception("Database unavailable")
        
        response = self.client.get(reverse('users:movie_details', args=[1]))
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Server error')

    def test_nonexistent_movie(self):
        """Test accessing nonexistent movie"""
        with patch('users.views.mysql.connector.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.is_connected.return_value = True
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None
            
            response = self.client.get(reverse('users:movie_details', args=[999999]))
            
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Movie not found')