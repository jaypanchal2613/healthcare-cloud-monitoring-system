
from flask import Flask, jsonify, render_template, request
from datetime import datetime
from database import get_connection

app = Flask(__name__)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INTEGER NOT NULL,
            condition VARCHAR(150) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


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


@app.route("/api/patients", methods=["GET"])
def get_patients():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, age, condition, created_at
        FROM patients
        ORDER BY id
    """)

    records = cursor.fetchall()

    patients = []

    for record in records:
        patients.append({
            "id": record[0],
            "name": record[1],
            "age": record[2],
            "condition": record[3],
            "created_at": record[4].isoformat()
        })

    cursor.close()
    connection.close()

    return jsonify(patients), 200


@app.route("/api/patients", methods=["POST"])
def add_patient():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    age = data.get("age")
    condition = data.get("condition")

    if (
        not name
        or not isinstance(age, int)
        or isinstance(age, bool)
        or age <= 0
        or not condition
    ):
        return jsonify({
            "error": "Please provide valid name, age and condition"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO patients (name, age, condition)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (name, age, condition))

    patient_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({
        "message": "Patient record added successfully",
        "patient_id": patient_id
    }), 201


init_db()
