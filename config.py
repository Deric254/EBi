import os

DB_PATH = os.getenv("SQLITE_DB_PATH", "ebi_data.db")

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "@mw(MYS)ti254")
}
