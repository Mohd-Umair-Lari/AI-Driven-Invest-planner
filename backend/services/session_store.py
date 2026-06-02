from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import certifi
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mockDB").strip()


def _get_db(client: MongoClient):
    return client[DB_NAME]


class SessionStore:
    """MongoDB-backed session store for token management and blacklisting."""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        self.db = _get_db(self.client)
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes for optimal performance."""
        try:
            sessions = self.db.sessions
            sessions.create_index("email")
            sessions.create_index("jti", unique=True)
            sessions.create_index("expires_at", expireAfterSeconds=0)
            sessions.create_index([("user_id", 1)])
        except PyMongoError as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def create_session(self, email: str, user_id: str, jti: str, 
                      token_type: str, expires_at: datetime) -> bool:
        """Create a new session record."""
        try:
            session_doc = {
                "email": email,
                "user_id": user_id,
                "jti": jti,
                "token_type": token_type,
                "created_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
                "is_valid": True,
                "ip_address": None,
                "user_agent": None
            }
            self.db.sessions.insert_one(session_doc)
            return True
        except PyMongoError:
            return False
    
    def get_session(self, jti: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by JWT ID."""
        try:
            session = self.db.sessions.find_one({"jti": jti})
            if session and session.get("is_valid"):
                return session
            return None
        except PyMongoError:
            return None
    
    def invalidate_session(self, jti: str) -> bool:
        """Mark a session as invalid (logout/revocation)."""
        try:
            result = self.db.sessions.update_one(
                {"jti": jti},
                {"$set": {"is_valid": False, "invalidated_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except PyMongoError:
            return False
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user (password change, etc)."""
        try:
            result = self.db.sessions.update_many(
                {"user_id": user_id, "is_valid": True},
                {"$set": {"is_valid": False, "invalidated_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count
        except PyMongoError:
            return 0
    
    def is_session_valid(self, jti: str) -> bool:
        """Check if a session is valid and not expired."""
        try:
            session = self.db.sessions.find_one({
                "jti": jti,
                "is_valid": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            return session is not None
        except PyMongoError:
            return False


class TokenBlacklist:
    """Manage token blacklist for revoked tokens."""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        self.db = _get_db(self.client)
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for blacklist collection."""
        try:
            blacklist = self.db.token_blacklist
            blacklist.create_index("jti", unique=True)
            blacklist.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError as e:
            print(f"Warning: Could not create blacklist indexes: {e}")
    
    def add_to_blacklist(self, jti: str, user_id: str, reason: str, 
                        expires_at: datetime) -> bool:
        """Add a token to the blacklist."""
        try:
            self.db.token_blacklist.insert_one({
                "jti": jti,
                "user_id": user_id,
                "reason": reason,
                "blacklisted_at": datetime.now(timezone.utc),
                "expires_at": expires_at
            })
            return True
        except PyMongoError:
            return False
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        try:
            entry = self.db.token_blacklist.find_one({
                "jti": jti,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            return entry is not None
        except PyMongoError:
            return False
    
    def get_blacklist_reason(self, jti: str) -> Optional[str]:
        """Get the reason a token was blacklisted."""
        try:
            entry = self.db.token_blacklist.find_one({"jti": jti})
            return entry.get("reason") if entry else None
        except PyMongoError:
            return None


class PasswordResetTokenStore:
    """Secure storage for password reset tokens in MongoDB."""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        self.db = _get_db(self.client)
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for reset tokens."""
        try:
            resets = self.db.password_reset_tokens
            resets.create_index("token_hash", unique=True)
            resets.create_index("email")
            resets.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError as e:
            print(f"Warning: Could not create reset token indexes: {e}")
    
    def create_reset_token(self, email: str, token_hash: str, 
                          expires_in_hours: int = 24) -> bool:
        """Create a password reset token record."""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
            self.db.password_reset_tokens.insert_one({
                "email": email,
                "token_hash": token_hash,
                "created_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
                "is_used": False,
                "used_at": None
            })
            return True
        except PyMongoError:
            return False
    
    def validate_reset_token(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Validate and retrieve a reset token."""
        try:
            token = self.db.password_reset_tokens.find_one({
                "token_hash": token_hash,
                "is_used": False,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            return token
        except PyMongoError:
            return None
    
    def mark_token_as_used(self, token_hash: str) -> bool:
        """Mark a reset token as used (prevent reuse)."""
        try:
            result = self.db.password_reset_tokens.update_one(
                {"token_hash": token_hash},
                {
                    "$set": {
                        "is_used": True,
                        "used_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except PyMongoError:
            return False
    
    def get_email_from_token(self, token_hash: str) -> Optional[str]:
        """Get email associated with a reset token."""
        try:
            token = self.db.password_reset_tokens.find_one({"token_hash": token_hash})
            return token.get("email") if token else None
        except PyMongoError:
            return None


session_store = SessionStore()
token_blacklist = TokenBlacklist()
password_reset_token_store = PasswordResetTokenStore()
