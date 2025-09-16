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
        self.assertContains(response, 'form')

    def test_login_view_redirect_authenticated(self):
        """Test redirect if user is already authenticated"""
        session = self.client.session
        session['access_token'] = 'fake_token'
        session.save()
        
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/home/')

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
        
        # Mock user data API response (/me endpoint)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'user_id': 123,
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
        self.assertEqual(response_data['redirect'], '/home/')
        
        # Check session data
        session = self.client.session
        self.assertEqual(session['access_token'], 'test_token')
        self.assertEqual(session['user_id'], 123)
        self.assertEqual(session['username'], 'test@example.com')

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
        self.assertEqual(response_data['error'], 'Invalid credentials')

    @patch('users.views.requests.post')
    def test_login_api_connection_error(self, mock_post):
        """Test login when API is unreachable"""
        mock_post.side_effect = requests.RequestException("Connection error")
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass'
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Connection error.')

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
        
        # Check session is cleared
        self.assertNotIn('access_token', self.client.session)

    def test_logout_get_redirects(self):
        """Test GET logout redirects to login"""
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/')

    @patch('users.views.get_genres_from_db')
    def test_register_view_get(self, mock_get_genres):
        """Test GET request to register view"""
        mock_get_genres.return_value = [
            {'genre_id': 1, 'name': 'Action'},
            {'genre_id': 2, 'name': 'Comedy'}
        ]
        
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Action')
        self.assertContains(response, 'Comedy')

    def test_register_redirect_authenticated(self):
        """Test redirect if user is already authenticated"""
        session = self.client.session
        session['access_token'] = 'fake_token'
        session.save()
        
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/home/')

    @patch('users.views.requests.post')
    def test_register_successful(self, mock_post):
        """Test successful registration"""
        # Mock registration API call
        mock_responses = [
            MagicMock(status_code=200),  # Create user
            MagicMock(status_code=200),  # Login
            MagicMock(status_code=200)   # Save genres
        ]
        mock_responses[1].json.return_value = {
            'access_token': 'test_token',
            'user_id': 123
        }
        mock_post.side_effect = mock_responses
        
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password': 'newpass',
            'genres': ['1', '2', '3']
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['redirect'], '/home/')

    def test_register_insufficient_genres(self):
        """Test registration with insufficient genre selection"""
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password': 'newpass',
            'genres': ['1', '2']  # Only 2 genres, need 3
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Please select at least 3 genres.')

    def test_register_missing_fields(self):
        """Test registration with missing fields"""
        response = self.client.post(self.register_url, {
            'email': '',
            'password': 'newpass',
            'genres': ['1', '2', '3']
        })
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Email and password required.')


class HomeViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('users:home')

    def test_home_view_authenticated(self):
        """Test home view with authenticated user"""
        session = self.client.session
        session['access_token'] = 'test_token'
        session.save()
        
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'home-container')

    def test_home_view_unauthenticated(self):
        """Test home view redirects when not authenticated"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/')


class ApiConfigViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_config_url = reverse('users:api_config')

    def test_api_config_returns_json(self):
        """Test API config returns correct JSON"""
        response = self.client.get(self.api_config_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('recommendations_api_url', data)
        self.assertEqual(data['recommendations_api_url'], settings.RECOMMENDATIONS_API_URL)