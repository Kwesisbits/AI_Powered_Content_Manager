import sqlite3
import json
from datetime import datetime

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    # Content table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            media_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_date TEXT,
            approved_by TEXT,
            approved_at TIMESTAMP
        )
    ''')
    
    # System logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_content(content: dict, platform: str, topic: str, status: str = "pending"):
    """Save generated content to database"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO content (topic, platform, content, status)
        VALUES (?, ?, ?, ?)
    ''', (topic, platform, json.dumps(content), status))
    
    content_id = cursor.lastrowid
    
    # Log event
    cursor.execute('''
        INSERT INTO logs (event, details)
        VALUES (?, ?)
    ''', ('content_created', f'Topic: {topic}, Platform: {platform}'))
    
    conn.commit()
    conn.close()
    return content_id

def get_pending_approvals():
    """Get all content pending approval"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, topic, platform, content, created_at 
        FROM content 
        WHERE status = 'pending'
        ORDER BY created_at DESC
    ''')
    
    results = []
    for row in cursor.fetchall():
        try:
            content_data = json.loads(row[3])
        except:
            content_data = {"post_text": row[3]}
        
        results.append((
            row[0],  # id
            row[1],  # topic
            row[2],  # platform
            content_data.get('post_text', 'No content'),
            row[4]   # created_at
        ))
    
    conn.close()
    return results

def approve_content(content_id: int, approver: str):
    """Approve content"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE content 
        SET status = 'approved', 
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (approver, content_id))
    
    cursor.execute('''
        INSERT INTO logs (event, details)
        VALUES (?, ?)
    ''', ('content_approved', f'ID: {content_id}, By: {approver}'))
    
    conn.commit()
    conn.close()

def reject_content(content_id: int, reason: str):
    """Reject content"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE content 
        SET status = 'rejected'
        WHERE id = ?
    ''', (content_id,))
    
    cursor.execute('''
        INSERT INTO logs (event, details)
        VALUES (?, ?)
    ''', ('content_rejected', f'ID: {content_id}, Reason: {reason}'))
    
    conn.commit()
    conn.close()

def get_all_content():
    """Get all content for monitoring"""
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, topic, platform, status, created_at 
        FROM content 
        ORDER BY created_at DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results
