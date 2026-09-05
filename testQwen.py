import requests

response = requests.post(
	"http://localhost:11434/api/generate",
	json={"model": "qwen2.5:latest", "prompt": "What is AI?", "stream": True}
)

print(response.json()["response"])