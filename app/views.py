# Python standard libraries
import json
import math
import logging
from datetime import datetime, date

# Django core libraries
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password

# Django-related third-party libraries
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Application-specific modules
from .models import game, court, history

# Set up channel layer and logging
channel_layer = get_channel_layer()
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
        }) 

    try:
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username and password are required"
            })

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
        })

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON request body")
        return JsonResponse({
            "responseCode": 5,
            "responseMessage": "Malformed request"
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Internal server error"
        })


@csrf_exempt
def signup(request):
    """
    Handles user signup.
    """
    if request.method != 'POST':
        return JsonResponse({
            "responseCode": 2,
            "responseMessage": "Method not allowed"
        })

    try:
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')
        confirmPassword = data.get('confirmPassword')

        if not username or not password:
            return JsonResponse({
                "responseCode": 4,
                "responseMessage": "Username and password are required"
            })

        # Check if passwords match
        if password != confirmPassword:
            return JsonResponse({
                "responseCode": 6,
                "responseMessage": "Passwords do not match!"
            })

        # Check for password length
        if len(password) < 5:
            return JsonResponse({
                "responseCode": 7,
                "responseMessage": "Password should be at least 5 characters long!"
            })

        if game.objects.filter(user_name=username).exists():
            logger.warning(f"Signup attempt with existing username: {username}")
            return JsonResponse({
                "responseCode": 1,
                "responseMessage": "Nickname already exists"
            }) 

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
        }) 

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JsonResponse({
            "responseCode": 3,
            "responseMessage": "Internal server error"
        }) 


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
def fetch_user_data(request):
    try:
        data = json.loads(request.body)
        user_name = data.get('userName')

        user_game = game.objects.get(user_name=user_name)

        # Convert rating_changes from comma-separated string to a list of integers
        rating_changes_list = [int(item) for item in user_game.rating_changes.split(',')] if user_game.rating_changes else []

        # Extract the last 5 changes for display
        last_five_changes = rating_changes_list[-5:]

        # Calculate win percentage
        win_percentage = round((user_game.won / user_game.played) * 100, 1) if user_game.played > 0 else 0

        response_data = {
            "username": user_game.user_name,
            "currentRating": user_game.elo_rating,
            "played": user_game.played,
            "won": user_game.won,
            "lost": user_game.lost,
            "winPercentage": win_percentage,
            "lastFiveGames": last_five_changes
        }

        return JsonResponse({"responseCode": 0, "responseMessage": "Profile Success", "userData": response_data})

    except game.DoesNotExist:
        logger.warning(f"User with name {user_name} not found.")
        return JsonResponse({"responseCode": 2, "responseMessage": "User not found"})

    except Exception as e:
        logger.error(f"Error fetching user data for {user_name}: {e}")
        return JsonResponse({"responseCode": 1, "responseMessage": "Profile Error"})


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
        player1_history = history.objects.filter(player1=player).values_list('player2', flat=True)
        player2_history = history.objects.filter(player2=player).values_list('player1', flat=True)
        
        if not any(p in team for p in player1_history) and not any(p in team for p in player2_history):
            return player
    return sorted_players[0]  # Return the top-ranked player if no unmatched player is found


def generate_pairing():
    try:
        available_players = game.objects.filter(status="active", playing="N")
        
        if len(available_players) < 4:
            return {
                "responseCode": 1,
                "responseMessage": "Not enough players for matches."
            }

        sorted_players = sorted(available_players, key=lambda p: (-p.unmatched_priority, -p.uncertainty, p.elo_rating))
        
        pairings, selected_players = [], []
        for _ in range(1):  
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
        game.objects.filter(pk__in=[player.pk for player in selected_players]).update(playing="Y", unmatched_priority=0)
        game.objects.filter(pk__in=[player.pk for player in sorted_players]).update(unmatched_priority=F('unmatched_priority') + 1)
        
        today = date.today()
        for team in pairings:
            for player1 in team[0]:
                for player2 in team[1]:
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

        available_courts = court.objects.filter(status=True).order_by('id')
        first_available_court = available_courts.first()
        first_available_court_key = f'court{first_available_court.id}' if first_available_court else None
        
        if first_available_court:
            first_available_court.status = False
            first_available_court.save()

        court_status = fetch_court_status()

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

        logger.info("Pairing generated successfully.")
        return response_data

    except Exception as e:
        logger.error(f"Error during pairing generation: {e}")
        return {
            "responseCode": 2,
            "responseMessage": "Error occurred during pairing generation."
        }


@csrf_exempt
def update_elo(request):
    try:
        # Load the JSON data from the request
        data = json.loads(request.body)
        team_details = data.get('teamDetails')

        winners = team_details['winner']
        losers = team_details['loser']
        court_name = team_details['court']

        # Constants
        K = 30
        F1 = 30
        F2 = 180

        updated_details = {}

        def calculate_average_rating(players):
            return sum([game.objects.get(user_name=player['userName']).elo_rating for player in players]) / len(players)

        winner_avg_rating = calculate_average_rating(winners)
        loser_avg_rating = calculate_average_rating(losers)

        # Calculate expected score
        expected_winner = 1 / (1 + 10 ** ((loser_avg_rating - winner_avg_rating) / 400))
        expected_loser = 1 - expected_winner

        def handle_players(team, outcome, expected_outcome):
            for player in team:
                user = game.objects.get(user_name=player['userName'])
                rating_change = round(K * (outcome - expected_outcome))

                # Updating and Truncating rating_changes_list to keep the last 10 entries
                rating_changes_list = [int(x) for x in (user.rating_changes or "").split(",") if x]
                rating_changes_list.append(rating_change)  # Append the new rating change
                rating_changes_list = rating_changes_list[-10:]  # Keep only the last 10 changes

                user.rating_changes = ",".join(map(str, rating_changes_list))  # Convert the list back to a string
                user.elo_rating += rating_change
                #user.status = "inactive"
                user.playing = 'N'
                user.played += 1
                user.won += outcome
                user.lost += 1 - outcome

                rating_changes_list = [int(x) for x in user.rating_changes.split(",") if x]
                sd_factor = 1 + (math.sqrt(sum([(x - sum(rating_changes_list)/len(rating_changes_list)) ** 2 for x in rating_changes_list]) / len(rating_changes_list)) if rating_changes_list else 0) / F1

                days_since_last_game = (datetime.now().date() - (user.last_played or datetime.now().date())).days
                decay_factor = 1 + days_since_last_game / F2
                base_uncertainty = max(0.05, 1 - user.played / 100)
                user.uncertainty = round(min(1, max(0.05, base_uncertainty * sd_factor * decay_factor)), 2)
                user.last_played = datetime.now().date()
                user.save()

                court_to_update = court.objects.get(court_name=court_name)
                court_to_update.status = True
                court_to_update.save()

                updated_details[user.user_name] = {
                    "eloRating": user.elo_rating,
                    "ratingDiff": rating_change,
                    "result": outcome
                }

                async_to_sync(channel_layer.group_send)('updates_group', {
                    'type': 'send_update',
                    'message': {
                        'updateType': 'updatedDetailsModal',
                        'data': updated_details
                    }
                })

        handle_players(winners, 1, expected_winner)
        handle_players(losers, 0, expected_loser)

        return JsonResponse({'responseCode': 0, "responseMessage": "ELO updated successfully.", "updatedDetails": updated_details})

    except Exception as e:
        logger.error(f"Error during ELO update: {e}")
        return JsonResponse({"responseCode": 2, "responseMessage": "Error occurred during ELO update."})


@csrf_exempt
def get_court_status(request):
    try:
        court_status = fetch_court_status()
        return JsonResponse({
            "responseCode": 0,
            "responseMessage": "Reset Successful",
            "courtStatus": court_status
        }, safe=False)

    except Exception as e:
        logger.error(f"Error while getting court status: {e}")
        return JsonResponse({"responseCode": 1, "responseMessage": "Reset Error"})


@csrf_exempt
def navigate_to_court_screen(request):
    try:
        data = json.loads(request.body)
        user_name = data.get('userName')

        court_status = fetch_court_status()

        async_to_sync(channel_layer.group_send)('updates_group', {
            'type': 'send_update',
            'message': {
                'updateType': 'court_status',
                'data': court_status
            }
        })

        async_to_sync(channel_layer.group_send)('updates_group', {
            'type': 'send_update',
            'message': {
                'updateType': 'navigateBack',
                'data': user_name
            }
        })

        return JsonResponse({"responseCode": 0, "responseMessage": "Navigation Success"})

    except Exception as e:
        logger.error(f"Error during navigation to court screen: {e}")
        return JsonResponse({"responseCode": 1, "responseMessage": "Navigation Error"})


#@receiver(post_save, sender=game)
#def player_joined(sender, instance, **kwargs):
    # Check if there are at least 4 active players to generate pairing.
    
    # Filter by both 'status="active"' and 'playing!="Y"'
#    active_players_count = game.objects.filter(status="active", playing="N").count()
    
#    if active_players_count >= 4:
#        generate_pairing()



@csrf_exempt
def reset_database(request):
    try:

        all_players = game.objects.all()

        all_courts = court.objects.all()

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

        for court_status in all_courts:
            court_status.status = True
            court_status.save()

        response_data = {
            "responseCode": 0,
            "responseMessage": "Reset Successful"
        }
        return JsonResponse(response_data, safe=False)

    except Exception as e:
        # Handle any exceptions that may occur during fetching active players
        print("Error:", e)
        return JsonResponse({"responseCode": 2, "responseMessage": "Reset Error"})

######################################################## TESTING ########################################################

from django.http import JsonResponse
from rest_framework.decorators import api_view
import requests
import random
from django.http import HttpResponse

@api_view(['POST'])
def run_simulation(request):
    game.objects.all().update(status='active')

    # Loop 1000 times
    for i in range(5):
        response2 = generate_pairing()  # Generate pairing
        callUpdateElo(response2)  # Update ELO

    # Fetch all game records
    all_games = game.objects.all()

    # Prepare HTML Table with styling
    html_table = '''
    <html>
    <head>
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #00897B;
                color: white;
                padding: 8px;
            }
            td {
                background-color: #E0F7FA;
                padding: 8px;
            }
        </style>
    </head>
    <body>
        <table border="1">
    '''

    html_table += "<tr><th>User Name</th><th>Elo Rating</th><th>Uncertainty</th><th>Played</th><th>Won</th><th>Lost</th><th>Win%</th></tr>"

    for game_instance in all_games:
        user_name = game_instance.user_name
        elo_rating = game_instance.elo_rating
        uncertainty = game_instance.uncertainty
        played = game_instance.played
        won = game_instance.won
        lost = game_instance.lost

        # Calculate win% (win percentage)
        win_percentage = 0  # Initialize to 0 to handle case when played is 0
        if played != 0:
            win_percentage = round((won / played) * 100, 1)

        html_table += f"<tr><td>{user_name}</td><td>{elo_rating}</td><td>{uncertainty}</td><td>{played}</td><td>{won}</td><td>{lost}</td><td>{win_percentage}</td></tr>"

    html_table += "</table></body></html>"

    return HttpResponse(html_table)



# Function to format the court name
def format_court_name(court_key):
    # Extract the last digit from the court key
    court_number = court_key[-1]
    # Create the new court name by attaching the extracted number
    return f"Court-{court_number}"

def callUpdateElo(response2):
    teams = response2.get('teams', [])

    # Assuming we're dealing with the first pairing
    team1 = teams[0].get('team1', [])
    team2 = teams[0].get('team2', [])

    # Randomly pick a winner and loser
    winner = random.choice(['team1', 'team2'])
    loser = 'team2' if winner == 'team1' else 'team1'

    # Create the payload
    payload = {
        "teamDetails":{
        'winner': team1 if winner == 'team1' else team2,
        'loser': team2 if loser == 'team2' else team1,
        'court': format_court_name(response2.get('firstAvailableCourt'))  # Format the court name
        }
    }

    # Step 3: Update ELO
    response3 = requests.post('https://badminton-app-py-c9deadd73cd5.herokuapp.com/app/updateElo/', json=payload)
    if response3.status_code != 200:  # Note: check for status_code, as it's an HTTP response object
        return JsonResponse({"error": "Failed to update ELO"}, status=400)



