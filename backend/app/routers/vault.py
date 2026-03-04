"""Token Vault management router."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.auth.token_vault import vault

logger = logging.getLogger(__name__)
router = APIRouter()


class StoreTokenRequest(BaseModel):
    user_id: str
    service: str
    access_token: str
    refresh_token: Optional[str] = None
    scopes: list[str] = []


@router.post("/tokens")
async def store_token(req: StoreTokenRequest):
    """Store an OAuth token in Auth0 Token Vault."""
    ok = await vault.store_token(
        user_id=req.user_id,
        service=req.service,
        access_token=req.access_token,
        refresh_token=req.refresh_token,
        scopes=req.scopes,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to store token in vault")
    return {"status": "stored", "service": req.service}


@router.get("/tokens/{user_id}")
async def list_tokens(user_id: str):
    """List all service connections for a user."""
    connections = await vault.list_connections(user_id)
    return {"user_id": user_id, "connections": connections}


@router.delete("/tokens/{user_id}/{service}")
async def revoke_token(user_id: str, service: str):
    """Revoke a stored token."""
    ok = await vault.revoke_token(user_id=user_id, service=service)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No token found for {service}")
    return {"status": "revoked", "service": service}
