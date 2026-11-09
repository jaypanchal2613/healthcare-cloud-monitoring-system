import os
import psycopg2


SLA_TARGET = 99.5


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "healthcare-db"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=5432
    )


def calculate_sla():
    connection = get_connection()
    cursor = connection.cursor()

    # Get monitoring records from the last 24 hours
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

    results = cursor.fetchall()

    print("\nHEALTHCARE CLOUD SLA REPORT")
    print("============================")
    print("Monitoring Period: Last 24 Hours")
    print("SLA Target:", SLA_TARGET, "%")

    if not results:
        print("\nNo monitoring records found in the last 24 hours.")

    for service, total, successful in results:

        availability = (successful / total) * 100

        compliance = (
            "COMPLIANT"
            if availability >= SLA_TARGET
            else "VIOLATION"
        )

        print("\nService:", service)
        print("Total Checks:", total)
        print("Successful Checks:", successful)
        print("Failed Checks:", total - successful)
        print("Availability:", round(availability, 2), "%")
        print("SLA Status:", compliance)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    calculate_sla()
