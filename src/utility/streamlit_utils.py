import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from databricks import sql
from .config import CATALOG_NAME, GOLD_SCHEMA

load_dotenv(find_dotenv(), override=True)

connection = sql.connect(
    server_hostname=st.secrets["DATABRICKS_HOST"],
    http_path=st.secrets["DATABRICKS_HTTP_PATH"],
    access_token=st.secrets["DATABRICKS_TOKEN"],
    catalog=CATALOG_NAME,
    schema=GOLD_SCHEMA,
)
