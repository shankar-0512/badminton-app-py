from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import math
import json
import random
from .models import game
from .models import court
from datetime import datetime
from django.db.models import F
from django.contrib.auth.hashers import make_password, check_password


@csrf_exempt
def login(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            username = data.get('userName')
            password = data.get('password')

            user = game.objects.filter(user_name=username).first()

            print(password, user.password)

            if user and check_password(password, user.password):
                response_data = {
                    "responseCode": 0,
                    "responseMessage": "Login Successful",
                    "userName": username
                }
            else:
                response_data = {
                    "responseCode": 1,
                    "responseMessage": "Invalid Username or Password",
                }

            return JsonResponse(response_data, safe=False)

    except Exception as e:
        print("Error:", e)
        return JsonResponse({"responseCode": 1, "responseMessage": "Login Error"})


@csrf_exempt
def signup(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            username = data.get('userName')
            password = data.get('password')

            if game.objects.filter(user_name=username).exists():
                return JsonResponse({"responseCode": 1, "responseMessage": "Username already exists"})

            hashed_password = make_password(password)

            new_user = game(
                user_name=username,
                password=hashed_password,
                # You can add any additional fields here that are required for the new user
            )
            new_user.save()

            response_data = {
                "responseCode": 0,
                "responseMessage": "Signup Successful",
            }
            return JsonResponse(response_data, safe=False)
        else:
            return JsonResponse({"responseCode": 1, "responseMessage": "Method not allowed"}, status=405)

    except Exception as e:
        print("Error:", e)
        return JsonResponse({"responseCode": 1, "responseMessage": "Signup Error"})


@csrf_exempt
def fetch_active_players(request):
    try:
        # Fetch all players with the "active" status and "playing" status as "N"
        available_players = game.objects.filter(status="active", playing="N")
        # Get the count of active players
        active_players_count = available_players.count()

        response_data = {
            "responseCode": 0,
            "responseMessage": "Active players fetched successfully.",
            "activePlayersCount": active_players_count,  # Include the count in the response
        }
        return JsonResponse(response_data, safe=False)

    except Exception as e:
        # Handle any exceptions that may occur during fetching active players
        print("Error:", e)
        return JsonResponse({"responseCode": 2, "responseMessage": "Error occurred during fetching active players."})


@csrf_exempt
def add_to_pool(request):
    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            user_name = data.get('userName')

            user = game.objects.get(user_name=user_name)

            # Update the status to "active"
            user.status = "active"
            user.save()

            response_data = {"responseCode": 0,
                             "responseMessage": "ADD_TO_POOL_SUCCESS"}

        except json.JSONDecodeError:
            response_data = {"responseCode": 1,
                             "responseMessage": "ADD_TO_POOL_ERROR"}

        return JsonResponse(response_data)


@csrf_exempt
def remove_from_pool(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_name = data.get('userName')

            user = game.objects.get(user_name=user_name)

            # Update the status to "active"
            user.status = "inactive"

            user.unmatched_priority = 0
            user.save()

            response_data = {"responseCode": 0,
                             "responseMessage": "REMOVE_FROM_POOL_SUCCESS"}

        except json.JSONDecodeError:
            response_data = {"responseCode": 1,
                             "responseMessage": "REMOVE_FROM_POOL_ERROR"}

        return JsonResponse(response_data)


@csrf_exempt
def generate_pairing(request):
    try:
        # Fetch all players with the "active" status and "playing" status as "N"
        available_players = game.objects.filter(status="active", playing="N")

        # Sort players based on unmatched priority, uncertainty, and ELO
        sorted_players = sorted(
            available_players, key=lambda p: (-p.unmatched_priority, -p.uncertainty, p.elo_rating))

        if len(sorted_players) < 4:  # Check if there are enough players for four matches
            return JsonResponse({"responseCode": 1, "responseMessage": "Not enough players for matches."})

        pairings = []
        for _ in range(1):  # Create four pairings for four matches
            team1 = []
            team2 = []

            # Select two players for team1
            for _ in range(2):
                player = select_player(sorted_players)
                team1.append(player)
                sorted_players.remove(player)

            # Select two players for team2
            for _ in range(2):
                player = select_player(sorted_players)
                team2.append(player)
                sorted_players.remove(player)

            pairings.append((team1, team2))

        # Update the "playing" column for all selected players to "Y"
        selected_players = [
            player for team in pairings for player in team[0] + team[1]]
        game.objects.filter(
            pk__in=[player.pk for player in selected_players]).update(playing="Y")

        # Increment unmatched priority for remaining players
        game.objects.filter(pk__in=[player.pk for player in sorted_players]).update(
            unmatched_priority=F('unmatched_priority') + 1)

        # Reset the unmatched priority for matched players
        game.objects.filter(pk__in=[player.pk for player in selected_players]).update(
            unmatched_priority=0)

        # Create a list of teams with userName, elo, and uncertainty
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

        # Fetches the first available court
        first_available_court = available_courts.first()
        first_available_court_key = None  # To store the key of the first available court

        if first_available_court:
            first_available_court_key = f'court{first_available_court.id}'
            first_available_court.status = False  # Sets the status to False
            first_available_court.save()  # Saves the change to the database

        # Reset pairings list to empty
        pairings = []

        court_status = fetch_court_status()

        response_data = {
            "responseCode": 0,
            "responseMessage": "Pairing generated successfully.",
            "teams": teams,
            "courtStatus": court_status,
            "firstAvailableCourt": first_available_court_key
        }

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        # Handle any exceptions that may occur during pairing generation
        print("Error:", e)
        return JsonResponse({"responseCode": 2, "responseMessage": "Error occurred during pairing generation."})


def select_player(available_players):
    # Select a player from available players without considering opponents
    return random.choice(available_players)


@csrf_exempt
def update_elo(request):
    try:
        # Load the JSON data from the request
        data = json.loads(request.body)
        teamDetails = data.get('teamDetails')

        winners = teamDetails['winner']
        losers = teamDetails['loser']
        court_name = teamDetails['court']

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
            player.status = "active"
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


def fetch_court_status():
    all_courts = court.objects.all()

    court_status = {}
    for c in all_courts:
        court_key = f'court{c.id}'
        court_status[court_key] = {
            "name": c.court_name,
            "status": c.status,
        }

    return court_status
