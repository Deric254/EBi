import os
import mysql.connector

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "sql12.freesqldatabase.com"),
    "user": os.getenv("MYSQL_USER", "sql12795574"),
    "password": os.getenv("MYSQL_PASSWORD", "KWPjrJmFfQ"),
    "database": os.getenv("MYSQL_DB", "sql12795574"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}

def get_connection():
    """Establish and return a MySQL connection using DB_CONFIG."""
    return mysql.connector.connect(**DB_CONFIG)

# Example usage
if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    print("Tables in database:", cursor.fetchall())
    conn.close()
