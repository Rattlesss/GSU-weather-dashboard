import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # reads .env into environment variables

def get_config(key):
    value = os.getenv(key)
    if value is None:
        try:
            import streamlit as st
            value = st.secrets.get(key)
        except Exception:
            pass
    return value

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl_ca": "../certs/ca.pem"}
)

if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("Connected successfully!")
    except Exception as e:
        print("Connection failed.")
        print(f"Error: {e}")
