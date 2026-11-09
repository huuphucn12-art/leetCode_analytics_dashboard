import os
from dotenv import load_dotenv, find_dotenv
from databricks import sql
from .config import CATALOG_NAME, GOLD_SCHEMA

load_dotenv(find_dotenv(), override=True)

connection = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_HTTP_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"),
    catalog=CATALOG_NAME,
    schema=GOLD_SCHEMA,
)
