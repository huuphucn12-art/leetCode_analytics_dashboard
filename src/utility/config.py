from datetime import date

CATALOG_NAME = "leetprod"

BRONZE_SCHEMA = "bronze"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA = "gold"

VOLUME_NAME = "storage"

BRONZE_DIR = f"/Volumes/{CATALOG_NAME}/{BRONZE_SCHEMA}/{VOLUME_NAME}/"
SILVER_DIR = f"/Volumes/{CATALOG_NAME}/{SILVER_SCHEMA}/{VOLUME_NAME}/"
GOLD_DIR = f"/Volumes/{CATALOG_NAME}/{GOLD_SCHEMA}/{VOLUME_NAME}/"
GRAPHQL_URL = "https://leetcode.com/graphql"

YEARS = [2025, date.today().year]