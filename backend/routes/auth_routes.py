"""FastAPI auth routes: login, signup, token refresh, logout, password reset."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Header

from api.schemas import LoginRequest, SignupRequest
from auth.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyResetTokenRequest,
)
from auth.forgot_password import forgot_password_service
from db import collection, serialize, ensure_onboarding
from services.jwt_handler import JWTHandler, TokenValidator, PasswordHasher
from services.session_store import session_store, token_blacklist, password_reset_token_store
from services.security_utils import rate_limiter, SecurityValidator
from config.logging_config import setup_logging

log = setup_logging()

router = APIRouter(tags=["Auth"])


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------
@router.post("/api/login")
async def api_login(body: LoginRequest):
    try:
        email_lower = body.email.lower()
        log.info(f"Login attempt for: {email_lower}")

        rate_check = rate_limiter.check_rate_limit(
            identifier=email_lower,
            action="login",
            max_attempts=5,
            window_seconds=300,
        )
        if not rate_check["allowed"]:
            log.warning(
                f"Rate limit exceeded for login: {email_lower} "
                f"({rate_check['attempt_count']}/5)"
            )
            raise HTTPException(
                429,
                f"Too many login attempts. Try again in {rate_check['reset_at']}",
            )

        user = collection.find_one({"email": email_lower})
        if not user:
            log.warning(f"User not found: {email_lower}")
            raise HTTPException(401, "Invalid credentials")

        stored_password = user.get("password") or ""
        if not PasswordHasher.verify(body.password, stored_password):
            log.warning(f"Invalid password for user: {email_lower}")
            raise HTTPException(401, "Invalid credentials")

        if PasswordHasher.needs_rehash(stored_password):
            collection.update_one(
                {"email": email_lower},
                {"$set": {"password": PasswordHasher.hash(body.password)}},
            )
            log.info(f"Upgraded legacy password hash for: {email_lower}")

        log.info(f"Password verified for: {email_lower}")

        user = ensure_onboarding(email_lower, user)

        access_token = JWTHandler.create_access_token(email_lower, str(user["_id"]))
        refresh_token = JWTHandler.create_refresh_token(email_lower, str(user["_id"]))

        access_claims = TokenValidator.validate_access_token(access_token)
        refresh_claims = TokenValidator.validate_refresh_token(refresh_token)

        if access_claims:
            session_store.create_session(
                email=email_lower,
                user_id=str(user["_id"]),
                jti=access_claims["jti"],
                token_type="access",
                expires_at=datetime.fromtimestamp(access_claims["exp"], timezone.utc),
            )
        if refresh_claims:
            session_store.create_session(
                email=email_lower,
                user_id=str(user["_id"]),
                jti=refresh_claims["jti"],
                token_type="refresh",
                expires_at=datetime.fromtimestamp(refresh_claims["exp"], timezone.utc),
            )

        collection.update_one(
            {"email": email_lower},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}},
        )

        rate_limiter.reset_limit(email_lower, "login")

        log.info(f"Login successful for: {email_lower}")
        return {
            "status": "success",
            "user": serialize(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Login error for {body.email}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Login failed: {str(e)}")


# ------------------------------------------------------------------
# Signup
# ------------------------------------------------------------------
@router.post("/api/signup", status_code=201)
async def api_signup(body: SignupRequest):
    try:
        from bson import ObjectId
        from db import trigger_user_indexing

        email_lower = body.email.lower()
        log.info(f"Signup attempt for: {email_lower}")

        rate_check = rate_limiter.check_rate_limit(
            identifier=email_lower,
            action="register",
            max_attempts=3,
            window_seconds=600,
        )
        if not rate_check["allowed"]:
            log.warning(f"Rate limit exceeded for registration: {email_lower}")
            raise HTTPException(429, "Too many registration attempts. Try again later.")

        if collection.find_one({"email": email_lower}):
            log.warning(f"Email already registered: {email_lower}")
            raise HTTPException(409, "Email already registered")

        pwd_validation = SecurityValidator.validate_password_strength(body.password)
        if not pwd_validation["is_strong"]:
            log.warning(f"Weak password for registration: {email_lower}")
            issues = "; ".join(pwd_validation["issues"])
            raise HTTPException(400, f"Password is not strong enough. {issues}")

        doc = {
            "_id": ObjectId(),
            "Name": body.Name,
            "email": email_lower,
            "password": PasswordHasher.hash(body.password),
            "Age": body.Age or "",
            "employment-status": body.employment_status or "Salaried",
            "Goal": body.Goal or {},
            "financials": body.financials or {},
            "investments": body.investments or {},
            "progress": body.progress or {},
            "onboarding": {
                "status": "in_progress",
                "current_step": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "security_version": 1,
        }

        result = collection.insert_one(doc)
        log.info(f"User created: {email_lower} (ID: {result.inserted_id})")

        access_token = JWTHandler.create_access_token(email_lower, str(result.inserted_id))
        refresh_token = JWTHandler.create_refresh_token(email_lower, str(result.inserted_id))

        access_claims = TokenValidator.validate_access_token(access_token)
        refresh_claims = TokenValidator.validate_refresh_token(refresh_token)

        if access_claims:
            session_store.create_session(
                email=email_lower,
                user_id=str(result.inserted_id),
                jti=access_claims["jti"],
                token_type="access",
                expires_at=datetime.fromtimestamp(access_claims["exp"], timezone.utc),
            )
        if refresh_claims:
            session_store.create_session(
                email=email_lower,
                user_id=str(result.inserted_id),
                jti=refresh_claims["jti"],
                token_type="refresh",
                expires_at=datetime.fromtimestamp(refresh_claims["exp"], timezone.utc),
            )

        trigger_user_indexing(email_lower)

        log.info(f"Signup successful for: {email_lower}")
        return {
            "status": "success",
            "user": serialize(doc),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Signup error for {body.email}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Signup failed: {str(e)}")


# ------------------------------------------------------------------
# Token refresh
# ------------------------------------------------------------------
@router.post("/api/auth/refresh")
async def refresh_token(body: dict):
    try:
        email = body.get("email", "").lower()
        refresh = body.get("refresh_token", "")

        if not email or not refresh:
            raise HTTPException(400, "email and refresh_token required")

        claims = TokenValidator.validate_refresh_token(refresh)
        if not claims:
            raise HTTPException(401, "Invalid or expired refresh token")

        if token_blacklist.is_blacklisted(claims["jti"]):
            raise HTTPException(401, "Refresh token has been revoked")

        if not session_store.is_session_valid(claims["jti"]):
            raise HTTPException(401, "Session expired or invalidated")

        if claims["sub"] != email:
            log.warning(f"Email mismatch in refresh token: {email} vs {claims['sub']}")
            raise HTTPException(401, "Invalid refresh token")

        user = collection.find_one({"email": email})
        if not user:
            raise HTTPException(401, "User not found")

        new_access_token = JWTHandler.create_access_token(email, claims["user_id"])
        new_access_claims = TokenValidator.validate_access_token(new_access_token)

        if new_access_claims:
            session_store.create_session(
                email=email,
                user_id=claims["user_id"],
                jti=new_access_claims["jti"],
                token_type="access",
                expires_at=datetime.fromtimestamp(new_access_claims["exp"], timezone.utc),
            )

        log.info(f"Token refreshed for: {email}")
        return {
            "access_token": new_access_token,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": 900,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Token refresh failed: {str(e)}")


# ------------------------------------------------------------------
# Logout
# ------------------------------------------------------------------
@router.post("/api/auth/logout")
async def logout(authorization: str = Header(None)):
    """Logout user and revoke current session."""
    try:
        if not authorization:
            raise HTTPException(401, "Authorization header missing")

        token = authorization.removeprefix("Bearer ").strip()
        claims = TokenValidator.validate_access_token(token)

        if not claims:
            raise HTTPException(401, "Invalid token")

        jti = claims["jti"]
        user_id = claims.get("user_id")
        email = claims["sub"]

        session_store.invalidate_session(jti)
        token_blacklist.add_to_blacklist(
            jti=jti,
            user_id=user_id,
            reason="logout",
            expires_at=datetime.fromtimestamp(claims["exp"], timezone.utc),
        )

        log.info(f"User logged out: {email}")
        return {"message": "Logged out successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Logout failed: {str(e)}")


# ------------------------------------------------------------------
# Logout all devices
# ------------------------------------------------------------------
@router.post("/api/auth/logout-all")
async def logout_all(authorization: str = Header(None)):
    """Logout user from all devices."""
    try:
        if not authorization:
            raise HTTPException(401, "Authorization header missing")

        token = authorization.removeprefix("Bearer ").strip()
        claims = TokenValidator.validate_access_token(token)

        if not claims:
            raise HTTPException(401, "Invalid token")

        user_id = claims.get("user_id")
        email = claims["sub"]

        count = session_store.invalidate_all_user_sessions(user_id)
        log.warning(f"All sessions invalidated for user: {email} ({count} sessions)")

        return {"message": "Logged out from all devices", "sessions_invalidated": count}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Logout-all error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Logout failed: {str(e)}")


# ------------------------------------------------------------------
# Forgot password
# ------------------------------------------------------------------
@router.post("/api/auth/forgot-password", status_code=200)
async def forgot_password(body: ForgotPasswordRequest):
    try:
        email_lower = body.email.strip().lower()
        log.info(f"Forgot password request for: {email_lower}")

        rate_check = rate_limiter.check_rate_limit(
            identifier=email_lower,
            action="forgot_password",
            max_attempts=3,
            window_seconds=900,
        )
        if not rate_check["allowed"]:
            log.warning(f"Rate limit exceeded for password reset: {email_lower}")
            return {
                "success": True,
                "message": "If an account exists with this email, you will receive a password reset link shortly.",
            }

        user = collection.find_one(
            {"email": {"$regex": f"^{email_lower}$", "$options": "i"}}
        )

        if user:
            reset_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

            password_reset_token_store.create_reset_token(
                email=user["email"],
                token_hash=token_hash,
                expires_in_hours=24,
            )

            log.info(f"Reset token created for: {email_lower}")
            success, message = forgot_password_service.send_reset_email(
                user["email"], reset_token
            )

            if success:
                log.info(f"Password reset email sent successfully to: {email_lower}")
            else:
                log.error(f"Failed to send reset email to {email_lower}: {message}")

        return {
            "success": True,
            "message": "If an account exists with this email, you will receive a password reset link shortly.",
        }

    except Exception as e:
        log.error(f"Forgot password error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "An error occurred processing your request. Please try again later.",
        }


# ------------------------------------------------------------------
# Verify reset token
# ------------------------------------------------------------------
@router.post("/api/auth/verify-reset-token")
async def verify_reset_token(body: VerifyResetTokenRequest):
    try:
        log.info("Verifying reset token")
        token_hash = hashlib.sha256(body.token.encode()).hexdigest()
        token_record = password_reset_token_store.validate_reset_token(token_hash)

        if not token_record:
            log.warning("Invalid or expired reset token provided")
            raise HTTPException(400, "Invalid or expired reset token")

        email = token_record["email"]
        log.info(f"Reset token verified for: {email}")
        return {
            "success": True,
            "email": email,
            "message": "Token is valid. You can now reset your password.",
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error verifying reset token: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error verifying token: {str(e)}")


# ------------------------------------------------------------------
# Reset password
# ------------------------------------------------------------------
@router.post("/api/auth/reset-password")
async def reset_password(body: ResetPasswordRequest):
    try:
        if body.new_password != body.confirm_password:
            raise HTTPException(400, "Passwords do not match")

        pwd_validation = SecurityValidator.validate_password_strength(body.new_password)
        if not pwd_validation["is_strong"]:
            raise HTTPException(
                400,
                {"error": "Password is not strong enough", "issues": pwd_validation["issues"]},
            )

        log.info("Processing password reset")
        token_hash = hashlib.sha256(body.token.encode()).hexdigest()
        token_record = password_reset_token_store.validate_reset_token(token_hash)

        if not token_record:
            log.warning("Invalid or expired token for password reset")
            raise HTTPException(400, "Invalid or expired reset token")

        email = token_record["email"]
        user = collection.find_one({"email": email})

        if not user:
            log.warning(f"User not found for password reset: {email}")
            raise HTTPException(404, "User not found")

        collection.update_one(
            {"email": email},
            {
                "$set": {
                    "password": PasswordHasher.hash(body.new_password),
                    "password_reset_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        password_reset_token_store.mark_token_as_used(token_hash)
        count = session_store.invalidate_all_user_sessions(str(user["_id"]))

        success, message = forgot_password_service.send_password_changed_email(email)
        if success:
            log.warning(
                f"Password reset and all sessions invalidated: {email} ({count} sessions)"
            )
        else:
            log.warning(
                f"Password reset but confirmation email failed for {email}: {message}"
            )

        return {
            "success": True,
            "message": "Password has been reset successfully. You can now log in with your new password.",
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error resetting password: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error resetting password: {str(e)}")
