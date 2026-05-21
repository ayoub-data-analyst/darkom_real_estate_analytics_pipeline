import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="logs/bi_schema.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

logging.info("Start bi_schema...")

# Database connection
load_dotenv()

def get_engine():
    try:
        engine = create_engine(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )

        logging.info("Database connection created successfully")
        return engine

    except Exception as e:
        logging.error(f"Error creating database connection: {e}")
        raise
engine = get_engine()

# create bi_schema
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS bi_schema"))

# Create staging table for raw data
with engine.begin() as conn:
    conn.execute(text("""
    
"""))