from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random


def hello_view(request):
    return HttpResponse("Hello, World!")


def json_example(request):
    data = {
        'message': 'This is a JSON response!',
        'status': 'success',
    }
    return JsonResponse(data)


@csrf_exempt
def greet(request):
    if request.method == 'POST':
        try:
            # Load the JSON data from the request body
            data = json.loads(request.body)

            # Extract the "name" field from the JSON data
            name = data.get('name')

            if name:
                # Construct the greeting message
                message = f"Hello, {name}! Welcome to the Django POST example."
                response_data = {'message': message, 'status': 'success'}
            else:
                response_data = {
                    'error': 'Name not found in the JSON data.', 'status': 'error'}

        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON data.', 'status': 'error'}

        return JsonResponse(response_data)
    else:
        response_data = {'error': 'Invalid request method.', 'status': 'error'}
        # Return "Method Not Allowed" status
        return JsonResponse(response_data, status=405)


@csrf_exempt
def add_to_pool(request):
    if request.method == 'POST':
        try:
            print("Hiiiiii")
            response_data = {'message': "Successful 2", 'status': 'success'}

        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON data.', 'status': 'error'}

        return JsonResponse(response_data)


def generate_pairing(request):

    # Sample list of player names
    player_names = ['John', 'Jane', 'Michael',
                    'Emily', 'David', 'Olivia', 'James', 'Emma']

    # Create a list of dictionaries representing players
    available_players = [
        {
            'name': name,
            # Random ELO score between 900 and 1200
            'elo': random.randint(900, 1200),
            'playing': False,
            'games_played': 0,
            'games_won': 0,
            'games_lost': 0,
            'uncertainty': 1.0,  # Initialize high uncertainty for new players
            'rating_deviation': 350  # Default rating deviation
        }
        for name in player_names
    ]

    # Sort players based on uncertainty and ELO
    available_players.sort(key=lambda p: (-p['uncertainty'], p['elo']))

    ########### TESTING #############

    if 999:  # You might want to specify a condition to trigger the testing
        for player in available_players:
            print(
                f'Name: {player["name"]}, ELO: {player["elo"]}, Uncertainty: {player["uncertainty"]}')

    #################################

    if len(available_players) < 8:  # Check if there are enough players for four matches
        return None

    pairings = []
    for _ in range(1):  # Create four pairings for four matches
        team1 = []
        team2 = []

        # Select two players for team1
        for _ in range(2):
            player = select_player(available_players)
            team1.append(player)

        # Select two players for team2
        for _ in range(2):
            player = select_player(available_players)
            team2.append(player)

        pairings.append((team1, team2))

    # Set playing status for players in all pairings
    for pair in pairings:
        for player in pair[0] + pair[1]:
            player['playing'] = True

    print(pairings)

    # Create a list of teams
    teams = [{'team1': team[0], 'team2': team[1]} for team in pairings]

    # Reset pairings list to empty
    pairings = []

    # Return the teams as a JSON response
    return JsonResponse(teams, safe=False)


def select_player(available_players):
    # Select a player from available players without considering opponents
    return random.choice(available_players)
