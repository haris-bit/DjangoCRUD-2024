# my_script.py
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType

def get_player_box_scores(year, month, day):
    # Get all player box scores for the specified date
    return client.player_box_scores(day=day, month=month, year=year)

def save_player_box_scores_as_json(year, month, day, output_file_path):
    # Output player box scores as JSON to the specified file path
    client.player_box_scores(
        day=day,
        month=month,
        year=year,
        output_type=OutputType.JSON,
        output_file_path=output_file_path,
    )

# Example usage:
if __name__ == '__main__':
    # Specify the date and output file path
    year = 2019
    month = 1
    day = 1
    output_file_path = './1_1_2019_box_scores.json'

    # Call functions
    player_box_scores = get_player_box_scores(year, month, day)
    save_player_box_scores_as_json(year, month, day, output_file_path)
