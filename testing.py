from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType

# Output all advanced player season totals for the 2017-2018 season in JSON format to 2017_2018_player_season_totals.json
print("Writing advanced player season totals for 2021-2022 season to JSON file")
client.players_advanced_season_totals(season_end_year=2022, output_type=OutputType.JSON, output_file_path="./2021_2022_advanced_player_season_totals.json")