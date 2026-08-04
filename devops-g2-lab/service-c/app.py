import os
from flask import Flask, jsonify

app = Flask(__name__)
service_name = os.environ.get('SERVICE_NAME', 'unknown')
sha = os.environ.get('GIT_SHA', 'dev')

@app.route('/')
def health():
    return jsonify({
        "service": service_name,
        "sha": sha,
        "status": "ok"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('APP_PORT', 3003)))
