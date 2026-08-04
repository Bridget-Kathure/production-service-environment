import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)
service_name = os.environ.get('SERVICE_NAME', 'unknown')
sha = os.environ.get('GIT_SHA', 'dev')
upstream = os.environ.get('UPSTREAM_SERVICE', '')

@app.route('/')
def health():
    result = {
        "service": service_name,
        "sha": sha,
        "status": "ok"
    }
    if upstream:
        try:
            resp = requests.get(f"http://{upstream}/", timeout=5)
            result["upstream"] = resp.json()
        except Exception as e:
            result["upstream_error"] = str(e)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('APP_PORT', 3002)))
