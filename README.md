# AI Powered Content Manager

Prototype AI content generation with mandatory human approval workflows and safety controls.

## Overview

Generates platform-optimized social media content using Groq API with strict approval gates, revision workflows, and emergency controls. No content publishes without explicit human approval.

## Features

- **Content Generation**: AI-powered creation (LinkedIn, Twitter, Instagram, Facebook)
- **Approval Workflow**: Hard gate - draft → pending approval → approved → scheduled → published
- **Revisions**: Send content back for AI regeneration with specific feedback
- **Safety Controls**: Emergency pause, system modes, crisis shutdown, audit logging
- **Scheduling**: Calendar interface with optimal posting times
- **Monitoring**: Real-time metrics, approval rates, performance analytics

## Quick Start

### Requirements
```
Python 3.8+
Streamlit 1.28.0
Requests 2.31.0
APScheduler 3.10.4
```

### Installation

```bash
git clone <repository-url>
cd ai-content-manager
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export GROQ_API_KEY="gsk_your_key_here"
streamlit run app.py
```

Access at **http://localhost:8501**

## Configuration

### API Key
```bash
export GROQ_API_KEY="gsk_your_api_key"
```

Get key from https://console.groq.com

### Brand Voice
Edit in app.py:
```python
brand_voice = BrandVoice(
    company_name="Your Company",
    tone="professional",
    personality_traits=["innovative", "trustworthy"],
    target_audience="tech professionals",
    content_pillars=["innovation", "leadership"],
    forbidden_topics=["politics"]
)
```

### System Modes
- **Manual Review**: All actions require approval (default)
- **AI Draft Only**: AI creates drafts only
- **Supervised Auto**: Auto-schedule after approval
- **Full Automation**: End-to-end (caution)

## Core Workflow

1. **Create**: AI generates content for chosen platform
2. **Submit**: Send to approval queue
3. **Approve/Reject**: Explicit human decision required
4. **Request Revisions** (optional): AI regenerates with feedback
5. **Schedule**: Calendar-based posting
6. **Monitor**: View metrics and performance

## Approval Workflow

**Hard Approval Gate**: All content requires explicit human approval before action.

**Revision Process**:
1. Reviewer requests changes with specific notes
2. AI receives feedback and regenerates content
3. New revision appears in draft history
4. Reviewer submits revised version for approval

**States**: Draft → Pending Approval → Approved → Scheduled → Published

## Safety Controls

| Feature | Action |
|---------|--------|
| **Emergency Pause** | Instantly halt all automation |
| **Crisis Mode** | Full system shutdown |
| **System Modes** | Configure automation level |
| **Audit Logging** | All events logged with timestamps |

## File Structure

| File | Purpose |
|------|---------|
| **app.py** | Streamlit UI and orchestration |
| **agents.py** | AI content generation (Groq API) |
| **workflow.py** | Approval state machine and revisions |
| **safety.py** | Emergency controls and audit logging |
| **database.py** | SQLite data persistence |

## Troubleshooting

**API error**: Verify API key starts with `gsk_` and has valid permissions

**Content not in approval queue**: Ensure submitted (not just saved as draft)

**Revision regeneration fails**: Check API key is active and internet connected

**Database locked**: Restart application

## API Reference

### ContentAgent.generate_content()
```python
result = agent.generate_content(
    platform="LinkedIn",
    topic="Your content topic",
    brand_voice=brand_voice,
    tone="Optional tone override",
    include_hashtags=True,
    include_question=True
)
# Returns: {content, hashtags, engagement_question, optimal_post_time, metadata}
```

### ApprovalWorkflow Methods
```python
workflow.submit_for_approval(content_id)
workflow.approve(content_id, approver="name", comments="")
workflow.reject(content_id, reason="reason", reviewer="name")
workflow.request_revision(content_id, notes="feedback", reviewer="name")
```

### SafetyController Methods
```python
safety.emergency_pause(reason="reason")
safety.activate_crisis_mode()
safety.set_mode("manual_review")
safety.check_content(text)
```

## Performance

- Content generation: 3-8 seconds
- API timeout: 30 seconds
- SQLite suitable for < 10,000 items
- Use PostgreSQL for production scaling

## Database

Default: **SQLite** (content.db)
- Content table: Generated posts with metadata
- Approvals table: Approval records and decisions
- Activity log: All system actions

For production: Switch to PostgreSQL by modifying ContentDatabase initialization.

## Security

- Store API key in environment variables only
- Never commit keys to version control
- All approvals logged with timestamp and approver
- Audit trail in safety_audit.log
- Regular key rotation recommended

## Production Deployment

### Streamlit Cloud
```
1. Push to GitHub
2. Connect in Streamlit Cloud
3. Set GROQ_API_KEY in secrets
4. Deploy
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GROQ_API_KEY=$GROQ_API_KEY
CMD ["streamlit", "run", "app.py"]
```

### Self-Hosted
1. Set up Python environment
2. Configure PostgreSQL database
3. Set environment variables
4. Run with Gunicorn + Nginx
5. Set up SSL/TLS certificates

## Maintenance

- Monitor API usage and costs
- Review audit logs monthly
- Backup database regularly
- Test disaster recovery
- Update dependencies periodically
- Monitor log file sizes

## License

MIT - See LICENSE file

## Support

For issues:
1. Check troubleshooting section above
2. Review audit logs (safety_audit.log)
3. Verify API key and environment setup
4. Check Groq API status at console.groq.com
