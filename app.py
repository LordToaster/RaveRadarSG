import streamlit as st
import sqlite3
import pandas as pd
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

DB_NAME = "raveradarv2.db"

def init_db():
    """Initializes the database structure with Country support."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, 
        country TEXT NOT NULL, rss_url TEXT, resident_advisor_id TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS manual_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, venue TEXT, 
        country TEXT, date TEXT, ticket_url TEXT
    )''')
    
    # Seed default legendary spots if empty
    cursor.execute("SELECT COUNT(*) FROM venues")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('Tuff Club', 'Singapore', '', '154508'),
            ('Thug Shop / Headquarters', 'Singapore', '', '109556'),
            ('Verknipt Malaysia', 'Malaysia', '', '')
        ]
        cursor.executemany("INSERT INTO venues (name, country, rss_url, resident_advisor_id) VALUES (?,?,?,?)", defaults)
    conn.commit()
    conn.close()

init_db()

# --- APP NAVIGATION ---
st.title("⚡ RaveRadar SE Asia")
st.caption("Tracking the underground across East & Southeast Asia. No Instagram required.")

tabs = st.tabs(["🎵 Upcoming Raves", "🏢 Venue & Promoter Directory", "➕ Add Event/Venue"])

COUNTRIES_LIST = ["Singapore", "Malaysia", "Thailand", "Indonesia", "Japan", "South Korea", "Philippines"]

# --- TAB 1: UPCOMING RAVES ---
with tabs[0]:
    st.subheader("Live Lineups & Parties")
    
    # 1. Fetch Manual Submissions from DB
    conn = sqlite3.connect(DB_NAME)
    manual_df = pd.read_sql_query("SELECT title, venue, country, date, ticket_url FROM manual_events", conn)
    conn.close()
    
    # 2. Simulated Aggregator Data matching your favorite acts
    mock_events = [
        {"title": "Joyhauser (Extended Set)", "venue": "Headquarters, Singapore", "country": "Singapore", "date": "2026-06-12", "ticket_url": "https://ra.co"},
        {"title": "Ben Klock x Thug Shop", "venue": "Tuff Club, Singapore", "country": "Singapore", "date": "2026-06-20", "ticket_url": "https://ra.co"},
        {"title": "Verknipt Kuala Lumpur 2026", "venue": "Mega Star Arena, KL", "country": "Malaysia", "date": "2026-07-04", "ticket_url": "https://ticketmelon.com"},
        {"title": "Tomorrowland CORE Stage", "venue": "Pattaya", "country": "Thailand", "date": "2026-10-15", "ticket_url": "https://ticketmelon.com"},
        {"title": "Jeff Mills - Outer Space Theories", "venue": "Wild Pearl Space", "country": "Singapore", "date": "2026-07-18", "ticket_url": "https://ra.co"}
    ]
    
    # Combine everything together
    all_events = mock_events + manual_df.to_dict(orient='records')
    
    # Filter Dropdown based on Country
    country_filter = st.selectbox("Filter Feed by Country", ["All Countries"] + COUNTRIES_LIST)
    
    for ev in all_events:
        if country_filter != "All Countries" and ev['country'] != country_filter:
            continue
            
        st.markdown(f"""
            <div class="event-card">
                <span style="float:right; background:#bc34fa; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">{ev['country']}</span>
                <strong style="font-size:18px; color:#ffffff;">{ev['title']}</strong><br>
                <span style="color:#aaaaaa;">📍 {ev['venue']}</span> • <span style="color:#00ffcc;">📅 {ev['date']}</span>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Get Tickets / Info", ev['ticket_url'])

# --- TAB 2: VENUE DIRECTORY ---
with tabs[1]:
    st.subheader("Tracked Collectives & Club Hubs")
    conn = sqlite3.connect(DB_NAME)
    venues_df = pd.read_sql_query("SELECT name as 'Name', country as 'Country' FROM venues ORDER BY country ASC", conn)
    conn.close()
    st.dataframe(venues_df, use_container_width=True, hide_index=True)

# --- TAB 3: ADD EVENT / VENUE (ADMIN PANEL) ---
with tabs[2]:
    st.subheader("Expand the Radar")
    
    option = st.radio("What do you want to add?", ["Single Event Announcement", "Permanent Club/Organizer Profile"])
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if option == "Single Event Announcement":
        with st.form("event_form", clear_on_submit=True):
            t = st.text_input("Event Name (e.g., Baby J Live)")
            v = st.text_input("Venue & Specific Location (e.g., Green Mango, Koh Samui)")
            c = st.selectbox("Country Location", COUNTRIES_LIST)
            d = st.date_input("Event Date")
            link = st.text_input("Ticket Link / Event URL")
            
            if st.form_submit_button("Publish Event to Public Radar"):
                if t and v and link:
                    cursor.execute("INSERT INTO manual_events (title, venue, country, date, ticket_url) VALUES (?,?,?,?,?)", (t, v, c, str(d), link))
                    conn.commit()
                    st.success("🎉 Event added! Head to the main feed to see it.")
                    
    else:
        with st.form("venue_form", clear_on_submit=True):
            name = st.text_input("Club/Promoter Name (e.g., Mustache)")
            country = st.selectbox("Base Country", COUNTRIES_LIST)
            ra_id = st.text_input("Resident Advisor Club ID (Optional)")
            
            if st.form_submit_button("Add Venue to Tracker"):
                if name:
                    cursor.execute("INSERT INTO venues (name, country, resident_advisor_id) VALUES (?,?,?)", (name, country, ra_id))
                    conn.commit()
                    st.success(f"Added {name} to the collective directory!")
                    
    conn.close()
