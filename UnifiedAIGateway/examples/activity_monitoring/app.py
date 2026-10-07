import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "default", "messages": [{"role": "user", "content": "Hi"}], "user": "alice-123"}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Check gateway logs for Audit Event tracking alice-123.")
