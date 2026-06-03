 import streamlit as st
import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="RaveRadar SE Asia", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0d0e15; color: #ffffff; }
    h1, h2, h3 { color: #bc34fa !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #bc34fa; color: white; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #9a24cf; color: white; }
    .event-card { background-color: #161824; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 4px solid #bc34fa; }
    </style>
""", unsafe_allow_html=True)

# Incremented database name to load all the new regional pre-sets
DB_NAME = "raveradar_final.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, 
        country TEXT NOT NULL, resident_advisor_id TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS manual_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, venue TEXT, 
        country TEXT, genre TEXT, date TEXT, ticket_url TEXT
    )''')
    
    cursor.execute("SELECT COUNT(*) FROM venues")
    if cursor.fetchone()[0] == 0:
        # Full master regional network hardcoded right into the database foundation
        defaults = [
            # Singapore
            ('Headquarters', 'Singapore', '119385'),
            ('Tuff Club', 'Singapore', '154508'),
            ('Mdlr', 'Singapore', '220686'),
            ('RASA', 'Singapore', '231502'),
            ('Wild Pearl', 'Singapore', '221487'),
            
            # Malaysia
            ('The Crane KL', 'Malaysia', '222135'),
            ('Over & Above KL', 'Malaysia', '226012'),
            ('Pisco Bar', 'Malaysia', '62181'),
            ('Wet Deck (W Hotel)', 'Malaysia', '163539'),
            
            # Thailand
            ('Mustache Bar (Bangkok)', 'Thailand', '102144'),
            ('Decommune (Bangkok)', 'Thailand', '198547'),
            ('Never Say Never (BKK)', 'Thailand', '217035'),
            ('Sing Sing Theater', 'Thailand', '108390'),
            
            # Indonesia
            ('Klymax Discotheque', 'Indonesia', '218451'),
            ('Vault Bali', 'Indonesia', '173003'),
            ('Red Ruby (Bali)', 'Indonesia', '137976'),
            ('Zodiac Jakarta', 'Indonesia', '176219'),
            
            # Japan
            ('WOMB (Tokyo)', 'Japan', '1643'),
            ('VENT (Tokyo)', 'Japan', '116035'),
            ('Circus Tokyo', 'Japan', '105191'),
            ('Ohjo Bldg (Shinjuku)', 'Japan', '221957'),
            ('Enter Shibuya', 'Japan', '214227'),
            
            # South Korea
            ('Faust (Itaewon)', 'South Korea', '106806'),
            ('vurt.', 'South Korea', '96227'),
            ('Atelier Space', 'South Korea', '244226'),
            ('Flac Seoul', 'South Korea', '284350'),
            ('Volnost', 'South Korea', '132644')
        ]
        cursor.executemany("INSERT INTO venues (name, country, resident_advisor_id) VALUES (?,?,?)", defaults)
    conn.commit()
    conn.close()

init_db()

# --- APP CONFIGURATIONS ---
st.title("⚡ RaveRadar SE Asia")
st.caption("The ultimate underground hub. Filtered by sound, completely decentralized.")

tabs = st.tabs(["🎵 Upcoming Raves", "🏢 Venue & Promoter Directory", "➕ Add Event/Venue"])

COUNTRIES_LIST = ["Singapore", "Malaysia", "Thailand", "Indonesia", "Japan", "South Korea", "Philippines"]

GENRES_LIST = [
    "Techno", "Hard Techno", "Industrial", "Hardgroove", "Peak-Time (Drumcode)", 
    "Acid", "Rave", "Neo-Rave", "Schranz", "House", "Hard House",
    "Trance", "Acid Trance", "Psytrance", "Hardcore", "Hardstyle"
]

def fetch_live_ra_events(ra_id, venue_name, country):
    events = []
    if not ra_id:
        return events
        
    url = f"https://ra.co/clubs/{ra_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"}
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a_tag in soup.find_all('a', href=re.compile(r'/events/\d+')):
                title_text = a_tag.get_text(strip=True)
                if title_text and len(title_text) > 5 and "PRV" not in title_text:
                    full_url = f"https://ra.co{a_tag['href']}"
                    events.append({
                        "title": title_text,
                        "venue": venue_name,
                        "country": country,
                        "genre": "Techno",  
                        "date": "Upcoming Lineup",
                        "ticket_url": full_url
                    })
    except Exception:
        pass
    return events

# --- TAB 1: UPCOMING RAVES ---
with tabs[0]:
    st.subheader("Live Lineups & Parties")
    
    col1, col2 = st.columns(2)
    with col1:
        country_filter = st.selectbox("Filter Country", ["All Countries"] + COUNTRIES_LIST)
    with col2:
        genre_filter = st.selectbox("Filter Genre/Sound", ["All Genres"] + GENRES_LIST)
        
    conn = sqlite3.connect(DB_NAME)
    manual_df = pd.read_sql_query("SELECT title, venue, country, genre, date, ticket_url FROM manual_events", conn)
    venues_to_scan = conn.execute("SELECT resident_advisor_id, name, country FROM venues WHERE resident_advisor_id != ''").fetchall()
    conn.close()
    
    live_events = []
    for ra_id, v_name, v_country in venues_to_scan:
        live_events.extend(fetch_live_ra_events(ra_id, v_name, v_country))
        
    all_events = live_events + manual_df.to_dict(orient='records')
    
    seen_links = set()
    display_count = 0
    
    for ev in all_events:
        if ev['ticket_url'] in seen_links:
            continue
        if country_filter != "All Countries" and ev['country'] != country_filter:
            continue
        if genre_filter != "All Genres" and ev['genre'] != genre_filter:
            continue
            
        seen_links.add(ev['ticket_url'])
        display_count += 1
        
        st.markdown(f"""
            <div class="event-card">
                <span style="float:right; background:#bc34fa; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; color:white; margin-left:5px;">{ev['country']}</span>
                <span style="float:right; background:#333; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; color:#00ffcc;">{ev['genre']}</span>
                <strong style="font-size:18px; color:#ffffff;">{ev['title']}</strong><br>
                <span style="color:#aaaaaa;">📍 {ev['venue']}</span> • <span style="color:#bc34fa; font-weight:bold;">📅 {ev['date']}</span>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Get Event Info / Tickets", ev['ticket_url'])

    if display_count == 0:
        st.info("No active events found matching those exact filters. Head to the 'Add' tab to publish one!")

# --- TAB 2: VENUE DIRECTORY ---
with tabs[1]:
    st.subheader("Tracked Collectives & Club Hubs")
    conn = sqlite3.connect(DB_NAME)
    venues_df = pd.read_sql_query("SELECT name as 'Name', country as 'Base Country', resident_advisor_id as 'RA System ID' FROM venues ORDER BY country ASC", conn)
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
            t = st.text_input("Event Name (e.g., Verknipt KL / Joyhauser Extended)")
            v = st.text_input("Venue & Location Details (e.g., Tuff Club, Singapore)")
            c = st.selectbox("Country Location", COUNTRIES_LIST)
            g = st.selectbox("Primary Sound/Genre", GENRES_LIST)
            d = st.date_input("Event Date")
            link = st.text_input("Direct Ticket / Checkout URL")
            
            if st.form_submit_button("Publish Event to Public Radar"):
                if t and v and link:
                    cursor.execute("INSERT INTO manual_events (title, venue, country, genre, date, ticket_url) VALUES (?,?,?,?,?,?)", (t, v, c, g, str(d), link))
                    conn.commit()
                    st.success("🎉 Event successfully uploaded and categorized!")
                    st.balloons()
                    
    else:
        with st.form("venue_form", clear_on_submit=True):
            name = st.text_input("Club or Promoter Name")
            country = st.selectbox("Base Country", COUNTRIES_LIST)
            ra_id = st.text_input("Resident Advisor Club ID Number")
            st.caption("Tip: If the web address is ra.co/clubs/154508, the ID number is 154508.")
            
            if st.form_submit_button("Add Venue to Tracker"):
                if name:
                    cursor.execute("INSERT INTO venues (name, country, resident_advisor_id) VALUES (?,?,?)", (name, country, ra_id))
                    conn.commit()
                    st.success(f"Successfully added {name} to the core scanning rotation!")
                    
    conn.close()
