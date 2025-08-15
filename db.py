import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import create_engine, text


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# ✅ Persistent connection
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# ✅ Cached data fetch
@st.cache_data(ttl=30)  # cache for 30 seconds
def get_all_leads():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
    return df

# Insert, update, delete clear cache so changes reflect instantly
def insert_lead(name, contact, address, source, status, first_contacted, notes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leads (name, contact_number, address, source, status, first_contacted, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, contact, address, source, status, first_contacted, notes))
    conn.commit()
    st.cache_data.clear()


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def update_lead(
        lead_id,
        name,
        contact_number,
        source,
        status,
        first_contacted,
        notes
):
    """Update all editable fields for a lead."""
    with engine.connect() as conn:
        query = text("""
            UPDATE leads
            SET 
                name = :name,
                contact_number = :contact_number,
                source = :source,
                status = :status,
                first_contacted = :first_contacted,
                notes = :notes
            WHERE id = :lead_id
        """)

        conn.execute(query, {
            "lead_id": lead_id,
            "name": name,
            "contact_number": contact_number,
            "source": source,
            "status": status,
            "first_contacted": first_contacted,
            "notes": notes
        })
        conn.commit()
    st.cache_data.clear()

def delete_lead(lead_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    conn.commit()
    st.cache_data.clear()