import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data_summary = {"model": "summarization-task", "messages": [{"role": "user", "content": "Summarize this."}]}
req_s = urllib.request.Request(url, data=json.dumps(data_summary).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_s) as response:
    print("Summary task routed to:", json.loads(response.read())['model'])

data_coding = {"model": "coding-task", "messages": [{"role": "user", "content": "Write code."}]}
req_c = urllib.request.Request(url, data=json.dumps(data_coding).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_c) as response:
    print("Coding task routed to:", json.loads(response.read())['model'])
