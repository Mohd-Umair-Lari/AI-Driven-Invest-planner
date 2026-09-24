"""GitHub OAuth2 routes (Authorization Code flow) + /api/me profile endpoint."""

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import RedirectResponse

from db import collection, serialize
from services import github_oauth
from services.jwt_handler import TokenValidator
from config.logging_config import setup_logging

log = setup_logging()

router = APIRouter(tags=["GitHub OAuth"])


@router.get("/api/me")
async def get_me(authorization: str = Header(default="")):
    """Return the current user's profile from a Bearer access token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")

    claims = TokenValidator.validate_access_token(authorization[7:])
    if not claims:
        raise HTTPException(401, "Invalid or expired token")

    user = collection.find_one({"email": claims["sub"]})
    if not user:
        raise HTTPException(404, "User not found")

    return {"status": "success", "user": serialize(user)}


@router.get("/api/auth/github/authorize")
async def github_authorize():
    """Start the flow: redirect the browser to GitHub's consent screen."""
    try:
        authorize_url = github_oauth.build_authorize_url()
        return RedirectResponse(authorize_url, status_code=302)
    except ValueError as e:
        log.error(f"GitHub OAuth not configured: {e}")
        raise HTTPException(500, f"GitHub OAuth is not configured: {e}")


@router.get("/api/auth/github/callback")
async def github_callback(
    code: str = Query("", description="Authorization code from GitHub"),
    state: str = Query("", description="CSRF state"),
    error: str = Query("", description="GitHub error code, if any"),
    error_description: str = Query("", description="GitHub error description, if any"),
):
    """
    GitHub redirects here with ?code=...&state=....
    We exchange the code, upsert the user, issue JWTs, and redirect the
    browser to the frontend callback page, passing tokens via URL fragment
    (fragments never reach server logs or the network after the '#').
    """
    frontend = github_oauth.get_frontend_base_url()
    callback_page = f"{frontend}/static/callback.html"

    if error:
        log.warning(f"GitHub OAuth denied: {error} - {error_description}")
        # User backed out / declined consent — fail cleanly, issue nothing.
        code_out = "cancelled" if error in ("access_denied", "user_cancelled_authorize") else "oauth_error"
        return RedirectResponse(f"{callback_page}?error={code_out}", status_code=302)

    if not code:
        raise HTTPException(400, "Missing authorization code")

    if not github_oauth._consume_state(state):
        log.warning("GitHub OAuth state validation failed")
        return RedirectResponse(f"{callback_page}?error=invalid_state", status_code=302)

    try:
        access_token = github_oauth.exchange_code_for_token(code)
        github_user = github_oauth.fetch_github_user(access_token)
        user = github_oauth.upsert_github_user(github_user)
        session = github_oauth.create_app_session(user)
    except ValueError as e:
        log.error(f"GitHub OAuth token exchange failed: {e}")
        return RedirectResponse(f"{callback_page}?error=token_exchange_failed", status_code=302)
    except Exception as e:
        log.error(f"GitHub OAuth callback error: {e}", exc_info=True)
        return RedirectResponse(f"{callback_page}?error=server_error", status_code=302)

    # Pass tokens in the URL fragment (never sent to servers / logs).
    fragment = urlencode(
        {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
        }
    )
    return RedirectResponse(f"{callback_page}#{fragment}", status_code=302)
