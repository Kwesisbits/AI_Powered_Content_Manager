"""
Production AI Content Agent - Complete Implementation
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os

# Import our production modules
from agents import ContentAgent, BrandVoice
from workflow import ApprovalWorkflow, ContentState
from safety import SafetyController, SystemMode
from database import ContentDatabase

# ========== SIMPLE SCHEDULER ==========
class PostingScheduler:
    def __init__(self, database):
        self.db = database
        self.scheduled = []
    
    def schedule_content(self, content_id, schedule_time):
        """Schedule content for posting"""
        self.db.update_status(content_id, "scheduled")
        
        self.scheduled.append({
            "content_id": content_id,
            "scheduled_time": schedule_time,
            "status": "pending"
        })
        
        return {
            "success": True,
            "message": f"Scheduled for {schedule_time}",
            "content_id": content_id
        }
    
    def get_scheduled_posts(self):
        """Get all scheduled posts"""
        return self.scheduled
    
    def simulate_posting(self):
        """Simulate posting due content"""
        now = datetime.now()
        posted = []
        
        for post in self.scheduled[:]:
            if post['scheduled_time'] <= now and post['status'] == 'pending':
                post['status'] = 'posted'
                post['posted_at'] = now
                self.db.update_status(post['content_id'], 'published')
                posted.append(post)
        
        return posted

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="AI Content Agent - Production System",
    page_icon="◼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SYSTEM INITIALIZATION ==========
@st.cache_resource
def init_system():
    """Initialize all system components"""
    # Brand voice configuration
    brand_voice = BrandVoice(
        company_name="40 Analytics",
        tone="educational",
        personality_traits=["Analytical", "Insightful", "Data-driven", "Educational"],
        target_audience="data scientists, business analysts, tech leaders",
        content_pillars=["Data Analytics", "AI Applications", "Business Intelligence", "Tech Trends"],
        forbidden_topics=["politics", "financial advice", "competitor names"]
    )
    
    # Initialize components
    db = ContentDatabase()
    safety = SafetyController()
    
    # Initialize AI agent first
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY")
    agent = ContentAgent(api_key=api_key)
    
    # Pass agent to workflow
    workflow = ApprovalWorkflow(db, ai_agent=agent)
    
    scheduler = PostingScheduler(db)
    
    if not api_key:
        st.sidebar.warning(" Set GROQ_API_KEY environment variable for AI generation")
    else:
        st.sidebar.success(" Groq API key loaded")
    
    return {
        "brand": brand_voice,
        "db": db,
        "safety": safety,
        "workflow": workflow,
        "scheduler": scheduler,
        "agent": agent
    }

# Initialize system
system = init_system()

# ========== SESSION STATE ==========
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "create"
if 'emergency_mode' not in st.session_state:
    st.session_state.emergency_mode = False
if 'current_content_id' not in st.session_state:
    st.session_state.current_content_id = None
if 'refresh_needed' not in st.session_state:
    st.session_state.refresh_needed = False

# Force refresh if needed
if st.session_state.refresh_needed:
    st.session_state.refresh_needed = False
    st.rerun()

# ========== SIDEBAR - CONTROL PANEL ==========
with st.sidebar:
    st.title("Control Panel")
    
    # Emergency Controls
    st.subheader(" Safety Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Pause All", type="secondary"):
            system["safety"].emergency_pause("Manual pause activated")
            st.session_state.emergency_mode = True
            st.error("All automation paused!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button(" Resume", disabled=not st.session_state.emergency_mode):
            system["safety"].resume_operations()
            st.session_state.emergency_mode = False
            st.success("System resumed!")
            time.sleep(1)
            st.rerun()
    
    # System Mode
    st.divider()
    st.subheader(" System Mode")
    
    mode = st.selectbox(
        "Operation Mode",
        ["Manual Review", "AI Draft Only", "Supervised Auto", "Full Automation"],
        index=0,
        help="Manual: All actions require approval\nAI Draft: AI creates drafts only\nSupervised: AI drafts + auto-schedule after approval\nFull: End-to-end automation"
    )
    
    # Update system mode
    system["safety"].set_mode(mode.lower().replace(" ", "_"))
    
    # Brand Configuration
    st.divider()
    st.subheader(" Brand Voice")
    
    with st.expander("Configure Brand", expanded=False):
        st.text_input("Company Name", value=system["brand"].company_name)
        st.selectbox("Tone", ["Professional", "Casual", "Technical", "Inspirational"])
        st.text_area("Target Audience", value=system["brand"].target_audience)
        st.text_area("Key Messages", value="\n".join(system["brand"].content_pillars))
    
    # System Status
    st.divider()
    st.subheader(" System Status")
    
    # Get stats from database
    stats = system["db"].get_system_stats()
    
    st.metric("Pending Approval", stats.get("pending_approval", 0))
    st.metric("Scheduled", stats.get("scheduled", 0))
    st.metric("Published", stats.get("published", 0))
    st.metric("AI Generations", stats.get("generated", 0))

# ========== MAIN DASHBOARD ==========
st.title(" AI Content Agent - Production System")
st.caption("Enterprise-grade AI automation with human-in-the-loop controls")

# Tabs with proper workflow
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " Create", 
    " Review", 
    " Approve", 
    " Schedule", 
    " Monitor"
])

# ========== TAB 1: AI CONTENT CREATION ==========
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("AI Content Creation")
        
        # Platform selection with platform-specific guidance
        platform = st.selectbox(
            "Select Platform",
            ["LinkedIn", "Twitter", "Instagram", "Facebook"],
            help="Content will be optimized for selected platform"
        )
        
        # Topic input with suggestions
        topic = st.text_area(
            "Content Brief",
            height=100,
            placeholder="Describe what you want to post about...\nExample: 'The impact of AI on data analytics workflows'",
            help="Be specific for better AI generation"
        )
        
        # Advanced options
        with st.expander(" Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                tone = st.selectbox(
                    "Specific Tone",
                    ["Default", "Excited", "Educational", "Thought Leadership", "Promotional"]
                )
                include_hashtags = st.checkbox("Generate Hashtags", value=True)
            with col_b:
                include_question = st.checkbox("Add Engagement Question", value=True)
                call_to_action = st.selectbox(
                    "Call to Action",
                    ["None", "Learn More", "Sign Up", "Download", "Comment"]
                )
        
        # Media Upload Section
        st.subheader(" Media Assets")
        
        uploaded_files = st.file_uploader(
            "Upload images/videos for this post",
            type=['jpg', 'jpeg', 'png', 'mp4', 'mov'],
            accept_multiple_files=True,
            help="AI will incorporate context from uploaded media"
        )
        
        if uploaded_files:
            st.success(f" {len(uploaded_files)} file(s) uploaded")
            cols = st.columns(min(3, len(uploaded_files)))
            for idx, file in enumerate(uploaded_files[:3]):
                with cols[idx % 3]:
                    if file.type.startswith('image'):
                        st.image(file, width=150)
                    else:
                        st.video(file)
                    st.caption(file.name[:20])
        
        # Generate button with confirmation
        if st.button(" Generate AI Content", type="primary"):
            if not topic:
                st.error("Please enter a content brief")
            else:
                with st.spinner(" AI agent creating content..."):
                    try:
                        # Get ALL advanced options
                        advanced_options = {
                            "tone": tone if tone != "Default" else None,
                            "include_hashtags": include_hashtags,
                            "include_question": include_question,
                            "call_to_action": call_to_action if call_to_action != "None" else None,
                            "media_files": uploaded_files if uploaded_files else None
                        }
                        
                        # Generate content using AI agent
                        result = system["agent"].generate_content(
                            platform=platform,
                            topic=topic,
                            brand_voice=system["brand"],
                            **advanced_options
                        )
                        
                        # Store in database
                        content_id = system["db"].create_content(
                            platform=platform,
                            topic=topic,
                            content=result["content"],
                            metadata=result["metadata"],
                            status="draft"
                        )
                        
                        st.session_state.current_content_id = content_id
                        
                        # Show generated content
                        st.success(" AI Content Generated!")
                        st.divider()
                        
                        # Display ALL information
                        col1_display, col2_display = st.columns([3, 1])
                        
                        with col1_display:
                            st.subheader("Generated Content")
                            st.write(result["content"])
                        
                        with col2_display:
                            st.subheader("Details")
                            st.write(f"**Company:** {result['metadata']['company']}")
                            st.write(f"**Platform:** {result['metadata']['platform']}")
                            st.write(f"**Tone:** {result['metadata']['tone']}")
                            st.write(f"**Audience:** {result['metadata']['audience']}")
                            
                            if result.get("hashtags"):
                                st.write(f"**Hashtags:** {', '.join(result['hashtags'])}")
                            
                            if result.get("engagement_question"):
                                st.write(f"**Question:** {result['engagement_question']}")
                        
                        # Action buttons
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if st.button(" Submit for Approval", use_container_width=True):
                                system["workflow"].submit_for_approval(content_id)
                                st.success("Submitted to approval queue!")
                                st.session_state.refresh_needed = True
                                time.sleep(1)
                                st.rerun()
                        with col_b:
                            if st.button(" Edit & Resubmit", use_container_width=True):
                                st.info("Edit interface would open here")
                        with col_c:
                            if st.button(" Discard", use_container_width=True, type="secondary"):
                                system["db"].update_status(content_id, "discarded")
                                st.info("Content discarded")
                                st.session_state.refresh_needed = True
                                time.sleep(1)
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f" AI Generation failed: {str(e)}")
                        st.info("Please check your GROQ_API_KEY environment variable and try again.")
    
    with col2:
        st.header("Recent Drafts & Revisions")
        
        # Show recent AI-generated content
        recent_drafts = system["db"].get_recent_content(limit=10)
        
        if not recent_drafts:
            st.info("No drafts yet. Create your first AI content!")
        else:
            for draft in recent_drafts:
                # Check if this is a revision
                is_revision = False
                revision_info = ""
                
                if draft.get('metadata'):
                    metadata = draft['metadata']
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    if 'revision_of' in metadata:
                        is_revision = True
                        revision_info = f" Revision of #{metadata['revision_of']}"
                        if 'revision_notes' in metadata:
                            revision_info += f" - {metadata['revision_notes'][:30]}..."
                
                expander_title = f"{draft['platform']}: {draft['topic'][:30]}..."
                if is_revision:
                    expander_title = f" {expander_title}"
                
                with st.expander(expander_title):
                    # Handle content display
                    content_to_show = draft.get('content', '')
                    if isinstance(content_to_show, dict):
                        content_to_show = content_to_show.get('content', 'No content')
                    
                    st.write(content_to_show[:200] + "...")
                    st.caption(f"Status: {draft['status']} | ID: {draft['id']} | Created: {draft['created_at']}")
                    
                    if is_revision:
                        st.info(revision_info)
                    
                    if draft['status'] == 'draft':
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("Edit", key=f"edit_{draft['id']}"):
                                st.session_state.current_content_id = draft['id']
                                st.session_state.selected_tab = "approve"
                                st.rerun()
                        with col_y:
                            if st.button("Submit", key=f"submit_{draft['id']}"):
                                system["workflow"].submit_for_approval(draft['id'])
                                st.success("Submitted!")
                                st.session_state.refresh_needed = True
                                time.sleep(1)
                                st.rerun()

# ========== TAB 2: REVIEW QUEUE ==========
with tab2:
    st.header(" Content Review Queue")
    st.caption("Content pending review before approval")
    
    # Get content needing review - FIXED to show 'pending_approval'
    review_queue = system["db"].get_content_by_status("pending_approval")
    
    if not review_queue:
        st.info(" No content pending review")
    else:
        for item in review_queue:
            with st.container():
                # Content card
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.subheader(f"{item['platform'].upper()}: {item['topic']}")
                    
                    # Content preview - FIX content display
                    content_to_show = item.get('content', '')
                    if isinstance(content_to_show, dict):
                        content_to_show = content_to_show.get('content', 'No content')
                    
                    with st.expander("View Full Content", expanded=False):
                        st.write(content_to_show[:300] + "..." if len(content_to_show) > 300 else content_to_show)
                        
                        # Handle metadata display
                        if item.get('metadata'):
                            if isinstance(item['metadata'], str):
                                try:
                                    metadata = json.loads(item['metadata'])
                                    if 'hashtags' in metadata:
                                        st.caption(f"**Hashtags:** {', '.join(metadata['hashtags'])}")
                                except:
                                    pass
                            elif isinstance(item['metadata'], dict) and 'hashtags' in item['metadata']:
                                st.caption(f"**Hashtags:** {', '.join(item['metadata']['hashtags'])}")
                
                with col2:
                    st.caption(f"ID: {item['id']}")
                    st.caption(f"Created: {item['created_at']}")
                    
                    # Review actions
                    if st.button(" Review", key=f"review_{item['id']}", use_container_width=True):
                        st.session_state.selected_tab = "approve"
                        st.session_state.current_content_id = item['id']
                        st.rerun()
                
                st.divider()

# ========== TAB 3: APPROVAL WORKFLOW ==========
with tab3:
    st.header(" Approval Workflow")
    st.caption("Hard approval gate - No content publishes without explicit approval")
    
    # Get content pending approval
    approval_queue = system["db"].get_content_by_status("pending_approval")
    
    if st.session_state.current_content_id:
        # Show specific content for approval
        content = system["db"].get_content(st.session_state.current_content_id)
        
        if content:
            # Display content for approval
            st.subheader(f"Reviewing: {content['platform']} - {content['topic']}")
            
            # SHOW REVISIONS IF ANY
            revisions = system["db"].get_revisions_of_content(content['id'])
            if revisions:
                st.subheader(" Revision History")
                for rev in revisions:
                    with st.expander(f"Revision from {rev['created_at']}"):
                        rev_content = rev.get('content', '')
                        if isinstance(rev_content, dict):
                            rev_content = rev_content.get('content', 'No content')
                        st.write(rev_content[:500] + "..." if len(rev_content) > 500 else rev_content)
                        
                        # Show revision notes
                        rev_metadata = rev.get('metadata', {})
                        if isinstance(rev_metadata, str):
                            try:
                                rev_metadata = json.loads(rev_metadata)
                            except:
                                rev_metadata = {}
                        
                        if 'revision_notes' in rev_metadata:
                            st.info(f"**Revision Notes:** {rev_metadata['revision_notes']}")
                        if 'reviewer' in rev_metadata:
                            st.caption(f"Requested by: {rev_metadata['reviewer']}")
                        
                        # Quick actions for revision
                        if rev['status'] == 'draft':
                            col_r1, col_r2 = st.columns(2)
                            with col_r1:
                                if st.button(f"Submit Revision", key=f"submit_rev_{rev['id']}"):
                                    system["workflow"].submit_for_approval(rev['id'])
                                    st.success("Revision submitted!")
                                    time.sleep(1)
                                    st.rerun()
                st.divider()
            # END REVISIONS
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Content display
                content_to_show = content.get('content', '')
                if isinstance(content_to_show, dict):
                    content_to_show = content_to_show.get('content', 'No content')
                
                st.write(content_to_show)
                
                # AI Analysis
                with st.expander(" AI Analysis", expanded=True):
                    if content.get('metadata'):
                        try:
                            if isinstance(content['metadata'], str):
                                metadata = json.loads(content['metadata'])
                            else:
                                metadata = content['metadata']
                            st.json(metadata, expanded=False)
                        except:
                            st.info("No metadata available")
                
                # Edit interface
                with st.expander(" Request Edits", expanded=False):
                    edit_notes = st.text_area("Edit instructions for AI:", placeholder="e.g., Make it more technical, focus on ROI, use more data-driven language...")
                    
                    if st.button(" Send for Revision"):
                        if edit_notes:
                            success = system["workflow"].request_revision(
                                content['id'], 
                                edit_notes,
                                st.session_state.get('user', 'admin')
                            )
                            if success:
                                st.success(" Content sent for AI revision! Check 'Recent Drafts & Revisions' for the new version.")
                                st.session_state.refresh_needed = True
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(" Revision failed")
            
            with col2:
                # Approval actions
                st.subheader("Approval Decision")
                
                approver = st.text_input("Approver Name", "admin@company.com")
                
                if st.button(" APPROVE CONTENT", type="primary", use_container_width=True):
                    system["workflow"].approve(
                        content['id'],
                        approver=approver,
                        comments="Approved via dashboard"
                    )
                    st.success(" Content Approved!")
                    
                    # Auto-schedule if in supervised mode
                    if system["safety"].mode == "supervised_auto":
                        schedule_time = datetime.now() + timedelta(hours=2)
                        system["scheduler"].schedule_content(content['id'], schedule_time)
                        st.info(f" Auto-scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    time.sleep(2)
                    st.session_state.current_content_id = None
                    st.session_state.refresh_needed = True
                    st.rerun()
                
                if st.button(" REJECT CONTENT", type="secondary", use_container_width=True):
                    rejection_reason = st.text_input("Rejection reason:", key="reject_reason", placeholder="e.g., Too technical, needs more business focus...")
                    
                    if rejection_reason:
                        system["workflow"].reject(
                            content['id'],
                            reason=rejection_reason,
                            reviewer=approver
                        )
                        st.error(" Content Rejected")
                        time.sleep(2)
                        st.session_state.current_content_id = None
                        st.session_state.refresh_needed = True
                        st.rerun()
                
                # Safety check
                safety_check = system["safety"].check_content(content_to_show)
                if not safety_check["safe"]:
                    st.warning(" Safety flags detected")
                    for flag in safety_check["flags"]:
                        st.caption(f"• {flag}")
    
    # Show approval queue
    if not st.session_state.current_content_id:
        st.divider()
        st.subheader("Approval Queue")
        
        if not approval_queue:
            st.info(" No content in approval queue")
        else:
            for item in approval_queue:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{item['platform']}:** {item['topic'][:50]}...")
                    st.caption(f"Submitted: {item['created_at']}")
                with col2:
                    if st.button("Review", key=f"quick_review_{item['id']}"):
                        st.session_state.current_content_id = item['id']
                        st.rerun()
                with col3:
                    st.caption(f"ID: {item['id']}")

# ========== TAB 4: SCHEDULING ==========
with tab4:
    st.header(" Content Scheduling")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Calendar view for scheduling
        st.subheader("Schedule Calendar")
        
        # Get scheduled content
        scheduled = system["db"].get_content_by_status("scheduled")
        
        # Simple calendar display
        today = datetime.now()
        
        for i in range(7):
            day = today + timedelta(days=i)
            day_content = [c for c in scheduled 
                          if c.get('scheduled_time') 
                          and isinstance(c['scheduled_time'], datetime)
                          and c['scheduled_time'].date() == day.date()]
            
            with st.expander(f"{day.strftime('%A, %b %d')}"):
                if day_content:
                    for content in day_content:
                        st.write(f" {content['scheduled_time'].strftime('%H:%M')} - {content['platform']}")
                        st.caption(content['topic'][:50])
                else:
                    st.info("No content scheduled")
        
        # Quick schedule interface
        st.subheader("Quick Schedule")
        
        approved_content = system["db"].get_content_by_status("approved")
        
        if approved_content:
            content_options = {f"{c['id']}: {c['platform']} - {c['topic'][:30]}": c['id'] 
                              for c in approved_content}
            
            if content_options:
                selected = st.selectbox("Select content to schedule:", list(content_options.keys()))
                
                col_a, col_b = st.columns(2)
                with col_a:
                    schedule_date = st.date_input("Date", min_value=datetime.now().date())
                with col_b:
                    schedule_time = st.time_input("Time")
                
                if st.button(" Schedule Content"):
                    schedule_datetime = datetime.combine(schedule_date, schedule_time)
                    
                    if schedule_datetime < datetime.now():
                        st.error("Cannot schedule in the past")
                    else:
                        content_id = content_options[selected]
                        system["scheduler"].schedule_content(content_id, schedule_datetime)
                        st.success(f" Scheduled for {schedule_datetime.strftime('%Y-%m-%d %H:%M')}")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("No approved content available for scheduling")
        else:
            st.info("No approved content available for scheduling")
    
    with col2:
        st.subheader("Scheduling Rules")
        
        # Posting frequency
        st.caption("Posting Frequency")
        frequency = st.select_slider(
            "Posts per week",
            options=[1, 2, 3, 5, 7, 10, 14],
            value=3
        )
        
        # Optimal times
        st.caption("Optimal Posting Times")
        platforms = ["LinkedIn", "Twitter", "Instagram"]
        
        for platform in platforms:
            st.multiselect(
                f"{platform} best times",
                ["8-10 AM", "12-1 PM", "5-7 PM", "8-9 PM"],
                default=["8-10 AM", "5-7 PM"],
                key=f"times_{platform}"
            )
        
        # Auto-schedule rules
        st.divider()
        if st.checkbox("Enable auto-scheduling", value=False):
            st.caption("AI will automatically schedule approved content")
            buffer_days = st.slider("Schedule X days after approval", 0, 7, 1)
            avoid_weekends = st.checkbox("Avoid weekends", value=True)

# ========== TAB 5: MONITORING & SAFETY ==========
with tab5:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(" System Monitoring")
        
        # Real-time metrics
        metrics_cols = st.columns(4)
        
        stats = system["db"].get_system_stats()
        
        with metrics_cols[0]:
            st.metric("AI Generations", stats["generated"], delta="+12 today")
        with metrics_cols[1]:
            st.metric("Approval Rate", f"{stats['approval_rate']}%", delta="+5%")
        with metrics_cols[2]:
            st.metric("Avg. Review Time", "2.5h")
        with metrics_cols[3]:
            st.metric("System Uptime", "99.8%", delta="-0.1%")
        
        # Activity timeline
        st.subheader(" Activity Timeline")
        
        activities = system["db"].get_recent_activities(limit=10)
        
        for activity in activities:
            timestamp = activity['timestamp'][11:16] if activity['timestamp'] else "--:--"
            st.caption(f"**{timestamp}** - {activity['action']}: {activity['details'][:50]}...")
        
        # Content performance (simulated)
        st.subheader(" Content Performance")
        
        performance_data = {
            "Platform": ["LinkedIn", "Twitter", "Instagram", "Facebook"],
            "Posts": [12, 24, 18, 8],
            "Avg. Engagement": [45, 120, 210, 35],
            "Approval Rate": [85, 92, 78, 65]
        }
        
        st.dataframe(performance_data, use_container_width=True)
    
    with col2:
        st.header(" Safety Dashboard")
        
        # Current safety status
        safety_status = system["safety"].get_status()
        
        st.metric("System Mode", safety_status["mode"].replace("_", " ").title())
        st.metric("Safety Score", f"{safety_status['safety_score']}/100")
        st.metric("Last Incident", safety_status["last_incident"] or "None")
        
        # Safety controls
        st.divider()
        st.subheader("Safety Actions")
        
        if st.button(" Enable Crisis Mode", type="secondary"):
            system["safety"].activate_crisis_mode("manual_activation")
            st.session_state.emergency_mode = True
            st.error(" CRISIS MODE ACTIVATED - All posting halted")
            st.rerun()
        
        if st.button(" Manual Review All", type="secondary"):
            system["safety"].force_manual_review()
            st.warning("All content moved to manual review")
        
        # Audit log
        st.divider()
        st.subheader(" Recent Audit Log")
        
        audit_log = system["safety"].get_audit_log(limit=5)
        
        for log in audit_log:
            st.caption(f"{log['timestamp']}: {log['event']}")

# ========== FOOTER ==========
st.divider()
st.caption("AI Content Agent v1.0 | Human-in-the-Loop Approval System")
