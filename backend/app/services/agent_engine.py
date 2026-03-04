"""AgentVault AI Engine — Claude-powered intent parsing and multi-service execution."""
import json
import logging
import httpx
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

SENSITIVE_ACTIONS = {
    "github": ["delete_repo", "delete_branch", "merge_pr", "force_push", "create_repo"],
    "google": ["delete_email", "send_email", "delete_calendar_event"],
    "slack": ["delete_message", "kick_user", "archive_channel", "send_message"],
}

SYSTEM_PROMPT = """You are AgentVault, a secure AI agent that executes tasks across GitHub, Gmail, and Slack on behalf of users.

You have access to these services (only if connected):
- GitHub: list_repos, list_issues, create_issue, list_prs, read_file, search_code, delete_repo (sensitive), merge_pr (sensitive)
- Gmail: list_emails, read_email, send_email (sensitive), search_emails, list_labels, delete_email (sensitive)  
- Slack: list_channels, read_messages, send_message (sensitive), search_messages, list_users, delete_message (sensitive)

Given a user command, respond with a JSON execution plan:
{
  "intent": "brief description of what user wants",
  "steps": [
    {
      "step": 1,
      "service": "github|google|slack",
      "action": "action_name",
      "params": {"key": "value"},
      "description": "human-readable description",
      "requires_step_up": true/false,
      "reason": "why this step is needed"
    }
  ],
  "summary": "what will happen overall"
}

Mark requires_step_up: true for any action in the sensitive list.
Only include services that are in the connected_services list provided.
If a required service is not connected, include a step with service="system", action="connect_service" explaining what's needed.

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""


class AgentEngine:
    """Claude-powered agent that parses intent and executes multi-service plans."""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-5-sonnet-20241022"

    async def parse_intent(self, command: str, connected_services: list[str]) -> list[dict]:
        """Parse natural language command into an execution plan."""
        if not self.api_key:
            # Demo mode: return a mock plan
            return self._demo_plan(command, connected_services)

        user_message = f"""Connected services: {connected_services}
User command: {command}

Create an execution plan."""

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
                timeout=30.0,
            )

        if resp.status_code != 200:
            logger.error(f"Claude API error: {resp.text}")
            return self._demo_plan(command, connected_services)

        content = resp.json()["content"][0]["text"]

        try:
            plan_data = json.loads(content)
            steps = plan_data.get("steps", [])
            # Enrich with sensitive action flags
            for step in steps:
                service = step.get("service", "")
                action = step.get("action", "")
                if action in SENSITIVE_ACTIONS.get(service, []):
                    step["requires_step_up"] = True
            return steps
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Claude response: {content}")
            return self._demo_plan(command, connected_services)

    def _demo_plan(self, command: str, connected_services: list[str]) -> list[dict]:
        """Generate a demo execution plan when API key is not set."""
        cmd_lower = command.lower()
        steps = []

        if "email" in cmd_lower or "gmail" in cmd_lower:
            steps.append({
                "step": 1,
                "service": "google",
                "action": "list_emails",
                "params": {"max_results": 10, "query": "is:unread"},
                "description": "Fetch unread emails from Gmail",
                "requires_step_up": False,
                "reason": "Retrieve emails to process",
            })

        if "issue" in cmd_lower or "github" in cmd_lower:
            steps.append({
                "step": len(steps) + 1,
                "service": "github",
                "action": "create_issue",
                "params": {"repo": "auto-detected", "title": "Action item from email", "body": "..."},
                "description": "Create GitHub issue for action items",
                "requires_step_up": False,
                "reason": "Track action items as GitHub issues",
            })

        if "slack" in cmd_lower or "post" in cmd_lower or "notify" in cmd_lower:
            steps.append({
                "step": len(steps) + 1,
                "service": "slack",
                "action": "send_message",
                "params": {"channel": "#general", "text": "Summary: ..."},
                "description": "Post summary to Slack",
                "requires_step_up": True,
                "reason": "Send notification (sensitive: requires step-up auth)",
            })

        if not steps:
            steps.append({
                "step": 1,
                "service": "system",
                "action": "clarify",
                "params": {},
                "description": f"Processing: {command}",
                "requires_step_up": False,
                "reason": "Command parsed in demo mode",
            })

        return steps

    async def execute_plan(
        self, plan: list[dict], user_id: str, vault: Any
    ) -> list[dict]:
        """Execute all steps in the plan."""
        results = []
        for step in plan:
            result = await self.execute_step(step=step, user_id=user_id, vault=vault)
            results.append(result)
        return results

    async def execute_step(self, step: dict, user_id: str, vault: Any) -> dict:
        """Execute a single plan step."""
        service = step.get("service")
        action = step.get("action")

        if service == "system":
            return {
                "step": step.get("step"),
                "service": service,
                "action": action,
                "status": "info",
                "result": {"message": step.get("description")},
            }

        # Get token from vault
        token = await vault.get_token(user_id=user_id, service=service)
        if not token:
            return {
                "step": step.get("step"),
                "service": service,
                "action": action,
                "status": "error",
                "result": {"error": f"No token for {service}. Please connect {service} first."},
            }

        # Execute the action
        try:
            result = await self._execute_service_action(
                service=service,
                action=action,
                params=step.get("params", {}),
                token=token,
            )
            return {
                "step": step.get("step"),
                "service": service,
                "action": action,
                "status": "success",
                "result": result,
            }
        except Exception as e:
            logger.error(f"Action {service}:{action} failed: {e}")
            return {
                "step": step.get("step"),
                "service": service,
                "action": action,
                "status": "error",
                "result": {"error": str(e)},
            }

    async def _execute_service_action(
        self, service: str, action: str, params: dict, token: str
    ) -> dict:
        """Execute a specific service action with the provided token."""
        if service == "github":
            return await self._github_action(action, params, token)
        elif service == "google":
            return await self._gmail_action(action, params, token)
        elif service == "slack":
            return await self._slack_action(action, params, token)
        else:
            raise ValueError(f"Unknown service: {service}")

    async def _github_action(self, action: str, params: dict, token: str) -> dict:
        """Execute GitHub API actions."""
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        base = "https://api.github.com"

        async with httpx.AsyncClient() as client:
            if action == "list_repos":
                resp = await client.get(f"{base}/user/repos", headers=headers, params={"per_page": 10})
                repos = resp.json()
                return {"repos": [{"name": r["name"], "url": r["html_url"], "stars": r["stargazers_count"]} for r in repos[:10]]}

            elif action == "list_issues":
                repo = params.get("repo", "")
                resp = await client.get(f"{base}/repos/{repo}/issues", headers=headers)
                issues = resp.json()
                return {"issues": [{"number": i["number"], "title": i["title"], "state": i["state"]} for i in issues[:10]]}

            elif action == "create_issue":
                repo = params.get("repo", "")
                resp = await client.post(
                    f"{base}/repos/{repo}/issues",
                    headers=headers,
                    json={"title": params.get("title", ""), "body": params.get("body", "")},
                )
                issue = resp.json()
                return {"issue_number": issue.get("number"), "url": issue.get("html_url")}

            elif action == "list_prs":
                resp = await client.get(f"{base}/user/pulls", headers=headers)
                return {"prs": resp.json()[:5]}

            else:
                return {"message": f"GitHub action '{action}' executed (demo)", "params": params}

    async def _gmail_action(self, action: str, params: dict, token: str) -> dict:
        """Execute Gmail API actions."""
        headers = {"Authorization": f"Bearer {token}"}
        base = "https://gmail.googleapis.com/gmail/v1/users/me"

        async with httpx.AsyncClient() as client:
            if action == "list_emails":
                resp = await client.get(
                    f"{base}/messages",
                    headers=headers,
                    params={"maxResults": params.get("max_results", 10), "q": params.get("query", "is:unread")},
                )
                data = resp.json()
                return {"messages": data.get("messages", [])[:10], "total": data.get("resultSizeEstimate", 0)}

            elif action == "read_email":
                msg_id = params.get("message_id", "")
                resp = await client.get(f"{base}/messages/{msg_id}", headers=headers)
                return resp.json()

            elif action == "search_emails":
                resp = await client.get(
                    f"{base}/messages",
                    headers=headers,
                    params={"q": params.get("query", ""), "maxResults": 20},
                )
                return {"results": resp.json().get("messages", [])}

            else:
                return {"message": f"Gmail action '{action}' executed (demo)", "params": params}

    async def _slack_action(self, action: str, params: dict, token: str) -> dict:
        """Execute Slack API actions."""
        headers = {"Authorization": f"Bearer {token}"}
        base = "https://slack.com/api"

        async with httpx.AsyncClient() as client:
            if action == "list_channels":
                resp = await client.get(f"{base}/conversations.list", headers=headers)
                data = resp.json()
                channels = data.get("channels", [])
                return {"channels": [{"id": c["id"], "name": c["name"]} for c in channels[:20]]}

            elif action == "send_message":
                resp = await client.post(
                    f"{base}/chat.postMessage",
                    headers=headers,
                    json={"channel": params.get("channel", "#general"), "text": params.get("text", "")},
                )
                return resp.json()

            elif action == "read_messages":
                channel = params.get("channel", "")
                resp = await client.get(
                    f"{base}/conversations.history",
                    headers=headers,
                    params={"channel": channel, "limit": 20},
                )
                data = resp.json()
                return {"messages": data.get("messages", [])[:10]}

            else:
                return {"message": f"Slack action '{action}' executed (demo)", "params": params}
