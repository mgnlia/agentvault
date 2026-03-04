"""Auth0 Token Vault integration — store and retrieve OAuth tokens securely."""
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging

from app.config import settings
from app.services.token_vault import TokenVaultService

router = APIRouter()
logger = logging.getLogger(__name__)


class StoreTokenRequest(BaseModel):
    user_id: str
    service: str
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    scopes: list[str] = []


class RevokeTokenRequest(BaseModel):
    user_id: str
    service: str


@router.get("/tokens/{user_id}")
async def list_user_tokens(user_id: str, request: Request):
    """List all services the user has connected via Token Vault."""
    vault = TokenVaultService()
    try:
        connections = await vault.list_connections(user_id)
        return {"user_id": user_id, "connections": connections}
    except Exception as e:
        logger.error(f"Failed to list tokens for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens")
async def store_token(body: StoreTokenRequest):
    """Store an OAuth token in Auth0 Token Vault."""
    vault = TokenVaultService()
    try:
        result = await vault.store_token(
            user_id=body.user_id,
            service=body.service,
            access_token=body.access_token,
            refresh_token=body.refresh_token,
            scopes=body.scopes,
        )
        return {"status": "stored", "service": body.service, "result": result}
    except Exception as e:
        logger.error(f"Failed to store token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tokens/{user_id}/{service}")
async def revoke_token(user_id: str, service: str):
    """Revoke a service token from Token Vault."""
    vault = TokenVaultService()
    try:
        await vault.revoke_token(user_id=user_id, service=service)
        return {"status": "revoked", "service": service}
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/{user_id}/{service}/status")
async def token_status(user_id: str, service: str):
    """Check if a service token exists and is valid."""
    vault = TokenVaultService()
    try:
        status = await vault.get_token_status(user_id=user_id, service=service)
        return status
    except Exception as e:
        logger.error(f"Failed to get token status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
