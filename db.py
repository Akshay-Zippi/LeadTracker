import os
import pandas as pd
import psycopg2
import streamlit as st
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Load local .env when present
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

DB_HOST = os.getenv("DB_HOST") or st.secrets.get("DB_HOST")
DB_PORT = os.getenv("DB_PORT") or st.secrets.get("DB_PORT")
DB_NAME = os.getenv("DB_NAME") or st.secrets.get("DB_NAME")
DB_USER = os.getenv("DB_USER") or st.secrets.get("DB_USER")
DB_PASS = os.getenv("DB_PASS") or st.secrets.get("DB_PASS")

# --- SQLAlchemy Engine (for pandas) ---
password = quote_plus(DB_PASS)
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT) if DB_PORT else None,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode="require"
    )

# --- Cached Query for Leads ---
@st.cache_data(ttl=60)
def get_all_leads():
    return pd.read_sql("SELECT * FROM leads ORDER BY id DESC", engine)

def insert_lead(name, contact, address, source, status, first_contacted=None, notes=None, licence="no", scheduled_walk_in=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (name, contact_number, address, source, status, first_contacted, notes, licence, scheduled_walk_in)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (name, contact, address, source, status,
                 first_contacted if first_contacted else None,
                 notes, licence, scheduled_walk_in)
            )
        conn.commit()
    st.cache_data.clear()

def update_lead_status(
    lead_id,
    name,
    contact_number,
    source,
    status,
    first_contacted=None,
    notes="",
    licence="no",
    scheduled_walk_in=None
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM leads WHERE id=%s", (lead_id,))
            row = cur.fetchone()
            old_status = row[0] if row else None

            cur.execute(
                """
                UPDATE leads
                SET name=%s,
                    contact_number=%s,
                    source=%s,
                    status=%s,
                    first_contacted=%s,
                    notes=%s,
                    licence=%s,
                    scheduled_walk_in=%s,
                    updated_at=NOW()
                WHERE id=%s
                """,
                (name, contact_number, source, status,
                 first_contacted, notes, licence, scheduled_walk_in, lead_id)
            )

            if old_status and old_status != status:
                cur.execute(
                    """
                    INSERT INTO lead_history (lead_id, old_status, new_status, changed_at, notes)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    (lead_id, old_status, status, notes)
                )
        conn.commit()
    st.cache_data.clear()

def delete_lead(lead_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
        conn.commit()
    st.cache_data.clear()