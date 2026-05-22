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
        CREATE TABLE IF NOT EXISTS bi_schema.dim_date(
                date_id SERIAL PRIMARY KEY,
                date_publication DATE,
                annee_publication INT,
                mois_publication INT,
                trimestre_publication INT
        )
"""))

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bi_schema.dim_location(
                location_id SERIAL PRIMARY KEY,
                ville VARCHAR,
                quartier VARCHAR
        )
"""))
    
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bi_schema.dim_bien(
                bien_id SERIAL PRIMARY KEY,
                type_bien VARCHAR,
                categorie_surface VARCHAR              
        )
"""))

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bi_schema.dim_transaction(
                transaction_id SERIAL PRIMARY KEY,
                transaction VARCHAR,
                categorie_prix VARCHAR
        )
"""))

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS bi_schema.fact_annonces(
                annonce_id VARCHAR PRIMARY KEY,
                prix INT,
                surface DECIMAL,
                prix_m2 INT,
                nb_chambres INT,
                nb_salles_bain INT,
                etage INT,
                age_bien INT,
                date_id INT,
                location_id INT,
                bien_id INT,
                transaction_id INT,
                FOREIGN KEY (date_id) REFERENCES bi_schema.dim_date(date_id),
                FOREIGN KEY (location_id) REFERENCES bi_schema.dim_location(location_id),
                FOREIGN KEY (bien_id) REFERENCES bi_schema.dim_bien(bien_id),
                FOREIGN KEY (transaction_id) REFERENCES bi_schema.dim_transaction(transaction_id)
        )
"""))

logging.info("Tables of bi_schema created successfully")


# load csv
df = pd.read_csv(r"/home/ayoub/Desktop/darkom_annonces/data/cleaned_feature_eng_data.csv")

logging.info("Load csv successfully")


# Convert date_publication to datetime
df["date_publication"] = pd.to_datetime(
    df["date_publication"]
)

# Separate dimension tables
df_dim_date = df[
    [
        "date_publication",
        "annee_publication",
        "mois_publication",
        "trimestre_publication"
    ]
].drop_duplicates()

df_dim_location = df[
    [
        "ville",
        "quartier"
    ]
].drop_duplicates()

df_dim_bien = df[
    [
        "type_bien",
        "categorie_surface"
    ]
].drop_duplicates()

df_dim_transaction =  df[
    [
        "transaction",
        "categorie_prix"
    ]
].drop_duplicates()

logging.info("Dimension tables separated successfully")


with engine.begin() as conn:
    conn.execute(text("""
        TRUNCATE TABLE bi_schema.fact_annonces CASCADE;
        TRUNCATE TABLE bi_schema.dim_date CASCADE;
        TRUNCATE TABLE bi_schema.dim_location CASCADE;
        TRUNCATE TABLE bi_schema.dim_bien CASCADE;
        TRUNCATE TABLE bi_schema.dim_transaction CASCADE;
    """))

# Load dimension tables
df_dim_date.to_sql(
        "dim_date",
        engine,
        if_exists="append",
        schema="bi_schema",
        index=False
)

df_dim_location.to_sql(
        "dim_location",
        engine,
        if_exists="append",
        schema="bi_schema",
        index=False
)

df_dim_bien.to_sql(
        "dim_bien",
        engine,
        if_exists="append",
        schema="bi_schema",
        index=False
)

df_dim_transaction.to_sql(
        "dim_transaction",
        engine,
        if_exists="append",
        schema="bi_schema",
        index=False
)

logging.info("Dimension tables loaded successfully")


# Read dimension tables
dim_date = pd.read_sql(
    "SELECT * FROM bi_schema.dim_date",
    engine
)

# Convert dim_date column to datetime
dim_date["date_publication"] = pd.to_datetime(
    dim_date["date_publication"]
)

dim_location = pd.read_sql(
    "SELECT * FROM bi_schema.dim_location",
    engine
)

dim_bien = pd.read_sql(
    "SELECT * FROM bi_schema.dim_bien",
    engine
)

dim_transaction = pd.read_sql(
    "SELECT * FROM bi_schema.dim_transaction",
    engine
)

logging.info("Dimension tables loaded successfully")


# Merge dimension tables
df_fact_annonces = df.merge(
    dim_date,
    on=[
        "date_publication",
        "annee_publication",
        "mois_publication",
        "trimestre_publication"
    ],
    how="left"
)

df_fact_annonces = df_fact_annonces.merge(
    dim_location,
    on=[
        "ville",
        "quartier"
    ],
    how="left"
)

df_fact_annonces = df_fact_annonces.merge(
    dim_bien,
    on=[
        "type_bien",
        "categorie_surface"
    ],
    how="left"
)

df_fact_annonces = df_fact_annonces.merge(
    dim_transaction,
    on=[
        "transaction",
        "categorie_prix"
    ],
    how="left"
)

logging.info("Dimension IDs merged successfully")


df_fact_annonces = df_fact_annonces[
    [
        "annonce_id",
        "prix",
        "surface",
        "prix_m2",
        "nb_chambres",
        "nb_salles_bain",
        "etage",
        "age_bien",
        "date_id",
        "location_id",
        "bien_id",
        "transaction_id"
    ]
]

logging.info("Fact table created successfully")


df_fact_annonces.to_sql(
    name="fact_annonces",
    con=engine,
    schema="bi_schema",
    if_exists="append",
    index=False
)

logging.info("Fact table loaded successfully")


logging.info("bi_schema created successfully")