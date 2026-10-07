import urllib.request, json
# Pretend we are the OpenAI client calling the Gateway
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Migration successful! Received:", response.read().decode())
