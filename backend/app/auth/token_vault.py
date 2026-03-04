"""Auth0 Token Vault integration — secure OAuth token storage and retrieval."""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory store for demo mode (replaces Token Vault when Auth0 isn't configured)
_demo_vault: dict[str, dict] = {}


class TokenVault:
    """
    Wraps Auth0 Token Vault API for secure OAuth token storage.
    Falls back to in-memory demo store when Auth0 isn't configured.
    """

    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.mgmt_token = settings.AUTH0_MGMT_TOKEN
        self.demo_mode = not self.mgmt_token or self.domain == "demo.auth0.com"
        if self.demo_mode:
            logger.warning("TokenVault running in DEMO MODE — tokens stored in memory only")

    # ─── Public API ───────────────────────────────────────────────────────────

    async def store_token(
        self,
        user_id: str,
        service: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        scopes: list[str] = [],
    ) -> bool:
        """Store an OAuth token for a user/service pair."""
        if self.demo_mode:
            return self._demo_store(user_id, service, access_token, refresh_token, scopes)
        return await self._vault_store(user_id, service, access_token, refresh_token, scopes)

    async def get_token(self, user_id: str, service: str) -> Optional[str]:
        """Retrieve a stored OAuth token."""
        if self.demo_mode:
            return self._demo_get(user_id, service)
        return await self._vault_get(user_id, service)

    async def revoke_token(self, user_id: str, service: str) -> bool:
        """Revoke/delete a stored token."""
        if self.demo_mode:
            return self._demo_revoke(user_id, service)
        return await self._vault_revoke(user_id, service)

    async def list_connections(self, user_id: str) -> list[dict]:
        """List all service connections for a user."""
        if self.demo_mode:
            return self._demo_list(user_id)
        return await self._vault_list(user_id)

    # ─── Auth0 Token Vault API ────────────────────────────────────────────────

    async def _vault_store(
        self, user_id: str, service: str, access_token: str,
        refresh_token: Optional[str], scopes: list[str],
    ) -> bool:
        """Store token via Auth0 Token Vault API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://{self.domain}/api/v2/users/{user_id}/credentials",
                headers={
                    "Authorization": f"Bearer {self.mgmt_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "credential_type": "access_token",
                    "name": f"agentvault_{service}",
                    "access_token": access_token,
                    **({"refresh_token": refresh_token} if refresh_token else {}),
                    "scopes": scopes,
                },
            )
        if resp.status_code in (200, 201):
            logger.info(f"Token stored in Auth0 Vault: {user_id}/{service}")
            return True
        logger.error(f"Token Vault store failed: {resp.status_code} {resp.text}")
        return False

    async def _vault_get(self, user_id: str, service: str) -> Optional[str]:
        """Retrieve token via Auth0 Token Vault API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}/credentials",
                headers={"Authorization": f"Bearer {self.mgmt_token}"},
            )
        if resp.status_code != 200:
            return None
        creds = resp.json()
        for cred in creds:
            if cred.get("name") == f"agentvault_{service}":
                return cred.get("access_token")
        return None

    async def _vault_revoke(self, user_id: str, service: str) -> bool:
        """Revoke token via Auth0 Token Vault API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}/credentials",
                headers={"Authorization": f"Bearer {self.mgmt_token}"},
            )
            if resp.status_code != 200:
                return False
            creds = resp.json()
            for cred in creds:
                if cred.get("name") == f"agentvault_{service}":
                    del_resp = await client.delete(
                        f"https://{self.domain}/api/v2/users/{user_id}/credentials/{cred['id']}",
                        headers={"Authorization": f"Bearer {self.mgmt_token}"},
                    )
                    return del_resp.status_code == 204
        return False

    async def _vault_list(self, user_id: str) -> list[dict]:
        """List credentials via Auth0 Token Vault API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}/credentials",
                headers={"Authorization": f"Bearer {self.mgmt_token}"},
            )
        if resp.status_code != 200:
            return []
        creds = resp.json()
        return [
            {
                "service": c["name"].replace("agentvault_", ""),
                "active": True,
                "scopes": c.get("scopes", []),
                "connected_at": c.get("created_at"),
                "last_used": c.get("last_used_at"),
            }
            for c in creds
            if c.get("name", "").startswith("agentvault_")
        ]

    # ─── Demo Mode (in-memory) ────────────────────────────────────────────────

    def _demo_store(
        self, user_id: str, service: str, access_token: str,
        refresh_token: Optional[str], scopes: list[str],
    ) -> bool:
        key = f"{user_id}:{service}"
        _demo_vault[key] = {
            "service": service,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scopes": scopes,
            "active": True,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_used": None,
        }
        return True

    def _demo_get(self, user_id: str, service: str) -> Optional[str]:
        key = f"{user_id}:{service}"
        entry = _demo_vault.get(key)
        if entry:
            entry["last_used"] = datetime.now(timezone.utc).isoformat()
            return entry["access_token"]
        return None

    def _demo_revoke(self, user_id: str, service: str) -> bool:
        key = f"{user_id}:{service}"
        if key in _demo_vault:
            del _demo_vault[key]
            return True
        return False

    def _demo_list(self, user_id: str) -> list[dict]:
        prefix = f"{user_id}:"
        return [
            {
                "service": v["service"],
                "active": v["active"],
                "scopes": v["scopes"],
                "connected_at": v["connected_at"],
                "last_used": v["last_used"],
            }
            for k, v in _demo_vault.items()
            if k.startswith(prefix)
        ]


# Singleton
vault = TokenVault()
