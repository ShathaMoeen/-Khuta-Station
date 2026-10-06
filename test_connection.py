import psycopg
from db_config import psycopg_dsn

with psycopg.connect(psycopg_dsn()) as conn:
    print("الاتصال نجح")
    print(conn.execute("SELECT version()").fetchone()[0])
