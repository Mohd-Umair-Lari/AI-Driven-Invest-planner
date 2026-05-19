import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple

class TokenManager:
    """Manages password reset tokens with expiration and one-time use"""
    
    def __init__(self):
        self.token_store = {}  # In production, use Redis or database
    
    def generate_reset_token(self, email: str, expires_in_hours: int = 24) -> str:
        """
        Generate a secure reset token for password reset
        
        Args:
            email: User email address
            expires_in_hours: Token expiration time in hours
            
        Returns:
            Reset token string
        """
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        expiration = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        self.token_store[token_hash] = {
            "email": email,
            "expires_at": expiration.isoformat(),
            "used": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return token
    
    def validate_reset_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a reset token
        
        Args:
            token: Reset token to validate
            
        Returns:
            Tuple of (is_valid, email) or (False, None) if invalid
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in self.token_store:
            return False, None
        
        token_data = self.token_store[token_hash]
        
        # Check if token has been used
        if token_data.get("used"):
            return False, None
        
        # Check if token has expired
        expiration = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expiration:
            return False, None
        
        return True, token_data["email"]
    
    def mark_token_as_used(self, token: str) -> bool:
        """
        Mark a token as used (one-time use)
        
        Args:
            token: Token to mark as used
            
        Returns:
            True if marked successfully, False otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.token_store:
            self.token_store[token_hash]["used"] = True
            return True
        
        return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from storage"""
        expired_tokens = []
        
        for token_hash, data in self.token_store.items():
            expiration = datetime.fromisoformat(data["expires_at"])
            if datetime.utcnow() > expiration:
                expired_tokens.append(token_hash)
        
        for token_hash in expired_tokens:
            del self.token_store[token_hash]


# Global token manager instance
token_manager = TokenManager()
