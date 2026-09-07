import requests

API_URL = "http://127.0.0.1:8000/query"
query = {"query": "How much experience does Bharath have?"}

response = requests.post(API_URL, json=query)
print(response.json())