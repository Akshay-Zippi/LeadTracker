import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

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

def update_lead_status(lead_id, new_status, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE leads 
        SET status=%s, notes=%s, updated_at=NOW()
        WHERE id=%s
    """, (new_status, notes, lead_id))

    cur.execute("""
        INSERT INTO lead_history (lead_id, old_status, new_status, changed_at, notes)
        SELECT id, status, %s, NOW(), %s FROM leads WHERE id=%s
    """, (new_status, notes, lead_id))

    conn.commit()
    st.cache_data.clear()

def delete_lead(lead_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    conn.commit()
    st.cache_data.clear()