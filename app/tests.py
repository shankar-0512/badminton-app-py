from django.test import TestCase
from django.urls import reverse
from .models import game
from django.contrib.auth.hashers import make_password
import json

class LoginTestCase(TestCase):

    def setUp(self):
        # Create a user in the test database
        self.user_name = "testuser"
        self.password = "testpass123"
        hashed_password = make_password(self.password)
        game.objects.create(user_name=self.user_name, password=hashed_password)
        
        self.login_url = reverse('login')  # Assuming 'login' is the name you've given to your URL pattern for the login view

    def test_login_successful(self):
        data = {
            'userName': self.user_name,
            'password': self.password
        }

        response = self.client.post(self.login_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["responseCode"], 0)
        self.assertEqual(response_data["responseMessage"], "Login successful")

    def test_login_unsuccessful(self):
        data = {
            'userName': self.user_name,
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertEqual(response_data["responseCode"], 1)
        self.assertEqual(response_data["responseMessage"], "Invalid username or password")

    def test_malformed_json(self):
        response = self.client.post(self.login_url, 'this is not a json', content_type='application/json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data["responseCode"], 5)
        self.assertEqual(response_data["responseMessage"], "Malformed request")

    def test_missing_data(self):
        data = {
            'userName': self.user_name
            # 'password' is missing
        }

        response = self.client.post(self.login_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data["responseCode"], 4)
        self.assertEqual(response_data["responseMessage"], "Username and password are required")

    def test_invalid_http_method(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertEqual(response_data["responseCode"], 3)
        self.assertEqual(response_data["responseMessage"], "Method not allowed")
