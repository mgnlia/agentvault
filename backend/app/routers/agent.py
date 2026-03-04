"""Agent command execution router."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.token_vault import vault
from app.services.agent_engine import AgentEngine, SENSITIVE_ACTIONS

logger = logging.getLogger(__name__)
router = APIRouter()
engine = AgentEngine()


class CommandRequest(BaseModel):
    command: str
    user_id: str
    confirm_sensitive: bool = False


class CommandResponse(BaseModel):
    status: str
    message: str
    plan: list[dict]
    results: list[dict]
    requires_step_up: bool = False
    step_up_action: Optional[str] = None


@router.post("/command", response_model=CommandResponse)
async def run_command(req: CommandRequest):
    """Parse and execute a natural language command."""
    logger.info(f"Command from {req.user_id}: {req.command[:80]}")

    # Get connected services
    connections = await vault.list_connections(req.user_id)
    connected_services = [c["service"] for c in connections if c["active"]]

    # Parse intent into plan
    plan = await engine.parse_intent(req.command, connected_services)

    # Check for sensitive steps requiring step-up
    sensitive_steps = [s for s in plan if s.get("requires_step_up")]
    if sensitive_steps and not req.confirm_sensitive:
        return CommandResponse(
            status="step_up_required",
            message="One or more steps require step-up authentication before execution.",
            plan=plan,
            results=[],
            requires_step_up=True,
            step_up_action=sensitive_steps[0].get("action", "sensitive_action"),
        )

    # Execute plan
    results = await engine.execute_plan(plan=plan, user_id=req.user_id, vault=vault)

    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = sum(1 for r in results if r.get("status") == "error")

    return CommandResponse(
        status="completed",
        message=f"Executed {len(results)} steps: {success_count} succeeded, {error_count} failed.",
        plan=plan,
        results=results,
        requires_step_up=False,
    )


@router.get("/sensitive-actions")
async def get_sensitive_actions():
    """Return the list of actions that require step-up auth."""
    return {"sensitive_actions": SENSITIVE_ACTIONS}
