# make sure to turn your django sever on in order to consume your RESTFUL API

import requests

response = requests.get('http://127.0.0.1:8000/drinks')

print(response.json())