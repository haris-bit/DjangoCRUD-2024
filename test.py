from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType

# Retrieve the JSON data
standings_data = client.standings(season_end_year=2019, output_type=OutputType.JSON)

# Specify the output file name
output_file = 'output.json'

# Write the JSON data to the output file
with open(output_file, 'w') as file:
    file.write(standings_data)

print(f"JSON data has been saved to {output_file}")
