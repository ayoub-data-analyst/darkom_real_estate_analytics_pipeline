import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    filename="logs/feature_eng.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

logging.info("Start Feature Enginnering processe ...")

# load cleaned data
df = pd.read_csv(r"/home/ayoub/Desktop/darkom_annonces/data/cleaned_data.csv")


# Create price per square meter
df["prix_m2"] = (
    df["prix"] /
    df["surface"]
).round().astype("Int64")


# Create estimated property age
current_year = pd.Timestamp.now().year

df["age_bien"] = (
    current_year -
    df["annee_construction"]
)

# Create price categories
df["categorie_prix"] = pd.cut(
    df["prix"],
    bins=[
        0,
        300000,
        1000000,
        3000000,
        float("inf")
    ],
    labels=[
        "Economique",
        "Moyen",
        "Haut Standing",
        "Luxe"
    ]
)

# Create surface categories
df["categorie_surface"] = pd.cut(
    df["surface"],
    bins=[
        0,
        80,
        150,
        float("inf")
    ],
    labels=[
        "Petit",
        "Moyen",
        "Grand"
    ]
)

# Convert date_publication to datetime
df["date_publication"] = pd.to_datetime(
    df["date_publication"],
    errors="coerce"
)

# Create temporal dimensions
df["annee_publication"] = (
    df["date_publication"].dt.year
)

df["mois_publication"] = (
    df["date_publication"].dt.month
)

df["trimestre_publication"] = (
    df["date_publication"].dt.quarter
)

# FINAL STEP

logging.info("Start saving in CSV file")

df.to_csv("data/cleaned_feature_eng_data.csv", index=False)

logging.info("Feature engineering completed.")