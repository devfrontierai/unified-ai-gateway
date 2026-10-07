import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "expensive-model", "messages": [{"role": "user", "content": "Write a long essay."}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Check gateway logs for cost estimation.")
