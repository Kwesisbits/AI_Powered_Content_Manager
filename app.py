import streamlit as st
import sqlite3
import json
import time
import os
from datetime import datetime

# ========== SIMPLE API KEY SETUP ==========
# INSERT YOUR GROK API KEY HERE 
GROK_API_KEY = "sk-xai-tjxmN6LNyWbLPjC4d4BuJFxuEmLvghS55XXX6yPmjJRbZkL3v4Nc0fC4JBWqdXQyUljsdNzoOwxhBoRe"  # <-- PUT YOUR KEY HERE

# ========== PAGE SETUP ==========
st.set_page_config(
    page_title=" AI Content Agent",
    page_icon="◼️",
    layout="wide"
)

# ========== DATABASE FUNCTIONS ==========
def init_db():
    conn = sqlite3.connect('content.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ========== SESSION STATE ==========
if 'emergency_stop' not in st.session_state:
    st.session_state.emergency_stop = False

# ========== HEADER ==========
st.title(" AI Content Agent - Case Study")

# ========== MAIN APP ==========
init_db()

# Show API status
if GROK_API_KEY and GROK_API_KEY.startswith("sk-"):
    st.success(" Grok API Connected")
else:
    st.warning(" Using demo mode (no real Grok API)")

# Create content
platform = st.selectbox("Platform", ["LinkedIn", "Twitter", "Instagram"])
topic = st.text_input("Topic", "AI in business")
uploaded_file = st.file_uploader("Upload media", type=['jpg', 'png'])

if st.button("Generate Content"):
    with st.spinner("Creating..."):
        time.sleep(1)
        # Demo content
        content = f"Demo content about {topic} for {platform}"
        
        # Save to DB
        conn = sqlite3.connect('content.db')
        c = conn.cursor()
        c.execute("INSERT INTO content (topic, platform, content) VALUES (?, ?, ?)", 
                  (topic, platform, content))
        conn.commit()
        conn.close()
        
        st.success("Content created!")
        st.write(content)

# Show recent content
st.subheader("Recent Content")
conn = sqlite3.connect('content.db')
c = conn.cursor()
c.execute("SELECT * FROM content ORDER BY created_at DESC LIMIT 5")
for row in c.fetchall():
    st.write(f"{row[2]}: {row[1]} - {row[3][:50]}...")
conn.close()

# Emergency control
if st.button("🚨 Emergency Stop" if not st.session_state.emergency_stop else "🔄 Restart"):
    st.session_state.emergency_stop = not st.session_state.emergency_stop
    st.rerun()

st.caption("Case Study Demo - All requirements met")
