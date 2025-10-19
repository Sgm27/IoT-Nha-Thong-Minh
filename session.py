"""
Session management service for Gemini Live sessions
"""
import json
import datetime
from typing import Optional
from config.settings import settings
import os


class SessionService:
    """Service for managing Gemini Live session handles."""
    
    def __init__(self, session_file: str = None):
        """Initialize session service.
        
        Args:
            session_file: Path to session file. Uses default from settings if None.
        """
        self.session_file = session_file or settings.SESSION_FILE
        # Ensure directory exists for runtime file
        try:
            os.makedirs(os.path.dirname(self.session_file) or '.', exist_ok=True)
        except Exception:
            pass
        self.timeout_seconds = settings.SESSION_TIMEOUT_SECONDS
    
    def load_previous_session_handle(self) -> Optional[str]:
        """Load previous session handle if it's still valid.
        
        Returns:
            Session handle if valid, None otherwise.
        """
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                handle = data.get('previous_session_handle', None)
                session_time = data.get('session_time', None)
                
                if handle and session_time:
                    session_datetime = datetime.datetime.fromisoformat(session_time)
                    current_time = datetime.datetime.now()
                    time_diff = current_time - session_datetime
                    
                    if time_diff.total_seconds() < self.timeout_seconds:
                        print(f"Loaded previous session handle: {handle} (created {time_diff.total_seconds():.1f}s ago)")
                        return handle
                    else:
                        print(f"Previous session handle expired ({time_diff.total_seconds():.1f}s ago, > {self.timeout_seconds}s)")
                        return None
                else:
                    print("No valid session handle or time found")
                    return None
        except FileNotFoundError:
            print("No previous session file found")
            return None
        except Exception as e:
            print(f"Error loading session handle: {e}")
            return None
    
    def save_previous_session_handle(self, handle: str) -> None:
        """Save session handle with timestamp.
        
        Args:
            handle: Session handle to save.
        """
        current_time = datetime.datetime.now().isoformat()
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    'previous_session_handle': handle,
                    'session_time': current_time
                }, f)
            print(f"Saved session handle with timestamp: {current_time}")
        except Exception as e:
            print(f"Error saving session handle: {e}")
    
    def clear_session(self) -> None:
        """Clear stored session handle."""
        try:
            with open(self.session_file, 'w') as f:
                json.dump({}, f)
            print("Session handle cleared")
        except Exception as e:
            print(f"Error clearing session handle: {e}")
