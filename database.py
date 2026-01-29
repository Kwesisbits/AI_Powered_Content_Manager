"""
Production database layer with SQLite/PostgreSQL support
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class ContentDatabase:
    def __init__(self, db_path: str = "content.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                platform TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_time TIMESTAMP,
                published_time TIMESTAMP,
                media_paths TEXT
            )
        ''')
        
        # Approvals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                approver TEXT,
                action TEXT,
                comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content (id)
            )
        ''')
        
        # Activity log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                details TEXT,
                content_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_content(self, platform: str, topic: str, content: str, 
                      metadata: Dict, status: str = "draft") -> int:
        """Create new content entry"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO content (platform, topic, content, metadata, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (platform, topic, content, json.dumps(metadata), status))
        
        content_id = cursor.lastrowid
        
        # Log activity
        cursor.execute('''
            INSERT INTO activity_log (action, details, content_id)
            VALUES (?, ?, ?)
        ''', ('content_created', f'Created {platform} content: {topic[:50]}', content_id))
        
        conn.commit()
        conn.close()
        
        return content_id
    
    def get_content(self, content_id: int) -> Optional[Dict]:
        """Get content by ID"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM content WHERE id = ?
        ''', (content_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            content = dict(row)
            if content.get('metadata'):
                try:
                    content['metadata'] = json.loads(content['metadata'])
                except:
                    content['metadata'] = {}
            return content
        
        return None
    
    def get_content_by_status(self, status: str) -> List[Dict]:
        """Get content by status"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM content WHERE status = ? ORDER BY created_at DESC
        ''', (status,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            content = dict(row)
            if content.get('metadata'):
                try:
                    content['metadata'] = json.loads(content['metadata'])
                except:
                    content['metadata'] = {}
            result.append(content)
        
        return result
    
    def update_status(self, content_id: int, status: str):
        """Update content status"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE content 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, content_id))
        
        conn.commit()
        conn.close()
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute('''
            SELECT status, COUNT(*) as count FROM content GROUP BY status
        ''')
        
        status_counts = cursor.fetchall()
        
        # Calculate totals
        stats = {
            "total": 0,
            "draft": 0,
            "pending_review": 0,
            "pending_approval": 0,
            "approved": 0,
            "scheduled": 0,
            "published": 0,
            "rejected": 0
        }
        
        for status, count in status_counts:
            stats[status] = count
            stats["total"] += count
        
        # Calculate approval rate
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved
            FROM content 
            WHERE status IN ('approved', 'rejected')
        ''')
        
        total, approved = cursor.fetchone()
        stats["approval_rate"] = round((approved / total * 100) if total > 0 else 0, 1)
        
        # Get AI generation count
        cursor.execute('''
            SELECT COUNT(*) as generated FROM activity_log 
            WHERE action = 'content_created'
        ''')
        
        stats["generated"] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_recent_content(self, limit: int = 10) -> List[Dict]:
        """Get recent content"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM content 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            content = dict(row)
            if content.get('metadata'):
                try:
                    content['metadata'] = json.loads(content['metadata'])
                except:
                    content['metadata'] = {}
            result.append(content)
        
        return result
    
    def log_activity(self, action: str, details: str, content_id: Optional[int] = None):
        """Log system activity"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_log (action, details, content_id)
            VALUES (?, ?, ?)
        ''', (action, details, content_id))
        
        conn.commit()
        conn.close()
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Get recent activities"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM activity_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def record_approval(self, approval_record: dict):
        """Record approval in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO approvals (content_id, approver, action, comments, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            approval_record.get('content_id'),
            approval_record.get('approver'),
            'approved',
            approval_record.get('comments', '')
        ))
        
    
        cursor.execute('''
            UPDATE content 
            SET status = 'approved', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (approval_record.get('content_id'),))
        
        # Log activity
        cursor.execute('''
            INSERT INTO activity_log (action, details, content_id)
            VALUES (?, ?, ?)
        ''', ('content_approved', f'Approved by {approval_record.get("approver")}', 
              approval_record.get('content_id')))
        
        conn.commit()
        conn.close()
    
    def record_rejection(self, rejection_record: dict):
        """Record rejection in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO approvals (content_id, approver, action, comments, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            rejection_record.get('content_id'),
            rejection_record.get('reviewer'),
            'rejected',
            rejection_record.get('reason', '')
        ))
        
        # Update content status
        cursor.execute('''
            UPDATE content 
            SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (rejection_record.get('content_id'),))
        
        # Log activity
        cursor.execute('''
            INSERT INTO activity_log (action, details, content_id)
            VALUES (?, ?, ?)
        ''', ('content_rejected', f'Rejected: {rejection_record.get("reason", "")[:50]}', 
              rejection_record.get('content_id')))
        
        conn.commit()
        conn.close()
    
    def record_revision_request(self, revision_record: dict):
        """Record revision request in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO approvals (content_id, approver, action, comments, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            revision_record.get('content_id'),
            revision_record.get('reviewer'),
            'revision_requested',
            revision_record.get('notes', '')
        ))
        
        # Update content status
        cursor.execute('''
            UPDATE content 
            SET status = 'needs_revision', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (revision_record.get('content_id'),))
        
        # Log activity
        cursor.execute('''
            INSERT INTO activity_log (action, details, content_id)
            VALUES (?, ?, ?)
        ''', ('revision_requested', f'Revision: {revision_record.get("notes", "")[:50]}', 
              revision_record.get('content_id')))
        
        conn.commit()
        conn.close()
    
    def save_notification(self, notification: dict):
        """Save notification (for future email/Slack integration)"""
        
        print(f"Notification: {notification}")
    
    def get_content_by_id(self, content_id: int) -> Optional[Dict]:
        """Alias for get_content for consistency"""
        return self.get_content(content_id)
