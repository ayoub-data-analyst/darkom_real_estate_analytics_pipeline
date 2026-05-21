import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="logs/cleaning.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

logging.info("Start cleaning...")

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

query = "SELECT * FROM staging.darkom_annonces"

df = pd.read_sql(query, engine)

# =============================
# STEP 1 : Basic text cleaning
# =============================

logging.info("STEP 1 START - Basic text cleaning")

# Clean ville column
ville_mapping = {
    "casablanca": "Casablanca",
    "casa": "Casablanca",

    "rabat": "Rabat",

    "marrakech": "Marrakech",

    "fès": "Fes",
    "fes": "Fes",

    "tanger": "Tanger",

    "agadir": "Agadir",

    "meknès": "Meknes",
    "meknes": "Meknes",

    "oujda": "Oujda",

    "kenitra": "Kenitra",

    "tétouan": "Tetouan",
    "tetouan": "Tetouan",
}

df["ville"] = (
    df["ville"]
    .str.strip()
    .str.lower()
    .replace(ville_mapping)
)

logging.info("STEP 1 END - Basic cleaning completed")
 
# ========================
# STEP 2 : FIX DATA TYPES
# ========================

logging.info("STEP 2 START - Converting data types")

# Convert date_publication column to datetime
df["date_publication"] = pd.to_datetime(
    df["date_publication"],
    errors="coerce"
)

# Convert numeric columns from float to integer
numeric_columns = [
    "prix",
    "nb_chambres",
    "nb_salles_bain",
    "etage",
    "annee_construction"
]

for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).round().astype("Int64")

# Convert string columns to category dtype
df[["type_bien", "transaction"]] = (
    df[["type_bien", "transaction"]]
    .astype("category")
)

logging.info("STEP 2 END - Data types converted")


# ===============================
# STEP 3 : HANDLE MISSING VALUES
# ===============================

logging.info("STEP 3 START - Handling missing values")

# Fix missing values in date_publication column (5% missing values)
df = df.sort_values("date_publication").reset_index(drop=True)

df["date_publication"] = (
    df["date_publication"]
    .ffill()
    .bfill()
)

# Fix missing values in quartier column (27% missing values)
df["quartier"] = df.groupby("ville")["quartier"].transform(
    lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown")
)

# Fix missing values in type_bien column (2.5% missing values)

# Extract type_bien from titre
def extract_type_bien(title):

    title = title.lower()

    if "appartement" in title:
        return "Appartement"

    elif "villa" in title:
        return "Villa"

    elif "bureau" in title:
        return "Bureau"

    elif "terrain" in title:
        return "Terrain"

    elif "duplex" in title:
        return "Duplex"

    else:
        return None

df["type_bien"] = df["type_bien"].fillna(
    df["titre"].apply(extract_type_bien)
)

# Fix missing values in transaction column (2.5% missing values)
def fill_transaction(row):

    if pd.notna(row["transaction"]):
        return row["transaction"]

    if row["prix"] <= 30000:
        return "Location"

    else:
        return "Vente"

df["transaction"] = df.apply(
    fill_transaction,
    axis=1
)

# Fix missing values in nb_chambres (8.5%), nb_salles_bain (6.9%), and etage (15.4%)
columns_to_fill = [
    "nb_chambres",
    "nb_salles_bain",
    "etage"
]

for col in columns_to_fill:

    df.loc[
        df["type_bien"] == "Terrain",
        col
    ] = df.loc[
        df["type_bien"] == "Terrain",
        col
    ].fillna(0)

for col in columns_to_fill:

    df[col] = df.groupby("type_bien")[col].transform(
        lambda x: x.fillna(x.median())
    )

# Fix missing values in anne_construction (13.5% missing values)
df["annee_construction"] = df.groupby(
    ["ville", "type_bien"]
)["annee_construction"].transform(
    lambda x: x.fillna(round(x.median()))
)

logging.info("STEP 3 END - Missing values handled")


# =========================
# STEP 4 : HANDLE OUTLIERS
# =========================

logging.info("STEP 4 START - Detecting outliers")

# Function to detect outliers using IQR
def detect_outliers(df, column):

    # Calculate quartiles
    Q1 = df[column].quantile(0.25)

    Q3 = df[column].quantile(0.75)

    # Calculate IQR
    IQR = Q3 - Q1

    # Define bounds
    lower_bound = Q1 - (1.5 * IQR)

    upper_bound = Q3 + (1.5 * IQR)

    # Detect outliers
    outliers = df[
        (df[column] < lower_bound) |
        (df[column] > upper_bound)
    ]

    # Calculate percentage
    percentage = (
        len(outliers) / len(df)
    ) * 100

    # Print results
    print("=" * 50)

    print(f"Column: {column}")

    print(f"Outliers count: {len(outliers)}")

    print(f"Outliers percentage: {percentage:.2f}%")

    print("=" * 50)

    return outliers

# Detect outliers
prix_outliers = detect_outliers(df, "prix")

surface_outliers = detect_outliers(df, "surface")

chambres_outliers = detect_outliers(df, "nb_chambres")

sdb_outliers = detect_outliers(df, "nb_salles_bain")

# Calculate total outliers percentage
total_outliers = (
    len(prix_outliers) +
    len(surface_outliers) +
    len(chambres_outliers) +
    len(sdb_outliers)
)

total_percentage = (
    total_outliers / len(df)
) * 100

print("\n" + "=" * 50)

print(f"Total outliers: {total_outliers}")

print(f"Total outliers percentage: {total_percentage:.2f}%")

print("=" * 50)

# Remove unrealistic outliers
df = df[df["surface"] >= 30]

df = df[df["nb_chambres"] <= 10]

df = df[df["nb_salles_bain"] <= 6]

df = df[df["prix"] <= 20000000]

logging.info("STEP 4 END - Outliers handled successfully")


# ===========
# FINAL STEP
# ===========

logging.info("Start saving in CSV file")

df.to_csv("data/cleaned_data.csv", index=False)

logging.info("Cleaning pipeline completed successfully")