import streamlit as st
import sqlite3
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="RaveRadar SE Asia", page_icon="⚡", layout="centered")

# Custom CSS to give it a dark, premium underground club vibe
st.markdown("""
    <style>
    .main { background-color: #0d0e15; color: #ffffff; }
    h1, h2, h3 { color: #bc34fa !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #bc34fa; color: white; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #9a24cf; color: white; }
    .event-card { background-color: #161824; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 4px solid #bc34fa; }
    </style>
""", unsafe_allow_html=True)

DB_NAME = "raveradar.db"

def init_db():
    """Initializes the database structure."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, 
        city TEXT NOT NULL, rss_url TEXT, resident_advisor_id TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS manual_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, venue TEXT, 
        city TEXT, date TEXT, ticket_url TEXT
    )''')
    
    # Seed a couple default legendary spots if empty
    cursor.execute("SELECT COUNT(*) FROM venues")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('Tuff Club', 'Singapore', '', '154508'),
            ('Thug Shop / Headquarters', 'Singapore', '', '109556'),
            ('Verknipt Malaysia', 'Kuala Lumpur', '', '')
        ]
        cursor.executemany("INSERT INTO venues (name, city, rss_url, resident_advisor_id) VALUES (?,?,?,?)", defaults)
    conn.commit()
    conn.close()

init_db()

# --- APP NAVIGATION ---
st.title("⚡ RaveRadar SE Asia")
st.caption("Tracking the underground across Singapore, KL, and beyond. No Instagram required.")

tabs = st.tabs(["🎵 Upcoming Raves", "🏢 Venue Directory", "➕ Add Event/Venue"])

# --- TAB 1: UPCOMING RAVES ---
with tabs[0]:
    st.subheader("Live Lineups & Parties")
    
    # 1. Fetch Manual Submissions from DB
    conn = sqlite3.connect(DB_NAME)
    manual_df = pd.read_sql_query("SELECT title, venue, city, date, ticket_url FROM manual_events", conn)
    conn.close()
    
    # 2. Simulated Aggregator (Ready to connect to real RA/Ticketmelon RSS endpoints)
    # This acts as our instantly working showcase data matching your taste
    mock_events = [
        {"title": "Joyhauser (Extended Set)", "venue": "Headquarters", "city": "Singapore", "date": "2026-06-12", "url": "https://ra.co"},
        {"title": "Ben Klock x Thug Shop", "venue": "Tuff Club", "city": "Singapore", "date": "2026-06-20", "url": "https://ra.co"},
        {"title": "Verknipt Kuala Lumpur 2026", "venue": "Mega Star Arena", "city": "Kuala Lumpur", "date": "2026-07-04", "url": "https://ticketmelon.com"},
        {"title": "Jeff Mills - Outer Space Theories", "venue": "Wild Pearl Space", "city": "Singapore", "date": "2026-07-18", "url": "https://ra.co"}
    ]
    all_events = mock_events + manual_df.to_dict(orient='records')
    
    # Filter by City
    city_filter = st.selectbox("Filter by City", ["All Cities", "Singapore", "Kuala Lumpur"])
    
    for ev in all_events:
        if city_filter != "All Cities" and ev['city'] != city_filter:
            continue
            
        st.markdown(f"""
            <div class="event-card">
                <span style="float:right; background:#bc34fa; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{ev['city']}</span>
                <strong style="font-size:18px; color:#ffffff;">{ev['title']}</strong><br>
                <span style="color:#aaaaaa;">📍 {ev['venue']}</span> • <span style="color:#00ffcc;">📅 {ev['date']}</span>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Get Tickets / Info", ev['url'] if 'url' in ev else ev['ticket_url'])

# --- TAB 2: VENUE DIRECTORY ---
with tabs[1]:
    st.subheader("Tracked Collectives & Club Hubs")
    conn = sqlite3.connect(DB_NAME)
    venues_df = pd.read_sql_query("SELECT name as 'Name', city as 'City' FROM venues", conn)
    conn.close()
    st.dataframe(venues_df, use_container_width=True, hide_index=True)

# --- TAB 3: ADD EVENT / VENUE (ADMIN PANEL) ---
with tabs[2]:
    st.subheader("Crowdsource / Expand the Radar")
    
    option = st.radio("What do you want to add?", ["Single Event Announcement", "Permanent Club/Organizer Profile"])
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if option == "Single Event Announcement":
        with st.form("event_form", clear_on_submit=True):
            t = st.text_input("Event Name (e.g., Baby J Live)")
            v = st.text_input("Venue / Host Location")
            c = st.selectbox("City", ["Singapore", "Kuala Lumpur", "Bangkok", "Jakarta"])
            d = st.date_input("Event Date")
            link = st.text_input("Ticket or Event Info Link URL")
            
            if st.form_submit_button("Publish Event to Public Radar"):
                if t and v and link:
                    cursor.execute("INSERT INTO manual_events (title, venue, city, date, ticket_url) VALUES (?,?,?,?,?)", (t, v, c, str(d), link))
                    conn.commit()
                    st.success("🎉 Event added! Refresh the page to see it live.")
                    
    else:
        with st.form("venue_form", clear_on_submit=True):
            name = st.text_input("Club/Promoter Name")
            city = st.selectbox("Base City", ["Singapore", "Kuala Lumpur", "Bangkok"])
            ra_id = st.text_input("Resident Advisor Club ID (Optional)")
            
            if st.form_submit_button("Add Venue to Tracker"):
                if name:
                    cursor.execute("INSERT INTO venues (name, city, resident_advisor_id) VALUES (?,?,?)", (name, city, ra_id))
                    conn.commit()
                    st.success(f"Added {name} to the community directory!")
                    
    conn.close()
