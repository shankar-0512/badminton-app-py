from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from .models import game,history,court  # assuming the model is in the same app
import json

class APITestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_username = "testuser"
        self.test_password = "abcde@123"

        # Create a test user for login tests
        hashed_password = make_password(self.test_password)
        game.objects.create(user_name=self.test_username, password=hashed_password)

    def test_login_valid_user(self):
        data = {
            'userName': self.test_username,
            'password': self.test_password
        }

        response = self.client.post('/app/login/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)

    def test_login_invalid_user(self):
        data = {
            'userName': 'nonexistentuser',
            'password': 'wrongpassword'
        }

        response = self.client.post('/app/login/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['responseCode'], 1)

    def test_signup_valid_data(self):
        data = {
            'userName': 'newuser',
            'password': 'newpass123'
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)

    def test_signup_existing_user(self):
        data = {
            'userName': self.test_username,
            'password': self.test_password
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['responseCode'], 1)

    def test_login_invalid_request(self):
        data = "This is not a valid json string."

        response = self.client.post('/app/login/', data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['responseCode'], 5)

    def test_signup_invalid_request(self):
        data = "This is not a valid json string."

        response = self.client.post('/app/signup/', data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['responseCode'], 5)


class PoolTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_username = "testuser"

        # Create a test user for the pool tests
        game.objects.create(user_name=self.test_username, status="inactive")

    def test_add_to_pool(self):
        data = {
            'userName': self.test_username
        }

        response = self.client.post('/app/addToPool/', json.dumps(data), content_type="application/json")
        user = game.objects.get(user_name=self.test_username)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        self.assertEqual(user.status, "active")

    def test_remove_from_pool(self):
        data = {
            'userName': self.test_username
        }

        response = self.client.post('/app/removeFromPool/', json.dumps(data), content_type="application/json")
        user = game.objects.get(user_name=self.test_username)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        self.assertEqual(user.status, "inactive")
        self.assertEqual(user.unmatched_priority, 0)

    def test_add_nonexistent_user_to_pool(self):
        data = {
            'userName': 'nonexistentuser'
        }

        response = self.client.post('/app/addToPool/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['responseCode'], 5)

    def test_remove_nonexistent_user_from_pool(self):
        data = {
            'userName': 'nonexistentuser'
        }

        response = self.client.post('/app/removeFromPool/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['responseCode'], 5)


class PlayerDataTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_username = "testuser"
        self.test_username_2 = "testuser2"

        # Create test users for the test cases
        game.objects.create(user_name=self.test_username, status="inactive", playing="N", elo_rating=1500, played=10, won=5, lost=5, rating_changes="10,-10,10,-10,10")
        game.objects.create(user_name=self.test_username_2, status="active", playing="N", elo_rating=1600, played=10, won=8, lost=2, rating_changes="10,10,-10,10,10")

    def test_fetch_active_players(self):

        response = self.client.get('/app/fetchActivePlayers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        self.assertEqual(response.json()['activePlayersCount'], 1)  # only testuser2 is active

    def test_fetch_user_data_valid_user(self):
        data = {
            'userName': self.test_username
        }

        response = self.client.post('/app/fetchUserDetails/', json.dumps(data), content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        expected_data = {
            "username": self.test_username,
            "currentRating": 1500,
            "played": 10,
            "won": 5,
            "lost": 5,
            "winPercentage": 50.0,
            "lastFiveGames": [10, -10, 10, -10, 10]
        }
        self.assertEqual(response.json()['userData'], expected_data)

    def test_fetch_user_data_nonexistent_user(self):
        data = {
            'userName': 'nonexistentuser'
        }

        response = self.client.post('/app/fetchUserDetails/', json.dumps(data), content_type="application/json")
        
        self.assertEqual(response.status_code, 200)  # Assuming you're returning 200 even for non-existent user for uniformity
        self.assertEqual(response.json()['responseCode'], 2)
