import json
import unittest.mock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
import requests


class AuthenticationViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('users:login')
        self.register_url = reverse('users:register')
        self.logout_url = reverse('users:logout')
        self.home_url = reverse('users:home')

    def test_login_view_get(self):
        """Test GET request to login view"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connexion')

    def test_login_view_redirect_authenticated(self):
        """Test redirect if user is already authenticated"""
        session = self.client.session
        session['access_token'] = 'fake_token'
        session.save()
        
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    def test_login_successful(self, mock_get, mock_post):
        """Test successful login"""
        # Mock login API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'user_id': 123
        }
        
        # Mock user data API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'test@example.com',
            'prenom': 'John',
            'nom': 'Doe'
        }
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

    @patch('users.views.requests.post')
    def test_login_invalid_credentials(self, mock_post):
        """Test login with invalid credentials"""
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {'detail': 'Invalid credentials'}
        mock_post.return_value.content = b'{"detail": "Invalid credentials"}'
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])

    def test_logout_post(self):
        """Test POST logout"""
        # Set session data
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()
        
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

    def test_home_view_authenticated(self):
        """Test home view with authenticated user"""
        session = self.client.session
        session['access_token'] = 'test_token'
        session.save()
        
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_unauthenticated(self):
        """Test home view redirects when not authenticated"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)

    def test_api_config_returns_json(self):
        """Test API config returns correct JSON"""
        response = self.client.get(reverse('users:api_config'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


class DatabaseViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Set up authenticated session
        session = self.client.session
        session['access_token'] = 'test_token'
        session['user_id'] = 123
        session.save()

    def test_get_movie_details_unauthenticated(self):
        """Test movie details access without authentication"""
        # Clear session
        self.client.session.flush()
        
        url = reverse('users:movie_details', args=[1])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Not authenticated')

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


class FormValidationTestCase(TestCase):
    """Test form validation logic"""
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = ['test@example.com', 'user.name@domain.co.uk', 'test123@test.org']
        invalid_emails = ['invalid-email', 'test@', '@domain.com', '']
        
        for email in valid_emails:
            response = self.client.post(reverse('users:login'), {
                'email': email,
                'password': 'validpass123'
            })
            # Should not fail due to email format (may fail due to other reasons)
            self.assertNotEqual(response.status_code, 400)
            
    def test_password_requirements(self):
        """Test password requirements in registration"""
        # Test with insufficient genres (should fail before password validation)
        response = self.client.post(reverse('users:register'), {
            'email': 'test@example.com',
            'password': 'weak',
            'genres': ['1', '2']  # Insufficient genres
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class SessionTestCase(TestCase):
    """Test session handling"""
    
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

    def test_session_cleanup_on_logout(self):
        """Test session is properly cleaned on logout"""
        # Set session data
        session = self.client.session
        session['access_token'] = 'token_to_clear'
        session['user_id'] = 123
        session.save()
        
        # Logout
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)
        
        # Check session data is cleared
        self.assertNotIn('access_token', self.client.session)

    def test_unauthorized_access_redirects(self):
        """Test unauthorized access to protected views"""
        protected_urls = [
            reverse('users:home'),
            reverse('users:profile'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login or return 401
            self.assertIn(response.status_code, [302, 401])


class ErrorHandlingTestCase(TestCase):
    """Test error handling"""
    
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

    def test_method_not_allowed(self):
        """Test method not allowed responses"""
        # Try GET on POST-only endpoint
        response = self.client.get(reverse('users:rate_movie'))
        
        self.assertEqual(response.status_code, 405)


class IntegrationTestCase(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.client = Client()

    @patch('users.views.get_genres_from_db')
    def test_registration_page_loads(self, mock_genres):
        """Test registration page loads with genres"""
        mock_genres.return_value = [
            {'genre_id': 1, 'name': 'Action'},
            {'genre_id': 2, 'name': 'Comedy'}
        ]
        
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Action')

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    def test_login_flow(self, mock_get, mock_post):
        """Test complete login flow"""
        # Mock API responses
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
        
        # Step 1: Login
        response = self.client.post(reverse('users:login'), {
            'email': 'user@test.com',
            'password': 'userpass123'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Step 2: Access protected page
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Logout
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


class UtilityFunctionTestCase(TestCase):
    """Test utility functions"""
    
    @patch('users.views.requests.get')
    def test_get_user_id_from_api_success(self, mock_get):
        """Test successful user ID retrieval from API"""
        from users.views import get_user_id_from_api
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'id': 123}
        
        user_id = get_user_id_from_api('test_token')
        self.assertEqual(user_id, 123)

    @patch('users.views.requests.get')
    def test_get_user_id_from_api_error(self, mock_get):
        """Test user ID retrieval with API error"""
        from users.views import get_user_id_from_api
        
        mock_get.return_value.status_code = 401
        
        user_id = get_user_id_from_api('invalid_token')
        self.assertIsNone(user_id)

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