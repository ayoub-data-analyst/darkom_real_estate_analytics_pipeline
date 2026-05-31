import logging

logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:

    print("1. Creating staging schema...")
    import src.warehouse.staging_schema

    print("2. Cleaning data...")
    import src.warehouse.clean.cleaning

    print("3. Feature engineering...")
    import Feature_Engineering.feature_engineering

    print("4. Creating BI schema...")
    import src.warehouse.bi_schema

    print("Pipeline finished successfully")
    logging.info("Pipeline finished successfully")

except Exception as e:

    print(f"Error: {e}")
    logging.error(f"Pipeline failed: {e}")