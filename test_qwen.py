import requests

# Define the local Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Define the payload with the prompt
payload = {
    "model": "qwen2.5:latest",
    "prompt": "What is AI?",
    "stream": False
}

# Send request to Ollama
response = requests.post(OLLAMA_API_URL, json=payload)

# Print response
print(response.json()["response"])
