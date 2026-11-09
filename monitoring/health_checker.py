import requests
import psycopg2
import os
import time


APP_URL = "http://127.0.0.1:5000/health"


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "healthcare-db"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=5432,
        connect_timeout=5
    )


def check_application():
    try:
        start_time = time.time()

        response = requests.get(APP_URL, timeout=5)

        response_time = (time.time() - start_time) * 1000

        return {
            "service": "Flask Application",
            "status": "UP" if response.status_code == 200 else "DOWN",
            "response_time_ms": round(response_time, 2)
        }

    except requests.RequestException:
        return {
            "service": "Flask Application",
            "status": "DOWN",
            "response_time_ms": None
        }


def check_database():
    try:
        connection = get_db_connection()
        connection.close()

        return {
            "service": "PostgreSQL Database",
            "status": "UP",
            "response_time_ms": None
        }

    except psycopg2.Error:
        return {
            "service": "PostgreSQL Database",
            "status": "DOWN",
            "response_time_ms": None
        }


def save_monitoring_result(result):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_logs (
            id SERIAL PRIMARY KEY,
            service_name VARCHAR(100) NOT NULL,
            status VARCHAR(10) NOT NULL,
            response_time_ms DECIMAL(10, 2),
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO monitoring_logs
        (service_name, status, response_time_ms)
        VALUES (%s, %s, %s)
    """, (
        result["service"],
        result["status"],
        result["response_time_ms"]
    ))

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    print("HEALTHCARE CLOUD MONITORING")
    print("---------------------------")

    results = [
        check_application(),
        check_database()
    ]

    for result in results:
        print(result)

        try:
            save_monitoring_result(result)
            print("Monitoring result saved successfully.")

        except psycopg2.Error as error:
            print("Could not save monitoring result:", error)
