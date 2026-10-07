import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "enterprise-reasoning", "messages": [{"role": "user", "content": "Solve this math problem"}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
for _ in range(5):
    with urllib.request.urlopen(req) as response:
        print("Routed to:", json.loads(response.read())['model'])
