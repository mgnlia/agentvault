"""Auth0 Token Vault service — secure OAuth token storage and retrieval."""
import httpx
import logging
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory token store for demo (Token Vault replaces this in production)
_token_store: dict[str, dict] = {}


class TokenVaultService:
    """
    Auth0 Token Vault integration.

    Token Vault stores third-party OAuth tokens encrypted at rest in Auth0.
    Tokens are retrieved per-user via the Auth0 Management API.

    In production: uses Auth0's /api/v2/users/{user_id}/credentials endpoint.
    In demo mode: uses in-memory store with same interface.
    """

    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.mgmt_token = settings.AUTH0_MGMT_TOKEN
        self.base_url = f"https://{self.domain}/api/v2"
        self.demo_mode = not bool(settings.AUTH0_MGMT_TOKEN)

    async def _get_mgmt_headers(self) -> dict:
        """Get Auth0 Management API headers."""
        return {
            "Authorization": f"Bearer {self.mgmt_token}",
            "Content-Type": "application/json",
        }

    async def store_token(
        self,
        user_id: str,
        service: str,
        access_token: str,
        refresh_token: str | None = None,
        scopes: list[str] | None = None,
    ) -> dict:
        """
        Store OAuth token in Auth0 Token Vault.

        Uses Auth0 Management API: POST /api/v2/users/{user_id}/credentials
        This stores tokens encrypted at rest, accessible only via Auth0.
        """
        if self.demo_mode:
            # Demo mode: store in memory
            key = f"{user_id}:{service}"
            _token_store[key] = {
                "service": service,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "scopes": scopes or [],
                "active": True,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "last_used": None,
            }
            logger.info(f"[Demo] Stored token for {user_id}:{service}")
            return {"credential_id": f"demo_{key}", "service": service}

        # Production: Auth0 Token Vault API
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/users/{user_id}/credentials",
                headers=await self._get_mgmt_headers(),
                json={
                    "credential_type": "oauth2_access_token",
                    "name": f"agentvault_{service}",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "scopes": scopes or [],
                    "metadata": {"service": service, "app": "agentvault"},
                },
            )

        if resp.status_code not in (200, 201):
            logger.error(f"Token Vault store failed: {resp.text}")
            raise Exception(f"Failed to store token: {resp.text}")

        return resp.json()

    async def get_token(self, user_id: str, service: str) -> str | None:
        """
        Retrieve OAuth token from Auth0 Token Vault.

        Auth0 handles token refresh automatically when refresh_token is stored.
        """
        if self.demo_mode:
            key = f"{user_id}:{service}"
            entry = _token_store.get(key)
            if entry:
                _token_store[key]["last_used"] = datetime.now(timezone.utc).isoformat()
                return entry.get("access_token")
            return None

        # Production: retrieve from Token Vault
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/users/{user_id}/credentials",
                headers=await self._get_mgmt_headers(),
                params={"name": f"agentvault_{service}"},
            )

        if resp.status_code != 200:
            return None

        creds = resp.json()
        if not creds:
            return None

        # Token Vault returns the access token directly (handles refresh)
        return creds[0].get("access_token")

    async def revoke_token(self, user_id: str, service: str) -> None:
        """Revoke and delete a token from Token Vault."""
        if self.demo_mode:
            key = f"{user_id}:{service}"
            _token_store.pop(key, None)
            logger.info(f"[Demo] Revoked token for {user_id}:{service}")
            return

        # Production: delete from Token Vault
        async with httpx.AsyncClient() as client:
            # First get credential ID
            resp = await client.get(
                f"{self.base_url}/users/{user_id}/credentials",
                headers=await self._get_mgmt_headers(),
                params={"name": f"agentvault_{service}"},
            )
            if resp.status_code == 200 and resp.json():
                cred_id = resp.json()[0]["id"]
                await client.delete(
                    f"{self.base_url}/users/{user_id}/credentials/{cred_id}",
                    headers=await self._get_mgmt_headers(),
                )

    async def list_connections(self, user_id: str) -> list[dict]:
        """List all connected services for a user."""
        if self.demo_mode:
            connections = []
            for key, data in _token_store.items():
                if key.startswith(f"{user_id}:"):
                    connections.append({
                        "service": data["service"],
                        "active": data["active"],
                        "scopes": data["scopes"],
                        "connected_at": data["connected_at"],
                        "last_used": data["last_used"],
                    })
            return connections

        # Production: list from Token Vault
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/users/{user_id}/credentials",
                headers=await self._get_mgmt_headers(),
            )

        if resp.status_code != 200:
            return []

        creds = resp.json()
        return [
            {
                "service": c.get("metadata", {}).get("service", "unknown"),
                "active": True,
                "scopes": c.get("scopes", []),
                "connected_at": c.get("created_at"),
                "last_used": c.get("updated_at"),
                "credential_id": c.get("id"),
            }
            for c in creds
            if c.get("metadata", {}).get("app") == "agentvault"
        ]

    async def get_token_status(self, user_id: str, service: str) -> dict:
        """Check token status for a service."""
        if self.demo_mode:
            key = f"{user_id}:{service}"
            entry = _token_store.get(key)
            if entry:
                return {
                    "service": service,
                    "connected": True,
                    "active": entry["active"],
                    "scopes": entry["scopes"],
                    "last_used": entry["last_used"],
                }
            return {"service": service, "connected": False}

        token = await self.get_token(user_id, service)
        return {
            "service": service,
            "connected": token is not None,
            "active": token is not None,
        }
