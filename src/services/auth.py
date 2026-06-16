"""
42 OAuth flow.

How 42 OAuth works:
1. We redirect user to 42's auth page with our client_id
2. 42 redirects back to /auth/callback with a ?code=...
3. We exchange that code for an access token (server-to-server)
4. We use the token to fetch the user's profile from 42 API
5. We create/update the user in our DB and store their id in the session
"""
import os
import httpx
from nicegui import app  # NiceGUI exposes a FastAPI app we attach routes to
import secrets


OAUTH_CLIENT_ID     = os.environ["OAUTH_CLIENT_ID"]
OAUTH_CLIENT_SECRET = os.environ["OAUTH_CLIENT_SECRET"]
OAUTH_REDIRECT_URI  = os.environ["OAUTH_REDIRECT_URI"]

AUTHORIZE_URL = "https://api.intra.42.fr/oauth/authorize"
TOKEN_URL     = "https://api.intra.42.fr/oauth/token"
USER_API_URL  = "https://api.intra.42.fr/v2/me"

# old one
# def get_login_url() -> str:
#     """Build the URL to send users to for 42 login."""
#     return (
#         f"{AUTHORIZE_URL}"
#         f"?client_id={OAUTH_CLIENT_ID}"
#         f"&redirect_uri={OAUTH_REDIRECT_URI}"
#         f"&response_type=code"
#     )


def get_login_url() -> str:
    state = secrets.token_urlsafe(32)
    app.storage.user["oauth_state"] = state   # store in session
    return (
        f"{AUTHORIZE_URL}"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={OAUTH_REDIRECT_URI}"
        f"&response_type=code"
        f"&state={state}"
    )


async def exchange_code_for_user(code: str) -> dict:
    """
    Given the OAuth code from 42's callback,
    fetch and return the user's 42 profile dict.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: exchange code for token
        token_resp = await client.post(TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "client_id":     OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "code":          code,
            "redirect_uri":  OAUTH_REDIRECT_URI,
        })
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # Step 2: use token to get profile
        profile_resp = await client.get(
            USER_API_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        profile_resp.raise_for_status()
        return profile_resp.json()
