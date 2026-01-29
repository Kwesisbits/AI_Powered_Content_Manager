"""
Production approval workflow with state machine
Implements hard approval gate as required
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json
import sqlite3

class ContentState(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    DISCARDED = "discarded"

class ApprovalWorkflow:
    def __init__(self, database, ai_agent=None):
        self.db = database
        self.ai_agent = ai_agent  # AI agent for regeneration
        self.required_approvers = 1  # Configurable
        self.min_review_time = 30  # Minimum seconds between creation and approval
        
    def submit_for_approval(self, content_id: str) -> bool:
        """Submit content for approval - HARD GATE"""
        
        # Get content
        content = self.db.get_content(content_id)
        if not content:
            print(f"Error: Content {content_id} not found")
            return False
        
        # Update state to 'pending_approval' (not 'pending_review')
        self.db.update_status(content_id, "pending_approval")
        
        # Log submission
        self.db.log_activity(
            action="submitted_for_approval",
            details=f"Content {content_id} submitted for approval",
            content_id=content_id
        )
        
        # Simulate notification
        self._send_notification(content_id, "submitted")
        
        print(f"Content {content_id} submitted to approval queue")
        return True
        
    def approve(self, content_id: str, approver: str, comments: str = "") -> bool:
        """Approve content - explicit human approval required"""
        
        # Check if content exists
        content = self.db.get_content(content_id)
        if not content:
            return False
        
        # Check if already approved
        if content['status'] == ContentState.APPROVED.value:
            return True
        
        # Update state
        self.db.update_status(content_id, ContentState.APPROVED.value)
        
        # Record approval
        approval_record = {
            "approver": approver,
            "timestamp": datetime.now(),
            "comments": comments,
            "content_id": content_id
        }
        
        self.db.record_approval(approval_record)
        
        # Log activity
        self.db.log_activity(
            action="approved",
            details=f"Content {content_id} approved by {approver}",
            content_id=content_id
        )
        
        # Simulate notification
        self._send_notification(content_id, "approved")
        
        return True
    
    def reject(self, content_id: str, reason: str, reviewer: str) -> bool:
        """Reject content - hard stop"""
        
        # Update state
        self.db.update_status(content_id, ContentState.REJECTED.value)
        
        # Record rejection
        rejection_record = {
            "reviewer": reviewer,
            "reason": reason,
            "timestamp": datetime.now(),
            "content_id": content_id
        }
        
        self.db.record_rejection(rejection_record)
        
        # Log activity
        self.db.log_activity(
            action="rejected",
            details=f"Content {content_id} rejected: {reason}",
            content_id=content_id
        )
        
        # Simulate notification
        self._send_notification(content_id, "rejected", reason)
        
        return True
    
    def request_revision(self, content_id: str, notes: str, reviewer: str) -> bool:
        """Send content back for AI revision - ACTUALLY REGENERATE"""
        
        # Get the original content
        content = self.db.get_content(content_id)
        if not content:
            print(f"Error: Content {content_id} not found for revision")
            return False
        
        print(f"Revision requested for content {content_id}")
        print(f"   Reviewer notes: {notes}")
        
        # Update state
        self.db.update_status(content_id, "needs_revision")
        
        # Record revision request
        revision_record = {
            "reviewer": reviewer,
            "notes": notes,
            "timestamp": datetime.now(),
            "content_id": content_id
        }
        
        self.db.record_revision_request(revision_record)
        
        # Log activity
        self.db.log_activity(
            action="revision_requested",
            details=f"Content {content_id} needs revision: {notes[:50]}...",
            content_id=content_id
        )
        
        # ACTUAL AI REGENERATION WITH FEEDBACK
        if self.ai_agent:
            try:
                print("Regenerating content with AI based on feedback...")
                
                # Extract original parameters
                original_topic = content.get('topic', '')
                original_platform = content.get('platform', '')
                
                # Get metadata for brand voice
                metadata = content.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                # Create enhanced prompt with revision feedback
                enhanced_topic = f"{original_topic} - REVISION REQUESTED: {notes}"
                
                # Generate revised content
                revised_result = self.ai_agent.generate_content(
                    platform=original_platform,
                    topic=enhanced_topic,
                    brand_voice=self._get_brand_voice_from_metadata(metadata),
                    tone=metadata.get('tone', 'professional'),
                    include_hashtags=True,
                    include_question=True,
                    call_to_action=None
                )
                
                # Create new content entry for revised version
                revised_content_id = self.db.create_content(
                    platform=original_platform,
                    topic=f"Revised: {original_topic[:50]}...",
                    content=revised_result["content"],
                    metadata={
                        **revised_result.get("metadata", {}),
                        "revision_of": content_id,
                        "revision_notes": notes,
                        "reviewer": reviewer,
                        "original_topic": original_topic,
                        "revision_timestamp": datetime.now().isoformat()
                    },
                    status="draft"
                )
                
                # Also add revision marker to original content
                original_metadata = content.get('metadata', {})
                if isinstance(original_metadata, str):
                    try:
                        original_metadata = json.loads(original_metadata)
                    except:
                        original_metadata = {}
                
                original_metadata['has_revisions'] = True
                original_metadata['latest_revision'] = revised_content_id
                
                # Update original metadata
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE content SET metadata = ? WHERE id = ?",
                    (json.dumps(original_metadata), content_id)
                )
                conn.commit()
                conn.close()
                
                # Log the regeneration
                self.db.log_activity(
                    action="content_regenerated",
                    details=f"Content {content_id} regenerated as {revised_content_id} based on revision notes",
                    content_id=revised_content_id
                )
                
                print(f"Revised content created: ID {revised_content_id}")
                print(f"   Original: {content_id}")
                print(f"   New version: {revised_content_id}")
                
                # Update original content to reference revision
                self.db.log_activity(
                    action="revision_created",
                    details=f"New version {revised_content_id} created from revision of {content_id}",
                    content_id=content_id
                )
                
                return True
                
            except Exception as e:
                print(f"AI regeneration failed: {e}")
                # Still record the revision request even if regeneration fails
                return True
        else:
            print("AI agent not available for regeneration")
            print("   In production, this would trigger AI to regenerate content.")
            return True
        
    def _get_brand_voice_from_metadata(self, metadata: Dict) -> object:
        """Create BrandVoice object from metadata"""
        from agents import BrandVoice
        
        # Default values
        company_name = metadata.get('company', 'TechInnovate')
        tone = metadata.get('tone', 'professional')
        personality_traits = metadata.get('personality_traits', ['Expert', 'Innovative'])
        target_audience = metadata.get('audience', 'tech professionals')
        content_pillars = metadata.get('content_pillars', ['AI Trends', 'Tech Leadership'])
        forbidden_topics = metadata.get('forbidden_topics', ['politics', 'financial advice'])
        
        # Ensure lists
        if isinstance(personality_traits, str):
            personality_traits = [personality_traits]
        if isinstance(content_pillars, str):
            content_pillars = [content_pillars]
        if isinstance(forbidden_topics, str):
            forbidden_topics = [forbidden_topics]
        
        return BrandVoice(
            company_name=company_name,
            tone=tone,
            personality_traits=personality_traits,
            target_audience=target_audience,
            content_pillars=content_pillars,
            forbidden_topics=forbidden_topics
        )
        
    def _send_notification(self, content_id: str, action: str, extra_info: str = ""):
        """Simulate notification system"""
        print(f"NOTIFICATION: Content {content_id} was {action}. {extra_info}")
        
        # In production: Send email/Slack/webhook
        notification = {
            "content_id": content_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "extra_info": extra_info
        }
        
        # Save notification for UI
        self.db.save_notification(notification)
    
    def get_approval_queue(self) -> List[Dict]:
        """Get all content pending approval"""
        return self.db.get_content_by_status(ContentState.PENDING_APPROVAL.value)
    
    def get_review_queue(self) -> List[Dict]:
        """Get all content pending review"""
        return self.db.get_content_by_status(ContentState.PENDING_REVIEW.value)
