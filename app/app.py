from flask import Flask, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "Healthcare Cloud Monitoring System",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route("/api/status")
def status():
    return jsonify({
        "application": "Healthcare Cloud Monitoring System",
        "status": "running",
        "service": "Flask"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
