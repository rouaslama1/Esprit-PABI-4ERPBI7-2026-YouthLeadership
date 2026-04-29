import os
from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder='.')

BASE = os.path.dirname(__file__)
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "http://localhost:8010")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/health')
def api_health():
    try:
        response = requests.get(f"{PREDICTION_API_URL}/health", timeout=5)
        return jsonify({"prediction_api_status": response.json()})
    except Exception as exc:
        return jsonify({"prediction_api_status": "unreachable", "error": str(exc)}), 503

if __name__ == '__main__':
    app.run(debug=True, port=5050)
