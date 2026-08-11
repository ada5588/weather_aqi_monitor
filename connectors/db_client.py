import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine

load_dotenv()

PROFILES = {
    "readonly": "POSTGRES_READONLY",
    "write": "POSTGRES_WRITE"
}

def get_postgres_connection(profile="readonly"):
    prefix = PROFILES[profile]
    return psycopg2.connect(
        host=os.getenv(f"{prefix}_HOST"),
        port=os.getenv(f"{prefix}_PORT", 5432),
        dbname=os.getenv(f"{prefix}_DB"),
        user=os.getenv(f"{prefix}_USER"),
        password=os.getenv(f"{prefix}_PASSWORD"),
    )

def get_sqlalchemy_engine(profile="write"):
    return create_engine(_build_database_url(profile))
