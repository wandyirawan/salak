import os
import psycopg2
from dotenv import load_dotenv
import glob
import re

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migrations():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Create migration table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Get applied migrations
    cur.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in cur.fetchall()}

    # Find migration files
    migrations = sorted(glob.glob("migrations/*.sql"))
    for mig_file in migrations:
        version = re.search(r"(\d+)_", os.path.basename(mig_file))
        if not version:
            continue
        ver = version.group(1)
        if ver in applied:
            print(f"Skip: {mig_file}")
            continue
        
        print(f"Apply: {mig_file}")
        with open(mig_file, 'r') as f:
            sql = f.read()
        cur.execute(sql)
        cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (ver,))
    
    conn.close()
    print("Migrations done.")

if __name__ == "__main__":
    run_migrations()
