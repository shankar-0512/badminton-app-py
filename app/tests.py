from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from .models import game, court
import json
from app.views import generate_pairing
from django.db.models.signals import post_save

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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 1)

    def test_signup_valid_data(self):
        data = {
            'userName': 'newuser',
            'password': 'newpass123',
            'confirmPassword': 'newpass123'
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)

    def test_signup_existing_user(self):
        data = {
            'userName': self.test_username,
            'password': self.test_password,
            'confirmPassword': self.test_password
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 1)

    def test_signup_short_password(self):
        data = {
            'userName': 'newuser',
            'password': 'abc4',
            'confirmPassword': 'abc4'
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 7)

    def test_signup_passwords_do_not_match(self):
        data = {
            'userName': 'newuser',
            'password': 'abcd1234',
            'confirmPassword': 'abcd5678'
        }

        response = self.client.post('/app/signup/', json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 6)

    def test_login_invalid_request(self):
        data = "This is not a valid json string."

        response = self.client.post('/app/login/', data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 5)

    def test_signup_invalid_request(self):
        data = "This is not a valid json string."

        response = self.client.post('/app/signup/', data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
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

        game.objects.create(user_name=self.test_username, status="inactive", playing="N", elo_rating=1500, played=10, won=5, lost=5, rating_changes="10,-10,10,-10,10")
        game.objects.create(user_name=self.test_username_2, status="active", playing="N", elo_rating=1600, played=10, won=8, lost=2, rating_changes="10,10,-10,10,10")

    def test_fetch_active_players_get_method(self):
        response = self.client.get('/app/fetchActivePlayers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        self.assertEqual(response.json()['activePlayersCount'], 1)  # only testuser2 is active

    def test_fetch_active_players_non_get_method(self):
        response = self.client.post('/app/fetchActivePlayers/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['responseCode'], 3)
        
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)


class UpdateEloTestCase(TestCase):
    
    def setUp(self):
        game.objects.create(user_name='player1', elo_rating=1000)
        game.objects.create(user_name='player2', elo_rating=1000)
        game.objects.create(user_name='player3', elo_rating=1000)
        game.objects.create(user_name='player4', elo_rating=1000)

        court.objects.create(court_name='Court1', status=True)
        
    def test_successful_elo_update(self):
        payload = {
            'teamDetails': {
                'winner': [{'userName': 'player1'}, {'userName': 'player2'}],
                'loser': [{'userName': 'player3'}, {'userName': 'player4'}],
                'court': 'Court1'
            }
        }
        response = self.client.post('/app/updateElo/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 0)
        
    def test_invalid_json_payload(self):
        payload = "Invalid JSON"
        response = self.client.post('/app/updateElo/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)
        
    def test_missing_team_details(self):
        payload = {}
        response = self.client.post('/app/updateElo/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)

    def test_invalid_court_name(self):
        payload = {
            'teamDetails': {
                'winner': [{'userName': 'player1'}, {'userName': 'player2'}],
                'loser': [{'userName': 'player3'}, {'userName': 'player4'}],
                'court': 'InvalidCourt'
            }
        }
        response = self.client.post('/app/updateElo/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)

    def test_nonexistent_players(self):
        payload = {
            'teamDetails': {
                'winner': [{'userName': 'ghost1'}, {'userName': 'ghost2'}],
                'loser': [{'userName': 'player3'}, {'userName': 'player4'}],
                'court': 'Court1'
            }
        }
        response = self.client.post('/app/updateElo/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)

    def test_empty_players(self):
        payload = {
            'teamDetails': {
                'winner': [],
                'loser': [],
                'court': 'Court1'
            }
        }
        response = self.client.post('/app/updateElo/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['responseCode'], 2)


class GeneratePairingTestCase(TestCase):
    
    def setUp(self):
        game.objects.create(user_name='player1', elo_rating=1000, status="active", playing="N")
        game.objects.create(user_name='player2', elo_rating=1000, status="active", playing="N")
        game.objects.create(user_name='player3', elo_rating=1000, status="active", playing="N")
        game.objects.create(user_name='player4', elo_rating=1000, status="active", playing="N")
        court.objects.create(court_name='Court1', status=True)

    def test_less_than_four_active_players(self):
        game.objects.get(user_name='player1').delete()
        response = generate_pairing()
        self.assertEqual(response['responseCode'], 1)
    
    def test_exactly_four_active_players(self):
        response = generate_pairing()
        self.assertEqual(response['responseCode'], 0)
        
    def test_no_available_courts(self):
        court.objects.all().update(status=False)
        response = generate_pairing()
        self.assertEqual(response['responseCode'], 0)
        self.assertIsNone(response.get('firstAvailableCourt'))

    def test_available_courts(self):
        response = generate_pairing()
        self.assertEqual(response['responseCode'], 0)
        self.assertIsNotNone(response.get('firstAvailableCourt'))

    def test_player_joined_active_players_less_than_four(self):
        game.objects.all().delete()
        instance = game.objects.create(user_name='player6', status="active", playing="N")
        post_save.send(sender=game, instance=instance)
        self.assertEqual(game.objects.filter(playing='Y').count(), 0)

    def test_player_joined_active_players_four_or_more(self):
        instance = game.objects.create(user_name='player7', elo_rating=1000, status="active", playing="N")
        post_save.send(sender=game, instance=instance)
        self.assertEqual(game.objects.filter(playing='Y').count(), 4)

