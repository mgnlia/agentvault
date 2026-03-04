"""Permission management router — per-user, per-service action controls."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory permission store (production: use DB)
_permissions: dict[str, dict] = {}
_step_up_config: dict[str, set] = {}


class PermissionUpdate(BaseModel):
    user_id: str
    service: str
    permission: str
    enabled: bool


@router.get("/{user_id}/{service}")
async def get_permissions(user_id: str, service: str):
    """Get permission settings for a user/service."""
    key = f"{user_id}:{service}"
    perms = _permissions.get(key, {})
    step_ups = list(_step_up_config.get(key, set()))
    return {"user_id": user_id, "service": service, "permissions": perms, "step_up_required": step_ups}


@router.put("/{user_id}/{service}")
async def update_permission(user_id: str, service: str, req: PermissionUpdate):
    """Enable or disable a specific action for a user/service."""
    key = f"{user_id}:{service}"
    if key not in _permissions:
        _permissions[key] = {}
    _permissions[key][req.permission] = req.enabled
    return {"status": "updated", "permission": req.permission, "enabled": req.enabled}


@router.post("/{user_id}/{service}/step-up")
async def configure_step_up(user_id: str, service: str, action: str, required: bool):
    """Configure whether a specific action requires step-up authentication."""
    key = f"{user_id}:{service}"
    if key not in _step_up_config:
        _step_up_config[key] = set()
    if required:
        _step_up_config[key].add(action)
    else:
        _step_up_config[key].discard(action)
    return {"status": "updated", "action": action, "step_up_required": required}


def is_permitted(user_id: str, service: str, action: str) -> bool:
    """Check if an action is permitted for a user/service (default: True)."""
    key = f"{user_id}:{service}"
    perms = _permissions.get(key, {})
    return perms.get(action, True)


def requires_step_up(user_id: str, service: str, action: str) -> bool:
    """Check if an action requires step-up auth for this user."""
    key = f"{user_id}:{service}"
    return action in _step_up_config.get(key, set())
