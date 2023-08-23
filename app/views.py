from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import math
import json
import random
from django.db import models
from .models import game
from .models import court
from datetime import datetime
from datetime import date
from django.db.models import F
from django.contrib.auth.hashers import make_password, check_password
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import history

channel_layer = get_channel_layer()

# Set up logging
logger = logging.getLogger(__name__)


@csrf_exempt
def login(request):
    """
    Handles user login.
    """
    if request.method != 'POST':
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Method not allowed"
        }, status=405)  # HTTP 405 Method Not Allowed

    try:
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username and password are required"
            }, status=400)  # HTTP 400 Bad Request

        user = game.objects.filter(user_name=username).first()

        if user and check_password(password, user.password):
            logger.info(f"Successful login attempt for {username}")
            return JsonResponse({
                "responseCode": 0,
                "responseMessage": "Login successful",
                "userName": username
            })

        logger.warning(f"Invalid login attempt for {username}")
        return JsonResponse({
            "responseCode": 1,
            "responseMessage": "Invalid username or password"
        }, status=401)  # HTTP 401 Unauthorized

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON request body")
        return JsonResponse({
            "responseCode": 5,
            "responseMessage": "Malformed request"
        }, status=400)  # HTTP 400 Bad Request

    except Exception as e:
        logger.error(f"Login error: {e}")
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Internal server error"
        }, status=500)  # HTTP 500 Internal Server Error


@csrf_exempt
def signup(request):
    """
    Handles user signup.
    """
    if request.method != 'POST':
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Method not allowed"
        }, status=405)  # HTTP 405 Method Not Allowed

    try:
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username and password are required"
            }, status=400)  # HTTP 400 Bad Request

        if game.objects.filter(user_name=username).exists():
            logger.warning(f"Signup attempt with existing username: {username}")
            return JsonResponse({
                "responseCode": 1,
                "responseMessage": "Nickname already exists"
            }, status=409)  # HTTP 409 Conflict

        hashed_password = make_password(password)

        new_user = game(
            user_name=username,
            password=hashed_password,
            # You can add any additional fields here that are required for the new user
        )
        new_user.save()

        logger.info(f"New user signup: {username}")
        return JsonResponse({
            "responseCode": 0,
            "responseMessage": "Signup successful"
        })

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON request body during signup")
        return JsonResponse({
            "responseCode": 5,
            "responseMessage": "Malformed request"
        }, status=400)  # HTTP 400 Bad Request

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Internal server error"
        }, status=500)  # HTTP 500 Internal Server Error


@csrf_exempt
def fetch_active_players(request):
    """
    Fetch active players.
    """
    if request.method != 'GET':
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Method not allowed"
        }, status=405)  # HTTP 405 Method Not Allowed

    try:
        # Fetch all players with the "active" status and "playing" status as "N"
        available_players = game.objects.filter(status="active", playing="N")
        # Get the count of active players
        active_players_count = available_players.count()

        # Send WebSocket message
        async_to_sync(channel_layer.group_send)(
            'updates_group',
            {
                'type': 'send_update',
                'message': {
                    'updateType': 'active_players',
                    # This can be the updated list of active players or a count
                    'data': active_players_count
                }
            }
        )

        logger.info("Active players fetched successfully.")
        return JsonResponse({
            "responseCode": 0,
            "responseMessage": "Active players fetched successfully.",
            "activePlayersCount": active_players_count  # Include the count in the response
        })

    except Exception as e:
        logger.error(f"Error occurred during fetching active players: {e}")
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Error occurred during fetching active players."
        }, status=500)  # HTTP 500 Internal Server Error


@csrf_exempt
def add_to_pool(request):
    """
    Adds a user to the pool.
    """
    if request.method != 'POST':
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Method not allowed"
        }, status=405)  # HTTP 405 Method Not Allowed

    try:
        data = json.loads(request.body)
        user_name = data.get('userName')

        if not user_name:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username is required"
            }, status=400)  # HTTP 400 Bad Request

        user = game.objects.get(user_name=user_name)

        # Update the status to "active"
        user.status = "active"
        user.save()

        logger.info(f"Added user {user_name} to pool successfully.")
        return JsonResponse({
            "responseCode": 0,
            "responseMessage": "ADD_TO_POOL_SUCCESS"
        })

    except game.DoesNotExist:
        logger.warning(f"Attempt to add nonexistent user {user_name} to pool.")
        return JsonResponse({
            "responseCode": 5,
            "responseMessage": "User does not exist"
        }, status=404)  # HTTP 404 Not Found

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON request body during add_to_pool.")
        return JsonResponse({
            "responseCode": 1,
            "responseMessage": "ADD_TO_POOL_ERROR"
        }, status=400)  # HTTP 400 Bad Request

    except Exception as e:
        logger.error(f"Unexpected error during add_to_pool: {e}")
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Internal server error"
        }, status=500)  # HTTP 500 Internal Server Error


@csrf_exempt
def remove_from_pool(request):
    """
    Removes a user from the pool.
    """
    if request.method != 'POST':
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Method not allowed"
        }, status=405)  # HTTP 405 Method Not Allowed

    try:
        data = json.loads(request.body)
        user_name = data.get('userName')

        if not user_name:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username is required"
            }, status=400)  # HTTP 400 Bad Request

        user = game.objects.get(user_name=user_name)

        # Update the status to "inactive"
        user.status = "inactive"
        user.unmatched_priority = 0
        user.save()

        logger.info(f"Removed user {user_name} from pool successfully.")
        return JsonResponse({
            "responseCode": 0,
            "responseMessage": "REMOVE_FROM_POOL_SUCCESS"
        })

    except game.DoesNotExist:
        logger.warning(f"Attempt to remove nonexistent user {user_name} from pool.")
        return JsonResponse({
            "responseCode": 5,
            "responseMessage": "User does not exist"
        }, status=404)  # HTTP 404 Not Found

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON request body during remove_from_pool.")
        return JsonResponse({
            "responseCode": 1,
            "responseMessage": "REMOVE_FROM_POOL_ERROR"
        }, status=400)  # HTTP 400 Bad Request

    except Exception as e:
        logger.error(f"Unexpected error during remove_from_pool: {e}")
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Internal server error"
        }, status=500)  # HTTP 500 Internal Server Error


def fetch_court_status():
    """
    Fetch the status of all courts in the system.
    Returns a dictionary with court keys and their respective name and status.
    """
    all_courts = court.objects.all()
    return {
        f'court{c.id}': {
            "name": c.court_name,
            "status": c.status,
        } for c in all_courts
    }


def select_player(sorted_players, team):
    for player in sorted_players:
        if not any([p in team for p in history.objects.filter(player1=player).values_list('player2', flat=True)]) and \
           not any([p in team for p in history.objects.filter(player2=player).values_list('player1', flat=True)]):
            return player
    return sorted_players[0]  # Return the top-ranked player if no unmatched player is found

def generate_pairing():
    try:
        available_players = game.objects.filter(status="active", playing="N")
        if len(available_players) < 4:
            return {"responseCode": 1, "responseMessage": "Not enough players for matches."}

        # Sorting and pairing logic
        sorted_players = sorted(available_players, key=lambda p: (-p.unmatched_priority, -p.uncertainty, p.elo_rating))
        pairings, selected_players = [], []
        for _ in range(1):  # Create four pairings for four matches
            team1, team2 = [], []
            for _ in range(2):
                player = select_player(sorted_players, team1)
                team1.append(player)
                sorted_players.remove(player)
            for _ in range(2):
                player = select_player(sorted_players, team2)
                team2.append(player)
                sorted_players.remove(player)
            pairings.append((team1, team2))
            selected_players.extend(team1 + team2)

        # Updating players' status and history in DB
        game.objects.filter(pk__in=[player.pk for player in selected_players]).update(playing="Y")
        game.objects.filter(pk__in=[player.pk for player in sorted_players]).update(unmatched_priority=F('unmatched_priority') + 1)
        game.objects.filter(pk__in=[player.pk for player in selected_players]).update(unmatched_priority=0)
        
        # Update pairing history
        today = date.today()
        for team in pairings:
            for player1 in team[0]:
                for player2 in team[1]:
                    # Check if the pairing already exists
                    already_exists = history.objects.filter(
                        models.Q(player1=player1, player2=player2) |
                        models.Q(player1=player2, player2=player1)
                    ).exists()

                    if not already_exists or len(available_players) == 4:
                        history.objects.create(player1=player1, player2=player2, date=today)


        # Formatting teams
        teams = [
            {
                'team1': [{'userName': player.user_name, 'elo': player.elo_rating, 'uncertainty': player.uncertainty}
                          for player in team[0]],
                'team2': [{'userName': player.user_name, 'elo': player.elo_rating, 'uncertainty': player.uncertainty}
                          for player in team[1]]
            }
            for team in pairings
        ]

        # Court logic
        available_courts = court.objects.filter(status=True).order_by('id')
        first_available_court = available_courts.first()
        first_available_court_key = f'court{first_available_court.id}' if first_available_court else None
        if first_available_court:
            first_available_court.status = False
            first_available_court.save()

        court_status = fetch_court_status()

        # Prepare response
        response_data = {
            "responseCode": 0,
            "responseMessage": "Pairing generated successfully.",
            "teams": teams,
            "courtStatus": court_status,
            "firstAvailableCourt": first_available_court_key
        }

        # Send WebSocket messages
        async_to_sync(channel_layer.group_send)('updates_group', {'type': 'send_update', 'message': {'updateType': 'court_status', 'data': court_status}})
        async_to_sync(channel_layer.group_send)('updates_group', {'type': 'send_update', 'message': {'updateType': 'teams', 'data': response_data}})

        return response_data

    except Exception as e:
        logger.error(f"Error during pairing generation: {e}")
        return {"responseCode": 2, "responseMessage": "Error occurred during pairing generation."}


@csrf_exempt
def update_elo(request):
    try:
        # Load the JSON data from the request
        data = json.loads(request.body)
        teamDetails = data.get('teamDetails')

        winners = teamDetails['winner']
        losers = teamDetails['loser']
        court_name = teamDetails['court']

        print(court_name)

        # K factor
        K = 30
        # Factors for tuning uncertainty
        F1 = 30
        F2 = 180

        # Updated details dictionary
        updated_details = {}

        # Calculate average rating for winners and losers
        winner_avg_rating = sum([game.objects.get(
            user_name=winner['userName']).elo_rating for winner in winners]) / len(winners)
        loser_avg_rating = sum([game.objects.get(
            user_name=loser['userName']).elo_rating for loser in losers]) / len(losers)

        # Calculate expected score
        expected_winner = 1 / \
            (1 + 10 ** ((loser_avg_rating - winner_avg_rating) / 400))
        expected_loser = 1 - expected_winner

        # Function to handle updating players
        def handle_players(team, outcome, expected_outcome):
            for player in team:
                user = game.objects.get(user_name=player['userName'])
                rating_change = round(
                    user.elo_rating + K * (outcome - expected_outcome)) - user.elo_rating

                # Update rating changes
                rating_changes_str = user.rating_changes or ""
                user.rating_changes = ",".join(
                    filter(None, [rating_changes_str, str(rating_change)]))

                # Update ELO rating
                user.elo_rating += rating_change
                user.status = "inactive"
                user.playing = 'N'
                user.played += 1
                user.won += outcome
                user.lost += 1 - outcome

                # Calculate Standard Deviation
                rating_changes_list = [
                    int(x) for x in user.rating_changes.split(",") if x]
                sd_factor = 1 + (math.sqrt(sum([(x - sum(rating_changes_list)/len(rating_changes_list))
                                                ** 2 for x in rating_changes_list]) / len(rating_changes_list)) if rating_changes_list else 0)/F1

                # Time Decay Factor
                days_since_last_game = (datetime.now().date() -
                                        (user.last_played or datetime.now().date())).days
                decay_factor = 1 + days_since_last_game/F2

                # Combine with base uncertainty
                base_uncertainty = max(0.05, 1 - user.played / 100)
                user.uncertainty = min(
                    1, max(0.05, base_uncertainty * sd_factor * decay_factor))

                # Update last played date
                user.last_played = datetime.now().date()
                user.save()

                # Fetch the court by its name
                court_to_update = court.objects.get(court_name=court_name)

                # Update the status to True
                court_to_update.status = True

                # Save the changes to the database
                court_to_update.save()

                # Add the updated details of the user to the response
                updated_details[user.user_name] = {
                    "eloRating": user.elo_rating,
                    "ratingDiff": rating_change,
                    "result": outcome
                }

                # Send WebSocket message
                async_to_sync(channel_layer.group_send)(
                'updates_group',
                {
                    'type': 'send_update',
                    'message': {
                        'updateType': 'updatedDetailsModal',
                        'data': updated_details
                    }
                })

        # Update ratings for winners
        handle_players(winners, 1, expected_winner)

        # Update ratings for losers
        handle_players(losers, 0, expected_loser)

        return JsonResponse({'responseCode': 0, "responseMessage": "UPDATE ELO SUCCESS", "updatedDetails": updated_details})

    except Exception as e:
        # Handle any exceptions that may occur during pairing generation
        print("Error:", e)
        return JsonResponse({"responseCode": 2, "responseMessage": "UPDATE ELO ERROR"})

@csrf_exempt
def reset_database(request):
    try:

        all_players = game.objects.all()

        # Loop through available players and reset their attributes to default values
        for player in all_players:
            player.elo_rating = 1500  # Assuming default ELO rating is 1500
            player.playing = 'N'
            player.status = "inactive"
            player.played = 0
            player.won = 0
            player.lost = 0
            player.uncertainty = 1
            player.last_played = ""
            player.rating_changes = ""
            player.unmatched_priority = 0
            # Reset any other attributes as needed
            player.save()

        response_data = {
            "responseCode": 0,
            "responseMessage": "Reset Successful"
        }
        return JsonResponse(response_data, safe=False)

    except Exception as e:
        # Handle any exceptions that may occur during fetching active players
        print("Error:", e)
        return JsonResponse({"responseCode": 2, "responseMessage": "Reset Error"})


@csrf_exempt
def get_court_status(request):
    try:
        court_status = fetch_court_status()

        response_data = {
            "responseCode": 0,
            "responseMessage": "Reset Successful",
            "courtStatus": court_status
        }
        return JsonResponse(response_data, safe=False)

    except Exception as e:
        # Handle any exceptions that may occur during fetching active players
        print("Error:", e)
        return JsonResponse({"responseCode": 1, "responseMessage": "Reset Error"})


@csrf_exempt
def navigate_to_court_screen(request):
    try:

        data = json.loads(request.body)
        userName = data.get('userName')

        print(userName)

        court_status = fetch_court_status()

        async_to_sync(channel_layer.group_send)('updates_group', {'type': 'send_update', 'message': {'updateType': 'court_status', 'data': court_status}})

        # Send WebSocket message
        async_to_sync(channel_layer.group_send)(
            'updates_group',
            {
                'type': 'send_update',
                'message': {
                    'updateType': 'navigateBack',
                    'data': userName
                }
            })
        
        return JsonResponse({"responseCode": 0, "responseMessage": "Navigation Success"})

    except Exception as e:
        # Handle any exceptions that may occur during fetching active players
        print("Error:", e)
        return JsonResponse({"responseCode": 1, "responseMessage": "Navigation Error"})


@receiver(post_save, sender=game)
def player_joined(sender, instance, **kwargs):
    # Check the count of active players
    active_players = game.objects.filter(status="active").count()
    if active_players >= 4:
        generate_pairing()
