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

# Bumped database name to v7 for clean filter initialization
DB_NAME = "raveradar_v7.db"

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

COUNTRIES_LIST = ["Singapore", "Malaysia", "Thailand", "Indonesia", "Vietnam", "Japan", "South Korea", "Philippines"]

GENRES_LIST = [
    "Techno", "Hard Techno", "Industrial", "Hardgroove", "Peak-Time (Drumcode)", 
    "Acid", "Rave", "Neo-Rave", "Schranz", "House", "Hard House",
    "Trance", "Acid Trance", "Psytrance", "Hardcore", "Hardstyle"
]

def fetch_single_ra_venue(ra_id, venue_name, country):
    events = []
    url = f"https://ra.co/clubs/{ra_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a_tag in soup.find_all('a', href=re.compile(r'/events/\d+')):
                title_text = a_tag.get_text(strip=True)
                if title_text and len(title_text) > 5 and "PRV" not in title_text:
                    events.append({
                        "title": title_text,
                        "venue": venue_name,
                        "country": country,
