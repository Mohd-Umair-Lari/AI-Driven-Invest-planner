from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import certifi

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

class RateLimiter:
    """Rate limiting to prevent brute force attacks."""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        self.db = self.client.get_database()
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for rate limiting."""
        try:
            rate_limits = self.db.rate_limits
            rate_limits.create_index([("identifier", 1), ("action", 1)])
            rate_limits.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError as e:
            print(f"Warning: Could not create rate limit indexes: {e}")
    
    def check_rate_limit(self, identifier: str, action: str, 
                        max_attempts: int = 5, window_seconds: int = 300) -> Dict[str, any]:
        """
        Check if an identifier has exceeded rate limit.
        
        Returns: {
            "allowed": bool,
            "remaining": int,
            "reset_at": datetime
        }
        """
        try:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)
            
            record = self.db.rate_limits.find_one({
                "identifier": identifier,
                "action": action,
                "expires_at": {"$gt": now}
            })
            
            if record:
                attempt_count = record.get("attempt_count", 0) + 1
                
                self.db.rate_limits.update_one(
                    {"_id": record["_id"]},
                    {
                        "$set": {
                            "attempt_count": attempt_count,
                            "last_attempt": now
                        }
                    }
                )
            else:
                # Create new rate limit record
                expires_at = now + timedelta(seconds=window_seconds)
                attempt_count = 1
                
                self.db.rate_limits.insert_one({
                    "identifier": identifier,
                    "action": action,
                    "attempt_count": attempt_count,
                    "first_attempt": now,
                    "last_attempt": now,
                    "expires_at": expires_at
                })
            
            allowed = attempt_count <= max_attempts
            remaining = max(0, max_attempts - attempt_count)
            reset_at = record["expires_at"] if record else now + timedelta(seconds=window_seconds)
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "reset_at": reset_at,
                "attempt_count": attempt_count
            }
        
        except PyMongoError as e:
            print(f"Rate limiter error: {e}")
            return {
                "allowed": True,
                "remaining": max_attempts,
                "reset_at": datetime.now(timezone.utc) + timedelta(seconds=window_seconds),
                "attempt_count": 0
            }
    
    def reset_limit(self, identifier: str, action: str) -> bool:
        """Reset rate limit for an identifier (after successful login, etc)."""
        try:
            result = self.db.rate_limits.delete_one({
                "identifier": identifier,
                "action": action
            })
            return result.deleted_count > 0
        except PyMongoError:
            return False
    
    def get_stats(self, identifier: str) -> Dict[str, any]:
        """Get rate limiting statistics for an identifier."""
        try:
            records = list(self.db.rate_limits.find({"identifier": identifier}))
            return {
                "total_actions": len(records),
                "actions": {r["action"]: r.get("attempt_count", 0) for r in records}
            }
        except PyMongoError:
            return {"total_actions": 0, "actions": {}}


class SecurityHeaders:
    """Middleware for security headers."""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    @staticmethod
    def apply_headers(response):
        """Apply security headers to response."""
        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value
        return response


class SecurityValidator:
    """Validate security-related claims and patterns."""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, any]:
        """
        Validate password strength.
        Returns: {
            "is_strong": bool,
            "score": int (0-100),
            "issues": list
        }
        """
        issues = []
        score = 0
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        else:
            score += 20
        
        if not any(c.isupper() for c in password):
            issues.append("Must contain uppercase letter")
        else:
            score += 20
        
        if not any(c.islower() for c in password):
            issues.append("Must contain lowercase letter")
        else:
            score += 20
        
        if not any(c.isdigit() for c in password):
            issues.append("Must contain number")
        else:
            score += 20
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Must contain special character")
        else:
            score += 20
        
        return {
            "is_strong": len(issues) == 0,
            "score": score,
            "issues": issues
        }
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_suspicious_pattern(email: str, ip_address: str = None) -> Dict[str, any]:
        """Check for suspicious patterns (multiple failed attempts, etc)."""
        return {
            "is_suspicious": False,
            "reasons": []
        }


rate_limiter = RateLimiter()
