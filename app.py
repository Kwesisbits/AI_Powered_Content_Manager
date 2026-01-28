import streamlit as st
import sqlite3
import json
import time
import os
from datetime import datetime
from grok_agent import GrokContentAgent, BrandVoice
from database import init_db, save_content, get_pending_approvals, approve_content, reject_content

# Page config
st.set_page_config(
    page_title="AI Content Agent",
    page_icon="⚫",
    layout="wide"
)

# Initialize database
init_db()

# Initialize session state
if 'emergency_stop' not in st.session_state:
    st.session_state.emergency_stop = False
if 'mode' not in st.session_state:
    st.session_state.mode = "manual_review"

# Brand voice configuration
BRAND_VOICE = BrandVoice(
    company_name="TechCorp",
    tone="professional yet approachable",
    personality_traits=["Expert", "Innovative", "Trustworthy"],
    target_audience="tech professionals, CTOs, developers"
)

# Header with emergency controls
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("🤖 AI Content Agent")
with col2:
    if st.button("🚨 Emergency Stop", type="secondary"):
        st.session_state.emergency_stop = True
        st.error("All automation stopped!")
        time.sleep(2)
        st.rerun()
with col3:
    if st.session_state.emergency_stop:
        if st.button("🔄 Restart System"):
            st.session_state.emergency_stop = False
            st.success("System restarted!")
            time.sleep(1)
            st.rerun()

# Mode selector
mode = st.radio(
    "System Mode:",
    ["Manual Review", "Auto-Draft Only", "Full Auto"],
    horizontal=True,
    disabled=st.session_state.emergency_stop
)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Create", "Approve", "Schedule", "Monitor"])

with tab1:
    # Content Creation
    st.header("Create Content")
    
    col1, col2 = st.columns(2)
    
    with col1:
        platform = st.selectbox("Platform", ["LinkedIn", "Twitter", "Instagram"])
        topic = st.text_input("Topic", "The future of AI in business")
        
        # Media upload
        uploaded_file = st.file_uploader("Upload media (optional)", 
                                       type=['jpg', 'png', 'jpeg', 'mp4'])
        media_context = None
        if uploaded_file:
            # Save file temporarily
            os.makedirs("uploads", exist_ok=True)
            file_path = f"uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            media_context = f"Uploaded: {uploaded_file.name}"
            st.image(uploaded_file, width=200)
        
        if st.button("Generate Content", disabled=st.session_state.emergency_stop):
            with st.spinner("Creating content with Grok..."):
                # Initialize agent
                agent = GrokContentAgent(api_key=st.secrets.get("GROK_API_KEY", "demo"))
                
                # Generate content
                content = agent.generate_platform_content(
                    platform=platform,
                    topic=topic,
                    brand_voice=BRAND_VOICE,
                    media_context=media_context
                )
                
                # Save to database
                content_id = save_content(
                    content=content,
                    platform=platform,
                    topic=topic,
                    status="pending"
                )
                
                st.success(f"Content created! ID: {content_id}")
                st.divider()
                
                # Display content
                st.subheader("Generated Content:")
                st.write(content.get("post_text", ""))
                st.caption(f"Hashtags: {', '.join(content.get('hashtags', []))}")
                st.caption(f"Optimal time: {content.get('optimal_post_time', 'N/A')}")
                
                # Quick actions
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Submit for Approval"):
                        st.success("Submitted to approval queue!")
                with col_b:
                    if st.button("✏️ Edit"):
                        st.info("Edit feature ready")

    with col2:
        st.subheader("Recent Drafts")
        # Show recent content from database
        conn = sqlite3.connect('content.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM content ORDER BY created_at DESC LIMIT 5")
        drafts = cursor.fetchall()
        
        for draft in drafts:
            with st.expander(f"{draft[2]} - {draft[1]}"):
                st.write(draft[3][:100] + "...")
                st.caption(f"Status: {draft[5]}")

with tab2:
    # Approval Workflow
    st.header("Approval Queue")
    
    # Get pending approvals
    pending = get_pending_approvals()
    
    if not pending:
        st.info("No content pending approval")
    else:
        for item in pending:
            with st.container():
                st.subheader(f"{item[2]} Post: {item[1]}")
                st.write(item[3])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Approve", key=f"approve_{item[0]}"):
                        approve_content(item[0], "admin")
                        st.success("Approved!")
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject", key=f"reject_{item[0]}"):
                        reject_content(item[0], "Quality issues")
                        st.error("Rejected!")
                        time.sleep(1)
                        st.rerun()
                with col3:
                    if st.button(f"✏️ Edit Request", key=f"edit_{item[0]}"):
                        st.text_input("Edit notes:", key=f"notes_{item[0]}")
                st.divider()

with tab3:
    # Scheduling
    st.header("Schedule Posts")
    
    # Get approved content
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content WHERE status='approved'")
    approved = cursor.fetchall()
    
    if not approved:
        st.info("No approved content to schedule")
    else:
        for post in approved:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{post[2]}**: {post[3][:80]}...")
            with col2:
                schedule_time = st.date_input("Date", key=f"date_{post[0]}")
            with col3:
                if st.button("📅 Schedule", key=f"schedule_{post[0]}"):
                    # Mock scheduling
                    st.success(f"Scheduled for {schedule_time}")
                    
                    # Update status
                    cursor.execute(
                        "UPDATE content SET status='scheduled', scheduled_date=? WHERE id=?",
                        (str(schedule_time), post[0])
                    )
                    conn.commit()
                    time.sleep(1)
                    st.rerun()
    
    # Show scheduled posts
    st.divider()
    st.subheader("Upcoming Posts")
    cursor.execute("SELECT * FROM content WHERE status='scheduled'")
    scheduled = cursor.fetchall()
    
    for sched in scheduled:
        st.write(f"🗓️ {sched[2]} - {sched[1]} on {sched[7] or 'TBD'}")

with tab4:
    # Monitoring
    st.header("System Monitor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Activity Log")
        conn = sqlite3.connect('content.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, platform, topic, status, created_at 
            FROM content 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        logs = cursor.fetchall()
        
        for log in logs:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'scheduled': '📅',
                'posted': '🚀'
            }.get(log[3], '📝')
            
            st.write(f"{status_emoji} {log[2]}: {log[1]} - {log[3]}")
    
    with col2:
        st.subheader("System Status")
        st.metric("Emergency Stop", "ACTIVE" if st.session_state.emergency_stop else "INACTIVE")
        st.metric("Current Mode", mode)
        st.metric("Pending Approvals", len(pending))
        st.metric("Scheduled Posts", len(scheduled))
        
        # Quick actions
        st.divider()
        if st.button("📊 Generate Report"):
            st.info("Report generated in /reports/")
        if st.button("🔄 Refresh All"):
            st.rerun()

# Footer
st.divider()
st.caption("AI Content Agent v1.0 | Built with Grok API | Case Study Demo")
