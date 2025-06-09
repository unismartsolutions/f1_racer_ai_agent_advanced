import streamlit as st
import hashlib
import os
from typing import Dict, Optional

class AuthManager:
    """Simple authentication manager for the F1 Agent application"""
    
    def __init__(self):
        # Define demo users - in production, this would be in a database
        self.users = {
            "admin": {
                "password_hash": self._hash_password("f1racing2024"),
                "role": "admin",
                "display_name": "Administrator"
            }
        }
        
        # Load additional users from environment if available
        self._load_env_users()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_env_users(self):
        """Load additional users from environment variables. For app deployment"""
        # Check for custom admin credentials
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if admin_username and admin_password:
            self.users[admin_username] = {
                "password_hash": self._hash_password(admin_password),
                "role": "admin",
                "display_name": "Custom Admin"
            }
        
        # Check for additional user credentials
        for i in range(1, 6):  # Support up to 5 additional users. Local development
            username = os.getenv(f"USER_{i}_USERNAME")
            password = os.getenv(f"USER_{i}_PASSWORD")
            role = os.getenv(f"USER_{i}_ROLE", "user")
            
            if username and password:
                self.users[username] = {
                    "password_hash": self._hash_password(password),
                    "role": role,
                    "display_name": f"User {i}"
                }
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        if not username or not password:
            return False
        
        user = self.users.get(username.lower())
        if not user:
            return False
        
        password_hash = self._hash_password(password)
        return password_hash == user["password_hash"]
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        user = self.users.get(username.lower())
        if user:
            return {
                "username": username.lower(),
                "role": user["role"],
                "display_name": user["display_name"]
            }
        return None
    
    def is_admin(self, username: str) -> bool:
        """Check if user is admin"""
        user = self.users.get(username.lower())
        return user and user["role"] == "admin"

# Global auth manager instance
auth_manager = AuthManager()

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user and store in session"""
    if auth_manager.authenticate(username, password):
        # Store user info in session
        user_info = auth_manager.get_user_info(username)
        if user_info:
            st.session_state.user_info = user_info
            return True
    return False

def check_authentication() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_user() -> Optional[Dict]:
    """Get current user information"""
    return st.session_state.get('user_info')

def require_auth():
    """Decorator/function to require authentication"""
    if not check_authentication():
        st.error("Authentication required. Please login.")
        st.stop()

def logout_user():
    """Logout current user"""
    for key in ['authenticated', 'user_info', 'username']:
        if key in st.session_state:
            del st.session_state[key]

# Session management functions
def init_session():
    """Initialize session state for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

def get_session_info() -> Dict:
    """Get session information for debugging"""
    return {
        "authenticated": st.session_state.get('authenticated', False),
        "user_info": st.session_state.get('user_info'),
        "session_keys": list(st.session_state.keys())
    }

# Password strength validation
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength (for future user registration)"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password strength is adequate"

# Rate limiting (basic implementation)
import time
from collections import defaultdict

class RateLimiter:
    """Simple rate limiter for login attempts"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_seconds = window_minutes * 60
        self.attempts = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if login attempt is allowed"""
        now = time.time()
        
        # Clean old attempts
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if now - attempt_time < self.window_seconds
        ]
        
        # Check if under limit
        return len(self.attempts[identifier]) < self.max_attempts
    
    def record_attempt(self, identifier: str):
        """Record a login attempt"""
        self.attempts[identifier].append(time.time())
    
    def get_wait_time(self, identifier: str) -> int:
        """Get wait time before next attempt allowed"""
        if not self.attempts[identifier]:
            return 0
        
        oldest_attempt = min(self.attempts[identifier])
        wait_time = self.window_seconds - (time.time() - oldest_attempt)
        return max(0, int(wait_time))

# Global rate limiter
rate_limiter = RateLimiter()

def check_rate_limit(identifier: str) -> tuple[bool, int]:
    """Check if login attempt is rate limited"""
    if rate_limiter.is_allowed(identifier):
        return True, 0
    else:
        wait_time = rate_limiter.get_wait_time(identifier)
        return False, wait_time

def record_login_attempt(identifier: str):
    """Record a login attempt for rate limiting"""
    rate_limiter.record_attempt(identifier)
