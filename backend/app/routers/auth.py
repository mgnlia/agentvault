"""Auth0 OAuth flow and Token Vault authentication."""
import secrets
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urlencode
import logging

from app.config import settings
from app.services.token_vault import TokenVaultService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory state store (use Redis in production)
_state_store: dict[str, dict] = {}


def get_auth0_authorize_url(state: str, connection: str | None = None) -> str:
    """Build Auth0 authorization URL."""
    params = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "scope": "openid profile email offline_access",
        "audience": settings.AUTH0_AUDIENCE,
        "state": state,
    }
    if connection:
        params["connection"] = connection
    return f"https://{settings.AUTH0_DOMAIN}/authorize?{urlencode(params)}"


@router.get("/login")
async def login(request: Request, connection: str | None = None):
    """Initiate Auth0 login flow."""
    state = secrets.token_urlsafe(32)
    _state_store[state] = {"connection": connection}
    auth_url = get_auth0_authorize_url(state, connection)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    """Handle Auth0 callback and exchange code for tokens."""
    if state not in _state_store:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    _state_store.pop(state, None)

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.AUTH0_CALLBACK_URL,
            },
        )

    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.text}")
        raise HTTPException(status_code=400, detail="Token exchange failed")

    tokens = resp.json()
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    # Redirect to frontend with token
    redirect_url = f"{settings.FRONTEND_URL}/dashboard?token={access_token}"
    return RedirectResponse(url=redirect_url)


@router.post("/connect-service")
async def connect_service(
    request: Request,
    service: str,
    user_id: str,
):
    """Initiate OAuth connection for a third-party service via Token Vault."""
    # Generate step-up auth URL for service connection
    state = secrets.token_urlsafe(32)
    _state_store[state] = {"service": service, "user_id": user_id, "action": "connect"}

    # Map service to Auth0 social connection
    connection_map = {
        "github": "github",
        "google": "google-oauth2",
        "slack": "slack",
    }

    connection = connection_map.get(service)
    if not connection:
        raise HTTPException(status_code=400, detail=f"Unsupported service: {service}")

    params = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": f"{settings.AUTH0_CALLBACK_URL}/service",
        "scope": "openid profile email offline_access",
        "audience": settings.AUTH0_AUDIENCE,
        "state": state,
        "connection": connection,
        "access_type": "offline",  # Request refresh token
    }

    auth_url = f"https://{settings.AUTH0_DOMAIN}/authorize?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}


@router.get("/me")
async def get_me(request: Request):
    """Get current user info from Auth0."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header[7:]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    return resp.json()


@router.post("/step-up")
async def step_up_auth(request: Request, action: str, resource: str):
    """Initiate step-up authentication for sensitive actions."""
    state = secrets.token_urlsafe(32)
    _state_store[state] = {"action": action, "resource": resource, "step_up": True}

    params = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": f"{settings.AUTH0_CALLBACK_URL}/step-up",
        "scope": "openid",
        "state": state,
        "max_age": "0",  # Force re-authentication
        "acr_values": "http://schemas.openid.net/pape/policies/2007/06/multi-factor",
    }

    auth_url = f"https://{settings.AUTH0_DOMAIN}/authorize?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state, "requires_step_up": True}
