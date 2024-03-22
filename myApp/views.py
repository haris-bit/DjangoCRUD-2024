from  django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from basketball_reference_web_scraper import client
from .models import AdvanceStats
from .serializers import AdvanceStatsSerializer
import requests
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

# Create your views here.
def home(request):
    return render(request, 'myApp/index.html')


@api_view(["GET"])
@require_http_methods(["GET"])
def user_data(request, username, format=None):
    if request.method == 'GET':
        try:
            # Make a GET request to the JSON URL for user draft data
            url = "https://newdjangobackend-b4845409485a.herokuapp.com/json-data/"
            response = requests.get(url)

            if response.status_code == 200:
                user_drafts = response.json()

                # Find the user with the specified username
                user_data = next((user for user in user_drafts if user['Username'] == username), None)

                if user_data:
                    # Use the basketball_reference_web_scraper to fetch player advanced statistics data
                    player_stats = client.players_advanced_season_totals(season_end_year=2023)

                    # Initialize an empty list to store serialized player stats
                    players_stats = []

                    # Deserialize and validate each player's data
                    for stats in player_stats:
                        serializer = AdvanceStatsSerializer(data=stats)
                        if serializer.is_valid():
                            players_stats.append(serializer.data)

                    # Sort the data based on the specified fields in descending order
                    sorted_stats = sorted(players_stats, key=lambda x: (
                        -x.get('win_shares', 0),
                        -x.get('win_shares_per_48_minutes', 0),
                        -x.get('box_plus_minus', 0),
                        -x.get('value_over_replacement_player', 0),
                    ))

                    # Get the top 20 players
                    top_20_players = sorted_stats[:20]

                    # Fetch the user's player efficiency ratings
                    user_per_url = f"https://newdjangobackend-b4845409485a.herokuapp.com/api/player_efficiency_ratings/{username}/"
                    user_per_response = requests.get(user_per_url)

                    if user_per_response.status_code == 200:
                        user_per_data = user_per_response.json()

                        # Extract the PER values from the user_per_data
                        per_values = [player['per'] for player in user_per_data if player['per'] is not None]

                        # Calculate the sum of PER values
                        per_sum = sum(per_values)

                        # Calculate the PER%
                        if per_sum > 0:
                            per_percentage = (per_sum / sum(player['player_efficiency_rating'] for player in top_20_players)) * 100
                            per_percentage = round(per_percentage, 2)
                        else:
                            per_percentage = 0

                        # Compare picks and calculate the correct count
                        correct_count = 0
                        for i in range(1, 21):
                            user_pick = user_data.get(f'Who_{i}', None)
                            if user_pick == top_20_players[i - 1]['name']:
                                correct_count += 1

                        user_result = {
                            'Username': username,
                            'CorrectPicks': correct_count,
                            'UserTotalPER': per_sum,
                            'UserPERPercentage': per_percentage
                        }

                        return Response(user_result)

                    else:
                        error_message = f'Failed to fetch PER data for user: {username}'
                        print(error_message)
                        return Response({'error': error_message}, status=500)

                else:
                    return Response({'error': 'User not found'}, status=404)

            else:
                return Response({'error': 'Failed to fetch user draft data from JSON endpoint'}, status=500)
        except Exception as e:
            error_message = f'An error occurred: {str(e)}'
            print(error_message)
            return Response({'detail': error_message}, status=500)







# Decorate the view with caching
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def get_correct_picks(request, format=None):
    # Check if the result is already cached
    cached_result = cache.get('correct_picks')
    if cached_result:
        return Response(cached_result)
    else:
        if request.method == 'GET':
            try:
                # Make a GET request to the JSON URL for user draft data
                url = "https://newdjangobackend-b4845409485a.herokuapp.com/json-data/"

                response = requests.get(url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    user_drafts = response.json()

                    # Use the basketball_reference_web_scraper to fetch player advanced statistics data
                    player_stats = client.players_advanced_season_totals(
                        season_end_year=2023
                    )  # Replace with the desired season year

                    # Initialize an empty list to store serialized player stats
                    players_stats = []

                    # Deserialize and validate each player's data
                    for stats in player_stats:
                        serializer = AdvanceStatsSerializer(data=stats)
                        if serializer.is_valid():
                            players_stats.append(serializer.data)
                        else:
                            # Handle invalid data if needed
                            # You can log validation errors or take other actions here
                            pass

                    # Sort the data based on the specified fields in descending order
                    sorted_stats = sorted(players_stats, key=lambda x: (
                        -x.get('win_shares', 0),
                        -x.get('win_shares_per_48_minutes', 0),
                        -x.get('box_plus_minus', 0),
                        -x.get('value_over_replacement_player', 0),
                    ))

                    # Get the top 20 players
                    top_20_players = sorted_stats[:20]

                    # Save the top 20 players' data to the database
                    for player_data in top_20_players:
                        AdvanceStats.objects.create(
                            name=player_data['name'],
                            minutes_played=player_data['minutes_played'],
                            games_played=player_data['games_played'],
                            three_point_attempt_rate=player_data['three_point_attempt_rate'],
                            total_rebound_percentage=player_data['total_rebound_percentage'],
                            win_shares=player_data['win_shares'],
                            win_shares_per_48_minutes=player_data['win_shares_per_48_minutes'],
                            box_plus_minus=player_data['box_plus_minus'],
                            value_over_replacement_player=player_data['value_over_replacement_player'],
                            player_efficiency_rating=player_data['player_efficiency_rating']
                        )

                    # Make a GET request to the API for user-submitted players' PER

                    # Initialize an empty list to store all user results
                    correct_picks = []

                    for user_draft in user_drafts:
                        # Get user's email
                        username = user_draft['Username']
                        user_per_url = f"https://newdjangobackend-b4845409485a.herokuapp.com/api/player_efficiency_ratings/{username}/"
                        user_per_response = requests.get(user_per_url)

                        if user_per_response.status_code == 200:
                            user_per_data = user_per_response.json()
                            
                            # Extract the PER values from the user_per_data
                            per_values = [player['per'] for player in user_per_data if player['per'] is not None]

                            # Calculate the sum of PER values
                            per_sum = sum(per_values)
                            print("Sum of PER values:", per_sum)

                            # Calculate the PER%
                            if per_sum > 0:
                                per_percentage = (per_sum / sum(player['player_efficiency_rating'] for player in top_20_players)) * 100
                                # Round the PER% to 2 decimal places
                                per_percentage = round(per_percentage, 2)
                            else:
                                per_percentage = 0
                            print("PER%:", per_percentage)
                        else:
                            print(f"Failed to fetch PER data for user: {username}")

                        # Compare picks and calculate the correct count
                        correct_count = 0
                        for i in range(1, 21):
                            user_pick = user_draft[f'Who_{i}']
                            if user_pick == top_20_players[i - 1]['name']:
                                correct_count += 1

                        # Create an object for this user's results
                        user_result = {
                            'Username': username,
                            'CorrectPicks': correct_count,
                            'UserTotalPER': per_sum,
                            'UserPERPercentage': per_percentage
                        }

                        # Add the user's results to the list
                        correct_picks.append(user_result)

                    # Sort the correct picks based on the CorrectPicks value
                    correct_picks = sorted(correct_picks, key=lambda x: (-x['CorrectPicks'], -x['UserTotalPER'], -x['UserPERPercentage']))

                    # Cache the result
                    cache.set('correct_picks', correct_picks, 60 * 15)  # Cache for 15 minutes

                    # Return the sorted list of correct picks as a response
                    return Response(correct_picks)

                else:
                    return Response({'error': 'Failed to fetch user draft data from JSON endpoint'}, status=500)
            except Exception as e:
                return Response({'detail': str(e)}, status=500)












# Decorate the view with caching
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def leaderboard_list(request, format=None):
    # Check if the result is already cached
    cached_result = cache.get('leaderboard_list')
    if cached_result:
        return Response(cached_result)
    else:
        if request.method == 'GET':
            try:
                # Make a GET request to the JSON URL to fetch user data
                url = "https://sheetdb.io/api/v1/3z14mlm79tmet"
                response = requests.get(url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    json_data = response.json()

                    # Initialize dictionaries to store player_per and sum_per_actual data
                    player_per_cache = {}  # Cache player_per data
                    sum_per_actual_cache = {}  # Cache sum_per_actual data

                    # Initialize a list to store leaderboard data for all users
                    leaderboard_data_list = []

                    for user_data in json_data:
                        username = user_data.get("Username", None)

                        if username:
                            # Fetch player names from user data (Who_1 to Who_20)
                            player_names = [user_data.get(f'Who_{i}', None) for i in range(1, 21)]

                            # Fetch player efficiency ratings for the user
                            if username not in player_per_cache:
                                player_per_api_url = f"https://newdjangobackend-b4845409485a.herokuapp.com/api/player_efficiency_ratings/{username}/"
                                player_per_response = requests.get(player_per_api_url)

                                if player_per_response.status_code == 200:
                                    player_per_data = player_per_response.json()
                                    player_per_dict = {item["player_name"]: item["per"] for item in player_per_data}
                                    player_per_cache[username] = player_per_dict
                                else:
                                    return Response({'detail': 'Failed to fetch player_per data'}, status=500)

                            player_per_dict = player_per_cache[username]

                            # Fetch actual player statistics using the existing API
                            if "sum_per_actual" not in sum_per_actual_cache:
                                sum_per_actual_api_url = "https://newdjangobackend-b4845409485a.herokuapp.com/advance-stats/"
                                sum_per_actual_response = requests.get(sum_per_actual_api_url)

                                if sum_per_actual_response.status_code == 200:
                                    sum_per_actual_data = sum_per_actual_response.json()
                                    top_20_players = [item["player_efficiency_rating"] for item in sum_per_actual_data]
                                    sum_per_actual_cache["sum_per_actual"] = sum(top_20_players)
                                else:
                                    return Response({'detail': 'Failed to fetch sum_per_actual data'}, status=500)

                            sum_per_actual = sum_per_actual_cache["sum_per_actual"]

                            # Calculate sum PER user submitted and correct picks count
                            sum_per_user_submitted = 0
                            correct_picks_count = 0

                            for i, player_name in enumerate(player_names):
                                if player_name and player_name != 'null':
                                    player_per = player_per_dict.get(player_name, None)
                                    if player_per is not None:
                                        sum_per_user_submitted += player_per

                                    # Check if the pick matches the corresponding player in the top 20
                                    if i < len(top_20_players) and player_per == top_20_players[i]:
                                        correct_picks_count += 1

                            # Calculate Accuracy
                            accuracy = (correct_picks_count / 20) * 100

                            # Add the leaderboard data to the list
                            leaderboard_data = {
                                'Username': username,
                                'sum_per_user_submitted': sum_per_user_submitted,
                                'sum_per_actual': sum_per_actual,
                                'per_percentage': (sum_per_user_submitted / sum_per_actual) * 100,
                                'correct_picks_count': correct_picks_count,
                                'accuracy': accuracy
                            }
                            leaderboard_data_list.append(leaderboard_data)

                    # Sort the leaderboard data based on a suitable metric
                    leaderboard_data_list = sorted(leaderboard_data_list, key=lambda x: (-x['correct_picks_count'], -x['sum_per_user_submitted'], -x['per_percentage']))

                    # Cache the result
                    cache.set('leaderboard_list', leaderboard_data_list, 60 * 15)  # Cache for 15 minutes

                    # Return the sorted list of leaderboard data as a JSON response
                    return Response(leaderboard_data_list)
                else:
                    return Response({'detail': 'Failed to fetch JSON data'}, status=response.status_code)
            except Exception as e:
                return Response({'detail': str(e)}, status=500)








@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def leaderboard(request, username, format=None):
    if request.method == 'GET':
        try:
            # Make a single GET request to fetch user data and player efficiency ratings
            url = "https://sheetdb.io/api/v1/3z14mlm79tmet"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()

                # Find the user with the specified username
                user_data = next((d for d in data if d["Username"] == username), None)

                if user_data:
                    # Initialize variables to store sum PER values and correct picks count
                    sum_per_user_submitted = 0
                    correct_picks_count = 0

                    # Fetch actual player statistics using the existing API once
                    sum_per_actual_api_url = "https://newdjangobackend-b4845409485a.herokuapp.com/advance-stats/"
                    sum_per_actual_response = requests.get(sum_per_actual_api_url)

                    if sum_per_actual_response.status_code == 200:
                        sum_per_actual_data = sum_per_actual_response.json()
                        top_20_players = [item["player_efficiency_rating"] for item in sum_per_actual_data]

                        # Fetch player efficiency ratings for the user once
                        player_per_api_url = f"https://newdjangobackend-b4845409485a.herokuapp.com/api/player_efficiency_ratings/{username}/"
                        player_per_response = requests.get(player_per_api_url)

                        if player_per_response.status_code == 200:
                            player_per_data = player_per_response.json()
                            player_per_dict = {item["player_name"]: item["per"] for item in player_per_data}

                            # Fetch player names from user data (Who_1 to Who_20)
                            player_names = [user_data.get(f'Who_{i}', None) for i in range(1, 21)]

                            # Calculate sum PER actual and compare picks with top 20 players
                            for i, player_name in enumerate(player_names):
                                if player_name and player_name in player_per_dict:
                                    player_per = player_per_dict[player_name]
                                    if player_per is not None:  # Check if player_per is not None
                                        sum_per_user_submitted += player_per

                                    if i < len(top_20_players) and player_per == top_20_players[i]:
                                        correct_picks_count += 1

                            # Calculate Accuracy
                            accuracy = (correct_picks_count / 20) * 100

                            # Calculate sum PER actual once
                            sum_per_actual = sum(top_20_players)

                            # Return the leaderboard data as a JSON response
                            leaderboard_data = {
                                'Username': username,
                                'sum_per_user_submitted': sum_per_user_submitted,
                                'sum_per_actual': sum_per_actual,
                                'per_percentage': (sum_per_user_submitted / sum_per_actual) * 100,
                                'correct_picks_count': correct_picks_count,
                                'accuracy': accuracy
                            }

                            return Response(leaderboard_data)
                    else:
                        return Response({'detail': 'User not found'}, status=404)
                else:
                    return Response({'detail': 'User not found'}, status=404)
            else:
                return Response({'detail': 'Failed to fetch JSON data'}, status=response.status_code)
        except Exception as e:
            return Response({'detail': str(e)}, status=500)







@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_player_efficiency_ratings(request, username, format=None):
    try:
        # Initialize an empty list for player efficiency ratings
        player_efficiency_ratings = []

        # Fetch all player advanced statistics
        player_stats = client.players_advanced_season_totals(
            season_end_year=2023  # Update with your desired season year
        )

        # Make a GET request to your JSON URL
        url = "https://sheetdb.io/api/v1/3z14mlm79tmet"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_data = response.json()

            # Find the record with the matching username
            user_records = [record for record in json_data if record["Username"] == username]

            if not user_records:
                return Response({'detail': f'Username "{username}" not found in the JSON data'}, status=404)

            # Ensure there's only one user with the provided username
            if len(user_records) > 1:
                return Response({'detail': f'Multiple users with the same username "{username}" found'}, status=400)

            user_record = user_records[0]

            # Loop through selected players (Who_1 to Who_20)
            for i in range(1, 21):
                player_name_key = f'Who_{i}'
                player_name = user_record.get(player_name_key)

                # Search for the exact player name in player_stats
                matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                if matching_players:
                    # Assuming you want the first matching player
                    player_data = matching_players[0]
                    player_per = player_data.get('player_efficiency_rating', None)
                    player_efficiency_ratings.append({'player_name': player_name, 'per': player_per})
                else:
                    # Player not found, append a placeholder
                    player_efficiency_ratings.append({'player_name': player_name, 'per': None})

            # Return the list of player efficiency ratings as a JSON response
            return Response(player_efficiency_ratings)
        else:
            return Response({'detail': 'Failed to fetch JSON data'}, status=response.status_code)
    except Exception as e:
        return Response({'detail': str(e)}, status=500)






@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_new_player_efficiency_ratings(request, year=None, format=None):
    try:
        # Initialize an empty list for player efficiency ratings
        player_efficiency_ratings = []

        # Define the SheetDB URLs based on the provided year
        if year == "2021":
            sheetdb_url = "https://sheetdb.io/api/v1/o6b7thpgli01v"
        elif year == "2022":
            sheetdb_url = "https://sheetdb.io/api/v1/0ijfobes6yycf"
        else:
            # Default to 2023 if no year is provided
            sheetdb_url = "https://sheetdb.io/api/v1/c3zke3prjz5g6"

        # Make a GET request to the appropriate JSON URL
        response = requests.get(sheetdb_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_data = response.json()

            # Loop through each player object in the JSON data
            for player_obj in json_data:
                player_name = player_obj.get("Player")
                
                # Assuming client.players_advanced_season_totals is defined somewhere
                # Fetch all player advanced statistics for the given year
                player_stats = client.players_advanced_season_totals(
                    season_end_year=int(year) if year else 2023
                )

                # Search for the exact player name in player_stats
                matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                if matching_players:
                    # Assuming you want the first matching player
                    player_data = matching_players[0]
                    player_per = player_data.get('player_efficiency_rating', None)
                    minutes_played = player_data.get('minutes_played', None)
                    games_played = player_data.get('games_played', None)
                    three_point_attempt_rate = player_data.get('three_point_attempt_rate', None)
                    total_rebound_percentage = player_data.get('total_rebound_percentage', None)
                    win_shares = player_data.get('win_shares', None)
                    win_shares_per_48_minutes = player_data.get('win_shares_per_48_minutes', None)
                    box_plus_minus = player_data.get('box_plus_minus', None)
                    value_over_replacement_player = player_data.get('value_over_replacement_player', None)

                    if player_per is not None:  # Check if PER value is not None
                        player_efficiency_ratings.append({
                            'player_name': player_name,
                            'per': player_per,
                            'minutes_played': minutes_played,
                            'games_played': games_played,
                            'three_point_attempt_rate': three_point_attempt_rate,
                            'total_rebound_percentage': total_rebound_percentage,
                            'win_shares': win_shares,
                            'win_shares_per_48_minutes': win_shares_per_48_minutes,
                            'box_plus_minus': box_plus_minus,
                            'value_over_replacement_player': value_over_replacement_player
                        })

            # Filter out players with None PER values
            player_efficiency_ratings = [player for player in player_efficiency_ratings if player['per'] is not None]
            
            # Sort player efficiency ratings based on PER in descending order
            sorted_player_efficiency_ratings = sorted(player_efficiency_ratings, key=lambda x: x['per'], reverse=True)
            
            # Retrieve only the top 20 players
            top_20_players = sorted_player_efficiency_ratings[:20]

            # Return the list of top 20 player efficiency ratings as a JSON response
            return Response(top_20_players)

        else:
            return Response({'detail': 'Failed to fetch data from SheetDB'}, status=response.status_code)

    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=500)




# hard-coded for 2023
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_hard_coded_player_efficiency_ratings_2023(request, format=None):
    try:
        # Initialize an empty list for player efficiency ratings
        player_efficiency_ratings = []

        # Fetch all player advanced statistics
        player_stats = client.players_advanced_season_totals(
            season_end_year=2024  # Update with your desired season year
        )

        # Make a GET request to your JSON URL
        url = "https://sheetdb.io/api/v1/c3zke3prjz5g6"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_data = response.json()

            # Loop through each player object in the JSON data
            for player_obj in json_data:
                player_name = player_obj.get("Player")
                
                # Search for the exact player name in player_stats
                matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                if matching_players:
                    # Assuming you want the first matching player
                    player_data = matching_players[0]
                    player_per = player_data.get('player_efficiency_rating', None)
                    minutes_played = player_data.get('minutes_played', None)
                    games_played = player_data.get('games_played', None)
                    three_point_attempt_rate = player_data.get('three_point_attempt_rate', None)
                    total_rebound_percentage = player_data.get('total_rebound_percentage', None)
                    win_shares = player_data.get('win_shares', None)
                    win_shares_per_48_minutes = player_data.get('win_shares_per_48_minutes', None)
                    box_plus_minus = player_data.get('box_plus_minus', None)
                    value_over_replacement_player = player_data.get('value_over_replacement_player', None)

                    if player_per is not None:  # Check if PER value is not None
                        player_efficiency_ratings.append({
                            'player_name': player_name,
                            'per': player_per,
                            'minutes_played': minutes_played,
                            'games_played': games_played,
                            'three_point_attempt_rate': three_point_attempt_rate,
                            'total_rebound_percentage': total_rebound_percentage,
                            'win_shares': win_shares,
                            'win_shares_per_48_minutes': win_shares_per_48_minutes,
                            'box_plus_minus': box_plus_minus,
                            'value_over_replacement_player': value_over_replacement_player
                        })

            # Filter out players with None PER values
            player_efficiency_ratings = [player for player in player_efficiency_ratings if player['per'] is not None]
            
            # Sort player efficiency ratings based on PER in descending order
            sorted_player_efficiency_ratings = sorted(player_efficiency_ratings, key=lambda x: x['per'], reverse=True)
            
            # Retrieve only the top 20 players
            top_20_players = sorted_player_efficiency_ratings[:20]

            # Return the list of top 20 player efficiency ratings as a JSON response
            return Response(top_20_players)

        else:
            return Response({'detail': 'Failed to fetch data from SheetDB'}, status=response.status_code)

    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=500)


# hard-coded for 2022
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_hard_coded_player_efficiency_ratings_2022(request, format=None):
    try:
        # Initialize an empty list for player efficiency ratings
        player_efficiency_ratings = []

        # Fetch all player advanced statistics
        player_stats = client.players_advanced_season_totals(
            season_end_year=2024  # Update with your desired season year
        )

        # Make a GET request to your JSON URL
        url = "https://sheetdb.io/api/v1/0ijfobes6yycf"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_data = response.json()

            # Loop through each player object in the JSON data
            for player_obj in json_data:
                player_name = player_obj.get("Player")
                
                # Search for the exact player name in player_stats
                matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                if matching_players:
                    # Assuming you want the first matching player
                    player_data = matching_players[0]
                    player_per = player_data.get('player_efficiency_rating', None)
                    minutes_played = player_data.get('minutes_played', None)
                    games_played = player_data.get('games_played', None)
                    three_point_attempt_rate = player_data.get('three_point_attempt_rate', None)
                    total_rebound_percentage = player_data.get('total_rebound_percentage', None)
                    win_shares = player_data.get('win_shares', None)
                    win_shares_per_48_minutes = player_data.get('win_shares_per_48_minutes', None)
                    box_plus_minus = player_data.get('box_plus_minus', None)
                    value_over_replacement_player = player_data.get('value_over_replacement_player', None)

                    if player_per is not None:  # Check if PER value is not None
                        player_efficiency_ratings.append({
                            'player_name': player_name,
                            'per': player_per,
                            'minutes_played': minutes_played,
                            'games_played': games_played,
                            'three_point_attempt_rate': three_point_attempt_rate,
                            'total_rebound_percentage': total_rebound_percentage,
                            'win_shares': win_shares,
                            'win_shares_per_48_minutes': win_shares_per_48_minutes,
                            'box_plus_minus': box_plus_minus,
                            'value_over_replacement_player': value_over_replacement_player
                        })

            # Filter out players with None PER values
            player_efficiency_ratings = [player for player in player_efficiency_ratings if player['per'] is not None]
            
            # Sort player efficiency ratings based on PER in descending order
            sorted_player_efficiency_ratings = sorted(player_efficiency_ratings, key=lambda x: x['per'], reverse=True)
            
            # Retrieve only the top 20 players
            top_20_players = sorted_player_efficiency_ratings[:20]

            # Return the list of top 20 player efficiency ratings as a JSON response
            return Response(top_20_players)

        else:
            return Response({'detail': 'Failed to fetch data from SheetDB'}, status=response.status_code)

    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=500)


# hard-coded for 2021
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_hard_coded_player_efficiency_ratings_2021(request, format=None):
    try:
        # Initialize an empty list for player efficiency ratings
        player_efficiency_ratings = []

        # Fetch all player advanced statistics
        player_stats = client.players_advanced_season_totals(
            season_end_year=2024  # Update with your desired season year
        )

        # Make a GET request to your JSON URL
        url = "https://sheetdb.io/api/v1/o6b7thpgli01v"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            json_data = response.json()

            # Loop through each player object in the JSON data
            for player_obj in json_data:
                player_name = player_obj.get("Player")
                
                # Search for the exact player name in player_stats
                matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                if matching_players:
                    # Assuming you want the first matching player
                    player_data = matching_players[0]
                    player_per = player_data.get('player_efficiency_rating', None)
                    minutes_played = player_data.get('minutes_played', None)
                    games_played = player_data.get('games_played', None)
                    three_point_attempt_rate = player_data.get('three_point_attempt_rate', None)
                    total_rebound_percentage = player_data.get('total_rebound_percentage', None)
                    win_shares = player_data.get('win_shares', None)
                    win_shares_per_48_minutes = player_data.get('win_shares_per_48_minutes', None)
                    box_plus_minus = player_data.get('box_plus_minus', None)
                    value_over_replacement_player = player_data.get('value_over_replacement_player', None)

                    if player_per is not None:  # Check if PER value is not None
                        player_efficiency_ratings.append({
                            'player_name': player_name,
                            'per': player_per,
                            'minutes_played': minutes_played,
                            'games_played': games_played,
                            'three_point_attempt_rate': three_point_attempt_rate,
                            'total_rebound_percentage': total_rebound_percentage,
                            'win_shares': win_shares,
                            'win_shares_per_48_minutes': win_shares_per_48_minutes,
                            'box_plus_minus': box_plus_minus,
                            'value_over_replacement_player': value_over_replacement_player
                        })

            # Filter out players with None PER values
            player_efficiency_ratings = [player for player in player_efficiency_ratings if player['per'] is not None]
            
            # Sort player efficiency ratings based on PER in descending order
            sorted_player_efficiency_ratings = sorted(player_efficiency_ratings, key=lambda x: x['per'], reverse=True)
            
            # Retrieve only the top 20 players
            top_20_players = sorted_player_efficiency_ratings[:20]

            # Return the list of top 20 player efficiency ratings as a JSON response
            return Response(top_20_players)

        else:
            return Response({'detail': 'Failed to fetch data from SheetDB'}, status=response.status_code)

    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=500)














@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def get_player_per(request, format=None):
    if request.method == 'GET':
        try:
            # Make a GET request to the JSON URL
            url = "https://sheetdb.io/api/v1/3z14mlm79tmet"
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                json_data = response.json()

                # Initialize an empty list to store player PER values
                player_per_values = []

                # Fetch all player advanced statistics
                player_stats = client.players_advanced_season_totals(
                    season_end_year=2023
                )

                # Loop through records and player names
                for record in json_data:
                    for i in range(1, 21):
                        player_name_key = f'Who_{i}'
                        player_name = record.get(player_name_key)

                        # Search for the exact player name in player_stats
                        matching_players = [stats for stats in player_stats if player_name.lower() == stats["name"].lower()]

                        if matching_players:
                            # Assuming you want the first matching player
                            player_data = matching_players[0]
                            player_per = player_data.get('player_efficiency_rating', None)
                            player_per_values.append({'player_name': player_name, 'per': player_per})
                        else:
                            # Player not found, append a placeholder
                            player_per_values.append({'player_name': player_name, 'per': None})

                # Print player PER values for debugging
                # print(player_per_values)

                # Return the list of player PER values as a JSON response
                return Response(player_per_values)
            else:
                return Response({'detail': 'Failed to fetch JSON data'}, status=response.status_code)
        except Exception as e:
            return Response({'detail': str(e)}, status=500)











# I want from whos1 to whos20
@require_http_methods(["GET", "OPTIONS"])  # Allow GET and OPTIONS requests
@api_view(["GET"])
def json_data_view(request, format=None):
    if request.method == 'GET':
        try:
            # Make a GET request to the JSON URL
            url = "https://sheetdb.io/api/v1/3z14mlm79tmet"
            response = requests.get(url)
            
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                json_data = response.json()
                return Response(json_data)
            else:
                return Response({'detail': 'Failed to fetch JSON data'}, status=response.status_code)
        except Exception as e:
            return Response({'detail': str(e)}, status=500)



@api_view(['GET'])
def advance_stats_list(request, year=None, format=None):
    if request.method == 'GET':
        try:
            # Use the basketball_reference_web_scraper to fetch player advanced statistics data
            if year is not None:
                season_end_year = int(year)
            else:
                # If year is not provided, use a default value
                season_end_year = 2023

            player_stats = client.players_advanced_season_totals(
                season_end_year=season_end_year
            )

            # Initialize an empty list to store serialized player stats
            players_stats = []

            # Deserialize and validate each player's data
            for stats in player_stats:
                serializer = AdvanceStatsSerializer(data=stats)
                if serializer.is_valid():
                    players_stats.append(serializer.data)
                else:
                    # Handle invalid data if needed
                    pass

            # Sort the data based on the specified fields in descending order
            sorted_stats = sorted(players_stats, key=lambda x: (
                -x['player_efficiency_rating']
                if x['player_efficiency_rating'] is not None
                else -1000,
            ))

            # Get the top 20 players
            top_20_players = sorted_stats[:20]

            # Save the top 20 players' data to the database
            for player_data in top_20_players:
                AdvanceStats.objects.create(
                    name=player_data['name'],
                    minutes_played=player_data['minutes_played'],
                    games_played=player_data['games_played'],
                    three_point_attempt_rate=player_data['three_point_attempt_rate'],
                    total_rebound_percentage=player_data['total_rebound_percentage'],
                    win_shares=player_data['win_shares'],
                    win_shares_per_48_minutes=player_data['win_shares_per_48_minutes'],
                    box_plus_minus=player_data['box_plus_minus'],
                    value_over_replacement_player=player_data['value_over_replacement_player'],
                    player_efficiency_rating=player_data['player_efficiency_rating']
                )

            # Return the top 20 players' data as a JSON response
            return Response(top_20_players)
        except Exception as e:
            return Response({'detail': str(e)}, status=500)