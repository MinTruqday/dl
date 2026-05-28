import urllib.request
import json

token = "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"
model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"

data = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Bạn là ai?"}],
    "max_tokens": 100
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
})

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        print(res['choices'][0]['message']['content'])
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
