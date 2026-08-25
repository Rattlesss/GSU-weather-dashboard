import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # reads .env into environment variables (local dev only)

def get_config(key):
    value = os.getenv(key)
    if value is None:
        try:
            import streamlit as st
            value = st.secrets.get(key)
        except Exception:
            pass
    return value

DB_HOST = get_config("DB_HOST")
DB_PORT = get_config("DB_PORT")
DB_USER = get_config("DB_USER")
DB_PASSWORD = get_config("DB_PASSWORD")
DB_NAME = get_config("DB_NAME")
DB_USE_SSL = str(get_config("DB_USE_SSL") or "").lower() in ("1", "true", "yes")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

connect_args = {}
if DB_USE_SSL:
    # Build an absolute path to the cert, based on this file's own location —
    # works no matter what directory the app is actually run from.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CERT_PATH = os.path.join(BASE_DIR, "..", "certs", "ca.pem")
    connect_args["ssl_ca"] = CERT_PATH

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

if __name__ == "__main__":
    with engine.connect() as conn:
        print("Connected successfully!")
