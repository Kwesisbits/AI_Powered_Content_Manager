from enum import Enum
from datetime import datetime
from typing import Dict, List
import threading
import json

class SystemMode(Enum):
    MANUAL_REVIEW = "manual_review"
    AI_DRAFT_ONLY = "ai_draft_only"
    SUPERVISED_AUTO = "supervised_auto"
    FULL_AUTOMATION = "full_automation"
    CRISIS_MODE = "crisis_mode"
    EMERGENCY_STOP = "emergency_stop"

class SafetyController:
    def __init__(self):
        self.mode = SystemMode.MANUAL_REVIEW
        self.emergency_stop = False
        self.lock = threading.Lock()
        self.audit_log = []
        
        # Safety thresholds
        self.thresholds = {
            "max_auto_approvals_per_hour": 0,
            "min_approval_time_seconds": 60,
            "content_sensitivity_threshold": 0.8,
            "max_posts_per_hour": 10
        }
        
        self._log_event("system_start", "Safety controller initialized")
    
    def emergency_pause(self, reason: str = "Manual activation") -> Dict:
        """INSTANT PAUSE - Stops all automation immediately"""
        
        with self.lock:
            self.mode = SystemMode.EMERGENCY_STOP
            self.emergency_stop = True
            
            self._log_event("emergency_pause", reason, "CRITICAL")
            
            return {
                "status": "SYSTEM_HALTED",
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "mode": self.mode.value,
                "instructions": "All automation stopped. Manual intervention required."
            }
    
    def resume_operations(self) -> Dict:
        """Resume operations after emergency stop"""
        
        with self.lock:
            self.mode = SystemMode.MANUAL_REVIEW
            self.emergency_stop = False
            
            self._log_event("resume_operations", "System resumed from emergency stop")
            
            return {
                "status": "OPERATIONAL",
                "timestamp": datetime.now().isoformat(),
                "mode": self.mode.value
            }
    
    def set_mode(self, mode_str: str):
        """Set system mode"""
        
        mode_map = {
            "manual_review": SystemMode.MANUAL_REVIEW,
            "ai_draft_only": SystemMode.AI_DRAFT_ONLY,
            "supervised_auto": SystemMode.SUPERVISED_AUTO,
            "full_automation": SystemMode.FULL_AUTOMATION
        }
        
        if mode_str in mode_map:
            with self.lock:
                self.mode = mode_map[mode_str]
                self._log_event("mode_change", f"Changed to {mode_str}")
    
    def activate_crisis_mode(self, crisis_type: str = "generic") -> Dict:
        """Activate crisis mode - emergency shutdown"""
        
        with self.lock:
            self.mode = SystemMode.CRISIS_MODE
            
            actions = [
                "Paused all scheduled posts",
                "Disabled automatic content generation",
                "Enabled enhanced content review",
                "Notified security team"
            ]
            
            self._log_event("crisis_mode_activated", 
                          f"Crisis mode: {crisis_type}", "HIGH")
            
            return {
                "status": "CRISIS_MODE_ACTIVE",
                "crisis_type": crisis_type,
                "actions_taken": actions,
                "timestamp": datetime.now().isoformat()
            }
    
    def force_manual_review(self):
        """Force all content to manual review"""
        
        with self.lock:
            self.mode = SystemMode.MANUAL_REVIEW
            
            self._log_event("force_manual_review", 
                          "All content moved to manual review")
    
    def check_content(self, content: str) -> Dict:
        """Comprehensive content safety check"""
        
        issues = []
        
        alarm_words = ["emergency", "urgent", "crisis", "breaking", 
                      "alert", "immediately", "warning"]
        
        content_lower = content.lower()
        for word in alarm_words:
            if word in content_lower:
                issues.append(f"Contains alarming word: '{word}'")
        
        if len(content) < 20:
            issues.append("Content too short")
        elif len(content) > 5000:
            issues.append("Content too long")
        
        safety_score = max(0, 100 - (len(issues) * 20))
        
        return {
            "safe": len(issues) == 0,
            "safety_score": safety_score,
            "issues": issues,
            "requires_manual_review": len(issues) > 0 or safety_score < 70
        }
    
    def get_status(self) -> Dict:
        """Get current safety status"""
        
        return {
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop,
            "safety_score": self._calculate_system_score(),
            "last_incident": self._get_last_incident(),
            "audit_log_size": len(self.audit_log)
        }
    
    def get_audit_log(self, limit: int = 10) -> List[Dict]:
        """Get recent audit log entries"""
        
        return self.audit_log[-limit:] if self.audit_log else []
    
    def _log_event(self, event_type: str, description: str, severity: str = "INFO"):
        """Log safety event"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "description": description,
            "severity": severity,
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop
        }
        
        self.audit_log.append(log_entry)
        
        with open("safety_audit.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _calculate_system_score(self) -> int:
        """Calculate overall system safety score"""
        base_score = 95
        if self.emergency_stop:
            base_score -= 40
        if self.mode == SystemMode.CRISIS_MODE:
            base_score -= 30
        return max(0, min(100, base_score))
    
    def _get_last_incident(self):
        """Get last critical incident"""
        for log in reversed(self.audit_log):
            if log["severity"] in ["HIGH", "CRITICAL"]:
                return log["description"]
        return None
