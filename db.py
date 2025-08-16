# db1.py
import os
import pandas as pd
import psycopg2
import streamlit as st
from psycopg2.extras import RealDictCursor

# Load local .env when present (so you can keep developing locally)
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Prefer environment variables, fallback to streamlit secrets
DB_HOST = os.getenv("DB_HOST") or st.secrets.get("DB_HOST")
DB_PORT = os.getenv("DB_PORT") or st.secrets.get("DB_PORT")
DB_NAME = os.getenv("DB_NAME") or st.secrets.get("DB_NAME")
DB_USER = os.getenv("DB_USER") or st.secrets.get("DB_USER")
DB_PASS = os.getenv("DB_PASS") or st.secrets.get("DB_PASS")

def get_connection():
    # If any of these are None, this will raise — good for failing fast
    conn = psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT) if DB_PORT else None,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode="require"  # Keeps it safe for hosted Postgres like Supabase; remove if not needed
    )
    return conn

def get_all_leads():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    return df

def insert_lead(name, contact, address, source, status, first_contacted=None, notes=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (name, contact_number, address, source, status, first_contacted, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (name, contact, address, source, status,
                 first_contacted if first_contacted is not None else None,
                 notes)
            )
        conn.commit()

def update_lead_status(
    lead_id,
    name,
    contact_number,
    source,
    status,
    first_contacted=None,
    notes=""
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get old status before update
            cur.execute("SELECT status FROM leads WHERE id=%s", (lead_id,))
            row = cur.fetchone()
            old_status = row[0] if row else None

            # Update the lead record
            cur.execute(
                """
                UPDATE leads
                SET name=%s,
                    contact_number=%s,
                    source=%s,
                    status=%s,
                    first_contacted=%s,
                    notes=%s,
                    updated_at=NOW()
                WHERE id=%s
                """,
                (
                    name,
                    contact_number,
                    source,
                    status,
                    first_contacted if first_contacted else None,
                    notes,
                    lead_id
                )
            )

            # Log into lead_history only if status actually changed
            if old_status and old_status != status:
                cur.execute(
                    """
                    INSERT INTO lead_history (lead_id, old_status, new_status, changed_at, notes)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    (lead_id, old_status, status, notes)
                )

        conn.commit()

def delete_lead(lead_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
        conn.commit()