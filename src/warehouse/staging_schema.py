import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="logs/staging_schema.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

logging.info("Start staging...")

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

# create staging schema
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))

# Create staging table for raw data
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS staging.darkom_annonces(
                      annonce_id VARCHAR PRIMARY KEY,
                      date_publication TEXT,
                      titre VARCHAR,
                      ville VARCHAR,
                      quartier VARCHAR,
                      type_bien VARCHAR,
                      transaction VARCHAR,
                      prix DECIMAL,
                      surface DECIMAL,
                      nb_chambres DECIMAL,
                      nb_salles_bain DECIMAL,
                      etage DECIMAL,
                      annee_construction DECIMAL
        )
"""))
    
logging.info("Table staging.darkom_annonces created successfully")

# Read raw CSV file
df = pd.read_csv(r"C:\Users\HP\Desktop\101-flow-vd\darkom_annonces\darkom_annonces\data\darkom_annonces.csv")

logging.info(f"CSV loaded successfully with {len(df)} rows")

# Clean staging table before loading new data
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE staging.darkom_annonces"))

logging.info("Staging table truncated successfully")

# Drop duplicates
df = df.drop_duplicates(subset=['annonce_id'])
duplicates_ids = df['annonce_id'].duplicated().sum()

logging.info(f"Found {duplicates_ids} duplicate annonce_id values")

# Load raw data into PostgreSQL staging table
try:
    df.to_sql(
        "darkom_annonces",
        engine,
        if_exists="append",
        schema="staging",
        index=False,
        method="multi"
    )

    logging.info("Data loaded successfully into staging.darkom_annonces")

except Exception as e:
    logging.error(f"Error loading data into staging: {e}")

logging.info("Staging pipeline completed successfully")