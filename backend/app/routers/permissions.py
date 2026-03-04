"""Permission management — granular access control dashboard."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.token_vault import TokenVaultService

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdatePermissionRequest(BaseModel):
    user_id: str
    service: str
    permission: str
    enabled: bool


class PermissionPolicy(BaseModel):
    user_id: str
    service: str
    allowed_actions: list[str]
    denied_actions: list[str]
    require_step_up: list[str]


# In-memory policy store (use DB in production)
_permission_policies: dict[str, dict] = {}

SENSITIVE_ACTIONS = {
    "github": ["delete_repo", "delete_branch", "merge_pr", "force_push"],
    "google": ["delete_email", "send_email", "delete_calendar_event"],
    "slack": ["delete_message", "kick_user", "archive_channel"],
}

DEFAULT_ALLOWED = {
    "github": ["list_repos", "list_issues", "list_prs", "read_file", "search_code"],
    "google": ["list_emails", "read_email", "search_emails", "list_labels"],
    "slack": ["list_channels", "read_messages", "search_messages", "list_users"],
}


@router.get("/{user_id}")
async def get_permissions(user_id: str):
    """Get all permission policies for a user."""
    vault = TokenVaultService()
    connections = await vault.list_connections(user_id)

    permissions = []
    for conn in connections:
        service = conn["service"]
        policy = _permission_policies.get(f"{user_id}:{service}", {})

        permissions.append({
            "service": service,
            "active": conn.get("active", False),
            "connected_at": conn.get("connected_at"),
            "scopes": conn.get("scopes", []),
            "allowed_actions": policy.get("allowed_actions", DEFAULT_ALLOWED.get(service, [])),
            "denied_actions": policy.get("denied_actions", []),
            "require_step_up": policy.get("require_step_up", SENSITIVE_ACTIONS.get(service, [])),
            "last_used": conn.get("last_used"),
        })

    return {"user_id": user_id, "permissions": permissions}


@router.put("/{user_id}/{service}")
async def update_permission(user_id: str, service: str, body: UpdatePermissionRequest):
    """Update a specific permission for a service."""
    key = f"{user_id}:{service}"
    if key not in _permission_policies:
        _permission_policies[key] = {
            "allowed_actions": list(DEFAULT_ALLOWED.get(service, [])),
            "denied_actions": [],
            "require_step_up": list(SENSITIVE_ACTIONS.get(service, [])),
        }

    policy = _permission_policies[key]

    if body.enabled:
        if body.permission in policy["denied_actions"]:
            policy["denied_actions"].remove(body.permission)
        if body.permission not in policy["allowed_actions"]:
            policy["allowed_actions"].append(body.permission)
    else:
        if body.permission in policy["allowed_actions"]:
            policy["allowed_actions"].remove(body.permission)
        if body.permission not in policy["denied_actions"]:
            policy["denied_actions"].append(body.permission)

    return {"status": "updated", "service": service, "permission": body.permission, "enabled": body.enabled}


@router.post("/{user_id}/{service}/step-up")
async def toggle_step_up(user_id: str, service: str, action: str, required: bool):
    """Toggle step-up authentication requirement for an action."""
    key = f"{user_id}:{service}"
    if key not in _permission_policies:
        _permission_policies[key] = {
            "allowed_actions": list(DEFAULT_ALLOWED.get(service, [])),
            "denied_actions": [],
            "require_step_up": list(SENSITIVE_ACTIONS.get(service, [])),
        }

    policy = _permission_policies[key]

    if required and action not in policy["require_step_up"]:
        policy["require_step_up"].append(action)
    elif not required and action in policy["require_step_up"]:
        policy["require_step_up"].remove(action)

    return {"status": "updated", "action": action, "step_up_required": required}


@router.get("/audit/{user_id}")
async def get_audit_log(user_id: str, limit: int = 50):
    """Get audit log of all agent actions for a user."""
    # In production, query from database
    return {
        "user_id": user_id,
        "audit_log": [],
        "total": 0,
    }
