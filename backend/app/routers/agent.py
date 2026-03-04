"""Agent router — natural language command processing."""
import json
import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from app.services.agent_engine import AgentEngine
from app.services.token_vault import TokenVaultService

router = APIRouter()
logger = logging.getLogger(__name__)


class CommandRequest(BaseModel):
    command: str
    user_id: str
    session_id: str | None = None
    confirm_sensitive: bool = False  # User confirmed step-up for sensitive actions


class CommandResponse(BaseModel):
    status: str
    plan: list[dict]
    results: list[dict]
    requires_step_up: bool = False
    step_up_action: str | None = None
    message: str


@router.post("/command")
async def execute_command(body: CommandRequest):
    """Execute a natural language command via the AI agent."""
    engine = AgentEngine()
    vault = TokenVaultService()

    # Get user's connected services
    connections = await vault.list_connections(body.user_id)
    connected_services = [c["service"] for c in connections if c.get("active")]

    # Parse intent and build execution plan
    plan = await engine.parse_intent(
        command=body.command,
        connected_services=connected_services,
    )

    # Check if any steps require step-up auth
    sensitive_steps = [s for s in plan if s.get("requires_step_up")]
    if sensitive_steps and not body.confirm_sensitive:
        return CommandResponse(
            status="requires_step_up",
            plan=plan,
            results=[],
            requires_step_up=True,
            step_up_action=sensitive_steps[0].get("action"),
            message=f"Action '{sensitive_steps[0].get('action')}' requires additional authentication. Please confirm.",
        )

    # Execute the plan
    results = await engine.execute_plan(
        plan=plan,
        user_id=body.user_id,
        vault=vault,
    )

    return CommandResponse(
        status="completed",
        plan=plan,
        results=results,
        message=f"Executed {len(results)} action(s) successfully.",
    )


@router.post("/command/stream")
async def execute_command_stream(body: CommandRequest):
    """Execute command with SSE streaming for real-time updates."""
    engine = AgentEngine()
    vault = TokenVaultService()

    async def event_stream():
        try:
            connections = await vault.list_connections(body.user_id)
            connected_services = [c["service"] for c in connections if c.get("active")]

            yield f"data: {json.dumps({'type': 'status', 'message': 'Parsing intent...'})}\n\n"

            plan = await engine.parse_intent(
                command=body.command,
                connected_services=connected_services,
            )

            yield f"data: {json.dumps({'type': 'plan', 'plan': plan})}\n\n"

            # Check for step-up
            sensitive_steps = [s for s in plan if s.get("requires_step_up")]
            if sensitive_steps and not body.confirm_sensitive:
                yield f"data: {json.dumps({'type': 'step_up', 'action': sensitive_steps[0].get('action'), 'message': 'Step-up authentication required'})}\n\n"
                return

            # Execute each step with streaming updates
            for i, step in enumerate(plan):
                yield f"data: {json.dumps({'type': 'executing', 'step': i+1, 'total': len(plan), 'action': step.get('action'), 'service': step.get('service')})}\n\n"

                result = await engine.execute_step(
                    step=step,
                    user_id=body.user_id,
                    vault=vault,
                )

                yield f"data: {json.dumps({'type': 'result', 'step': i+1, 'result': result})}\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'message': f'All {len(plan)} actions completed'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{user_id}")
async def get_command_history(user_id: str, limit: int = 20):
    """Get command execution history for a user."""
    # In production, this would query a database
    return {
        "user_id": user_id,
        "history": [],
        "total": 0,
    }


@router.get("/capabilities")
async def get_capabilities():
    """List all agent capabilities and supported services."""
    return {
        "services": [
            {
                "id": "github",
                "name": "GitHub",
                "icon": "github",
                "capabilities": [
                    "list_repos", "create_issue", "list_issues",
                    "create_pr", "list_prs", "read_file", "search_code"
                ],
                "sensitive_actions": ["delete_repo", "delete_branch", "merge_pr"],
                "required_scopes": ["repo", "read:user"],
            },
            {
                "id": "google",
                "name": "Gmail",
                "icon": "google",
                "capabilities": [
                    "list_emails", "read_email", "send_email",
                    "search_emails", "list_labels"
                ],
                "sensitive_actions": ["delete_email", "send_email"],
                "required_scopes": ["gmail.readonly", "gmail.send"],
            },
            {
                "id": "slack",
                "name": "Slack",
                "icon": "slack",
                "capabilities": [
                    "list_channels", "read_messages", "send_message",
                    "search_messages", "list_users"
                ],
                "sensitive_actions": ["send_message", "delete_message"],
                "required_scopes": ["channels:read", "chat:write"],
            },
        ],
        "example_commands": [
            "Summarize my unread emails and create GitHub issues for action items",
            "List my open GitHub PRs and post a summary to #dev-updates on Slack",
            "Search my emails for invoices from last month and create a spreadsheet",
            "Find all GitHub issues assigned to me and send a daily digest to Slack",
            "Read the latest Slack messages in #general and draft email replies for anything urgent",
        ],
    }
