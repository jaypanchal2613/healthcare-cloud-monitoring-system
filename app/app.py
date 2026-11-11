from flask import Flask, jsonify, render_template, request
from datetime import datetime
from database import get_connection
from werkzeug.exceptions import HTTPException
import boto3
import os

app = Flask(__name__)

SLA_TARGET = 99.5

# CloudWatch configuration
CLOUDWATCH_NAMESPACE = "Healthcare/Application"


# Handle unexpected application errors
@app.errorhandler(Exception)
def handle_application_error(error):

    # Do not count normal HTTP errors such as 404
    if isinstance(error, HTTPException):
        return error

    # Write the error to application logs
    app.logger.exception("Unexpected application error")

    try:
        # Connect to CloudWatch using the EC2 IAM role
        cloudwatch = boto3.client(
            "cloudwatch",
            region_name=os.getenv("AWS_REGION", "ap-southeast-2")
        )

        # Publish application error metric
        cloudwatch.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=[
                {
                    "MetricName": "ApplicationErrorCount",
                    "Value": 1,
                    "Unit": "Count"
                }
            ]
        )

        app.logger.info("Application error metric published to CloudWatch")

    except Exception:
        # Monitoring failure must not hide the original application error
        app.logger.exception("Failed to publish metric to CloudWatch")

    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected application error occurred."
    }), 500



# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Application health check
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "Healthcare Cloud Monitoring System",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# Application status
@app.route("/api/status")
def status():
    return jsonify({
        "application": "Healthcare Cloud Monitoring System",
        "status": "running",
        "service": "Flask"
    }), 200


# Get all patient records
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


# Add a patient record
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


# Monitoring dashboard API
@app.route("/api/monitoring")
def get_monitoring_data():
    connection = get_connection()
    cursor = connection.cursor()

    # Get latest status of each service
    cursor.execute("""
        SELECT DISTINCT ON (service_name)
            service_name,
            status,
            response_time_ms,
            checked_at
        FROM monitoring_logs
        ORDER BY service_name, checked_at DESC
    """)

    latest_records = cursor.fetchall()
    services = []

    for record in latest_records:
        services.append({
            "service": record[0],
            "status": record[1],
            "response_time_ms": (
                float(record[2]) if record[2] is not None else None
            ),
            "checked_at": record[3].isoformat()
        })

    # Calculate availability during the last 24 hours
    cursor.execute("""
        SELECT
            service_name,
            COUNT(*) AS total_checks,
            COUNT(*) FILTER (WHERE status = 'UP') AS successful_checks
        FROM monitoring_logs
        WHERE checked_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        GROUP BY service_name
        ORDER BY service_name
    """)

    availability_records = cursor.fetchall()
    availability = []

    for record in availability_records:
        total = record[1]
        successful = record[2]
        failed = total - successful

        percentage = (successful / total) * 100 if total else 0

        availability.append({
            "service": record[0],
            "total_checks": total,
            "successful_checks": successful,
            "failed_checks": failed,
            "availability": round(percentage, 2),
            "sla_status": (
                "COMPLIANT"
                if percentage >= SLA_TARGET
                else "VIOLATION"
            )
        })

    # Get latest 10 monitoring records
    cursor.execute("""
        SELECT service_name, status, response_time_ms, checked_at
        FROM monitoring_logs
        ORDER BY checked_at DESC
        LIMIT 10
    """)

    history_records = cursor.fetchall()
    history = []

    for record in history_records:
        history.append({
            "service": record[0],
            "status": record[1],
            "response_time_ms": (
                float(record[2]) if record[2] is not None else None
            ),
            "checked_at": record[3].isoformat()
        })

    cursor.close()
    connection.close()

    return jsonify({
        "services": services,
        "availability": availability,
        "history": history,
        "sla_target": SLA_TARGET,
        "monitoring_period": "Last 24 Hours",
        "availability_method": "Check-based"
    }), 200


# Initialize database
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


init_db()

