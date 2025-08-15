import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, date

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


# ✅ Insert Lead
def insert_lead(name, contact, address, source, status, first_contacted, notes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leads (name, contact_number, address, source, status, first_contacted, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, contact, address, source, status, first_contacted, notes))
    conn.commit()
    st.cache_data.clear()


# ✅ Full Lead Update (name, contact, source, status, first_contacted, notes)

def update_lead_status(lead_id, name, contact_number, source, status, first_contacted, notes):
    conn = get_connection()
    cur = conn.cursor()

    # ✅ Normalize first_contacted to a proper datetime or None
    if isinstance(first_contacted, date) and not isinstance(first_contacted, datetime):
        first_contacted = datetime.combine(first_contacted, datetime.min.time())
    elif first_contacted in ("", None):
        first_contacted = None

    cur.execute("""
        UPDATE leads 
        SET name = %s, contact_number = %s, source = %s, status = %s, first_contacted = %s, notes = %s, updated_at = NOW()
        WHERE id = %s
    """, (name, contact_number, source, status, first_contacted, notes, lead_id))

    conn.commit()
    st.cache_data.clear()


# ✅ Delete Lead
def delete_lead(lead_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    conn.commit()
    st.cache_data.clear()