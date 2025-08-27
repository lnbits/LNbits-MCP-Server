"""Session-based credential isolation for multi-user MCP server."""

import asyncio
import uuid
from typing import Dict, Optional
from threading import RLock
from datetime import datetime, timedelta
import structlog

from .client import LNbitsConfig
from .utils.runtime_config import RuntimeConfigManager
from .tools.core import CoreTools
from .tools.payments import PaymentTools
from .tools.invoices import InvoiceTools
from .tools.config_tools import ConfigTools

logger = structlog.get_logger(__name__)


class SessionTools:
    """Container for session-specific tool instances."""
    
    def __init__(self, session_id: str, config: Optional[LNbitsConfig] = None):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        
        # Create session-specific instances
        self.config_manager = RuntimeConfigManager(config)
        self.core_tools = CoreTools(self.config_manager)
        self.payment_tools = PaymentTools(self.config_manager)
        self.invoice_tools = InvoiceTools(self.config_manager)
        self.config_tools = ConfigTools(self.config_manager)
        
    def update_last_accessed(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
        
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session is expired."""
        expiry = self.last_accessed + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry
        
    async def cleanup(self):
        """Cleanup session resources."""
        try:
            await self.config_manager.close()
            logger.info("Session cleaned up", session_id=self.session_id)
        except Exception as e:
            logger.error("Error cleaning up session", session_id=self.session_id, error=str(e))


class SessionManager:
    """Manages isolated sessions for different MCP clients."""
    
    def __init__(self, session_timeout_minutes: int = 60):
        self._sessions: Dict[str, SessionTools] = {}
        self._lock = RLock()
        self._session_timeout = session_timeout_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    def start_cleanup_task(self):
        """Start background task to clean up expired sessions."""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        self._shutdown = True
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while not self._shutdown:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._remove_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in session cleanup task", error=str(e))
                
    async def _remove_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = []
        
        with self._lock:
            for session_id, session in self._sessions.items():
                if session.is_expired(self._session_timeout):
                    expired_sessions.append(session_id)
                    
        for session_id in expired_sessions:
            await self.remove_session(session_id)
            
    def create_session(self, config: Optional[LNbitsConfig] = None) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        
        with self._lock:
            session_tools = SessionTools(session_id, config)
            self._sessions[session_id] = session_tools
            
        logger.info("Session created", session_id=session_id, total_sessions=len(self._sessions))
        return session_id
        
    def get_session(self, session_id: str) -> Optional[SessionTools]:
        """Get session tools for a session ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_last_accessed()
                return session
            return None
            
    async def remove_session(self, session_id: str) -> bool:
        """Remove a session and cleanup resources."""
        session = None
        
        with self._lock:
            session = self._sessions.pop(session_id, None)
            
        if session:
            await session.cleanup()
            logger.info("Session removed", session_id=session_id, total_sessions=len(self._sessions))
            return True
            
        return False
        
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        with self._lock:
            return len(self._sessions)
            
    async def cleanup_all_sessions(self):
        """Cleanup all sessions."""
        session_ids = []
        
        with self._lock:
            session_ids = list(self._sessions.keys())
            
        for session_id in session_ids:
            await self.remove_session(session_id)
            
        await self.stop_cleanup_task()


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_session_manager_lock = RLock()


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager
    
    with _session_manager_lock:
        if _session_manager is None:
            _session_manager = SessionManager()
            _session_manager.start_cleanup_task()
        return _session_manager


async def cleanup_session_manager():
    """Cleanup global session manager."""
    global _session_manager
    
    with _session_manager_lock:
        if _session_manager:
            await _session_manager.cleanup_all_sessions()
            _session_manager = None