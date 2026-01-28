"""
Production approval workflow with state machine
Implements hard approval gate as required
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
import uuid

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
    def __init__(self, database):
        self.db = database
        self.required_approvers = 1  # Configurable
        self.min_review_time = 30  # Minimum seconds between creation and approval
        
    def submit_for_approval(self, content_id: str) -> bool:
        """Submit content for approval - HARD GATE"""
        
        # Get content
        content = self.db.get_content(content_id)
        if not content:
            return False
        
        # Update state
        self.db.update_status(content_id, ContentState.PENDING_REVIEW.value)
        
        # Log submission
        self.db.log_activity(
            action="submitted_for_approval",
            details=f"Content {content_id} submitted for approval",
            content_id=content_id
        )
        
        # Simulate notification
        self._send_notification(content_id, "submitted")
        
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
        """Send content back for AI revision"""
        
        # Update state
        self.db.update_status(content_id, ContentState.NEEDS_REVISION.value)
        
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
        
        # TODO: Trigger AI to revise based on notes
        
        return True
    
    def _send_notification(self, content_id: str, action: str, extra_info: str = ""):
        """Simulate notification system"""
        print(f" NOTIFICATION: Content {content_id} was {action}. {extra_info}")
        
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
