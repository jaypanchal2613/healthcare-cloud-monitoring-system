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

    cursor.execute("""
        SELECT
            service_name,
            COUNT(*) AS total_checks,
            SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS successful_checks
        FROM monitoring_logs
        GROUP BY service_name
        ORDER BY service_name
    """)

    results = cursor.fetchall()

    print("\nHEALTHCARE CLOUD SLA REPORT")
    print("============================")
    print("SLA Target:", SLA_TARGET, "%")

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
        print("Availability:", round(availability, 2), "%")
        print("SLA Status:", compliance)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    calculate_sla()
