"""Auth0 OAuth flow router — handles service connections via Token Vault."""
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import settings
from app.auth.token_vault import vault

logger = logging.getLogger(__name__)
router = APIRouter()

# OAuth endpoints per service
OAUTH_CONFIG = {
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scopes": "repo read:user user:email",
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
    },
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
    },
    "slack": {
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": "channels:read chat:write users:read",
        "client_id": settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET,
    },
}


class ConnectServiceRequest(BaseModel):
    service: str
    user_id: str


@router.post("/connect-service")
async def connect_service(req: ConnectServiceRequest):
    """Generate OAuth authorization URL for connecting a service."""
    cfg = OAUTH_CONFIG.get(req.service)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Unknown service: {req.service}")

    if not cfg["client_id"]:
        # Demo mode — simulate connection
        await vault.store_token(
            user_id=req.user_id,
            service=req.service,
            access_token=f"demo_token_{req.service}_{req.user_id}",
            scopes=cfg["scopes"].split(),
        )
        return {"status": "demo_connected", "service": req.service, "auth_url": None}

    callback = f"{settings.AUTH0_CALLBACK_URL.rsplit('/callback', 1)[0]}/callback/{req.service}"
    state = f"{req.user_id}:{req.service}"

    auth_url = (
        f"{cfg['auth_url']}?"
        f"client_id={cfg['client_id']}&"
        f"redirect_uri={callback}&"
        f"scope={cfg['scopes'].replace(' ', '%20')}&"
        f"state={state}&"
        f"response_type=code"
    )

    if req.service == "google":
        auth_url += "&access_type=offline&prompt=consent"

    return {"status": "redirect", "auth_url": auth_url, "service": req.service}


@router.get("/callback/{service}")
async def oauth_callback(service: str, code: str = Query(...), state: str = Query(...)):
    """Handle OAuth callback, exchange code for token, store in Token Vault."""
    cfg = OAUTH_CONFIG.get(service)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    user_id = state.split(":")[0] if ":" in state else state
    callback = f"{settings.AUTH0_CALLBACK_URL.rsplit('/callback', 1)[0]}/callback/{service}"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            cfg["token_url"],
            headers={"Accept": "application/json"},
            data={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "redirect_uri": callback,
                "grant_type": "authorization_code",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

    token_data = resp.json()
    access_token = token_data.get("access_token") or token_data.get("authed_user", {}).get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    # Store in Token Vault
    await vault.store_token(
        user_id=user_id,
        service=service,
        access_token=access_token,
        refresh_token=token_data.get("refresh_token"),
        scopes=cfg["scopes"].split(),
    )

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?connected={service}")
