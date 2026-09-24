"""Google OAuth2 routes (Authorization Code flow)."""

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from services import google_oauth
from config.logging_config import setup_logging

log = setup_logging()

router = APIRouter(tags=["Google OAuth"])


@router.get("/api/auth/google/authorize")
async def google_authorize():
    """Start the flow: redirect the browser to Google's consent screen."""
    try:
        authorize_url = google_oauth.build_authorize_url()
        return RedirectResponse(authorize_url, status_code=302)
    except ValueError as e:
        log.error(f"Google OAuth not configured: {e}")
        raise HTTPException(500, f"Google OAuth is not configured: {e}")


@router.get("/api/auth/google/callback")
async def google_callback(
    code: str = Query("", description="Authorization code from Google"),
    state: str = Query("", description="CSRF state"),
    error: str = Query("", description="Google error code, if any"),
):
    """
    Google redirects here with ?code=...&state=....
    We exchange the code, upsert the user, issue JWTs, and redirect the browser
    to the frontend callback page, passing tokens via the URL fragment.
    """
    frontend = google_oauth.get_frontend_base_url()
    callback_page = f"{frontend}/static/callback.html"

    if error:
        log.warning(f"Google OAuth denied: {error}")
        # User backed out / declined consent — fail cleanly, issue nothing.
        code_out = "cancelled" if error == "access_denied" else "oauth_error"
        return RedirectResponse(f"{callback_page}?error={code_out}", status_code=302)

    if not code:
        raise HTTPException(400, "Missing authorization code")

    if not google_oauth._consume_state(state):
        log.warning("Google OAuth state validation failed")
        return RedirectResponse(f"{callback_page}?error=invalid_state", status_code=302)

    try:
        access_token = google_oauth.exchange_code_for_token(code)
        google_user = google_oauth.fetch_google_user(access_token)
        session = google_oauth.create_app_session(google_oauth.upsert_google_user(google_user))
    except ValueError as e:
        log.error(f"Google OAuth token exchange failed: {e}")
        return RedirectResponse(f"{callback_page}?error=token_exchange_failed", status_code=302)
    except Exception as e:
        log.error(f"Google OAuth callback error: {e}", exc_info=True)
        return RedirectResponse(f"{callback_page}?error=server_error", status_code=302)

    fragment = urlencode(
        {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
        }
    )
    return RedirectResponse(f"{callback_page}#{fragment}", status_code=302)
