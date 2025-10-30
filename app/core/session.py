"""
Session management for multi-user support.
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading
from collections import defaultdict

from app.utils.logger import logger
from app.config import settings


class SessionManager:
    """
    Thread-safe session manager for storing user conversation states.
    In production, use Redis or similar distributed cache.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._session_timestamps: Dict[str, datetime] = {}
        
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data dictionary
        """
        with self._lock:
            session_data = {
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "messages": [],
                "loan_application": {
                    "applicant_name": None,
                    "desired_amount": None,
                    "loan_term_months": None,
                    "purpose": None,
                    "kyc_verified": False,
                    "credit_score": None,
                    "credit_eligibility": "pending",
                    "offered_amount": None,
                    "offered_interest_rate": None,
                    "sanction_letter_generated": False,
                    "sanction_letter_url": None,
                    "status": "initiated"
                },
                "extracted_info": {}
            }
            
            self._sessions[session_id] = session_data
            self._session_timestamps[session_id] = datetime.utcnow()
            
            logger.info(f"Session created: {session_id}")
            return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                self._session_timestamps[session_id] = datetime.utcnow()
            return session
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            self._sessions[session_id].update(data)
            self._session_timestamps[session_id] = datetime.utcnow()
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                del self._session_timestamps[session_id]
                logger.info(f"Session deleted: {session_id}")
                return True
            return False
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """
        Remove sessions older than specified age.
        
        Args:
            max_age_hours: Maximum session age in hours
        """
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            expired = [
                sid for sid, ts in self._session_timestamps.items()
                if ts < cutoff_time
            ]
            
            for session_id in expired:
                del self._sessions[session_id]
                del self._session_timestamps[session_id]
                logger.info(f"Expired session cleaned up: {session_id}")
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        with self._lock:
            return len(self._sessions)
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to session history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant/system)
            content: Message content
        """
        with self._lock:
            if session_id in self._sessions:
                messages = self._sessions[session_id]["messages"]
                messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Trim message history to prevent memory issues
                if len(messages) > settings.MAX_MESSAGE_HISTORY:
                    self._sessions[session_id]["messages"] = messages[-settings.MAX_MESSAGE_HISTORY:]

