"""AgentVault core engine — parses natural language commands into executable plans."""
import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SENSITIVE_ACTIONS = [
    "send_email", "delete_email",
    "send_message", "delete_message",
    "delete_repo", "delete_branch", "merge_pr", "force_push",
    "create_webhook", "delete_webhook",
]

# Keyword → service+action mapping for demo/fallback parsing
INTENT_MAP = [
    (["email", "gmail", "inbox", "unread", "mail"], "google", "list_emails"),
    (["read email", "open email"], "google", "read_email"),
    (["send email", "reply", "compose"], "google", "send_email"),
    (["github", "repo", "repository", "repos"], "github", "list_repos"),
    (["issue", "issues"], "github", "list_issues"),
    (["pr", "pull request", "pull requests", "prs"], "github", "list_prs"),
    (["create issue"], "github", "create_issue"),
    (["slack", "channel", "message", "post"], "slack", "send_message"),
    (["slack channel", "channels"], "slack", "list_channels"),
]


class AgentEngine:
    def __init__(self):
        self.has_anthropic = bool(settings.ANTHROPIC_API_KEY)

    async def parse_intent(self, command: str, connected_services: list[str]) -> list[dict]:
        """Parse a natural language command into a step-by-step execution plan."""
        if self.has_anthropic:
            try:
                return await self._parse_with_claude(command, connected_services)
            except Exception as e:
                logger.warning(f"Claude parsing failed, falling back: {e}")
        return self._parse_with_rules(command, connected_services)

    async def execute_plan(self, plan: list[dict], user_id: str, vault: Any) -> list[dict]:
        """Execute each step in the plan, retrieving tokens from Token Vault."""
        results = []
        for step in plan:
            service = step.get("service", "")
            action = step.get("action", "")

            # Retrieve token from Auth0 Token Vault
            token = await vault.get_token(user_id, service)
            if not token:
                results.append({
                    "step": step.get("step", 0),
                    "service": service,
                    "action": action,
                    "status": "error",
                    "error": f"No token found for {service}. Please connect the service first.",
                })
                continue

            # Execute the action
            result = await self._execute_action(service, action, token, step.get("params", {}))
            results.append({
                "step": step.get("step", 0),
                "service": service,
                "action": action,
                **result,
            })

        return results

    async def _parse_with_claude(self, command: str, connected_services: list[str]) -> list[dict]:
        """Use Claude API to parse command into structured plan."""
        system_prompt = """You are AgentVault's planning engine. Parse user commands into execution plans.
Return ONLY valid JSON — an array of step objects. Each step must have:
- step: integer (1-based)
- service: string (github|google|slack)
- action: string (e.g. list_emails, create_issue, send_message)
- description: string (human-readable description)
- requires_step_up: boolean (true for sensitive/destructive actions)
- params: object (optional parameters)

Sensitive actions requiring step_up=true: send_email, delete_email, send_message, delete_message, delete_repo, merge_pr, force_push.
Only include services from the connected list. If no relevant service is connected, include the step anyway with a note."""

        user_prompt = f"""Command: "{command}"
Connected services: {connected_services}
Return the execution plan as JSON array only, no markdown."""

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()

        # Strip markdown fences if present
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        plan = json.loads(content)
        # Ensure requires_step_up is set correctly
        for step in plan:
            if step.get("action") in SENSITIVE_ACTIONS:
                step["requires_step_up"] = True
        return plan

    def _parse_with_rules(self, command: str, connected_services: list[str]) -> list[dict]:
        """Rule-based fallback parser."""
        cmd_lower = command.lower()
        steps = []
        step_num = 1

        # Detect services/actions mentioned
        seen = set()
        for keywords, service, action in INTENT_MAP:
            if service not in connected_services and connected_services:
                continue
            if any(kw in cmd_lower for kw in keywords):
                key = f"{service}:{action}"
                if key not in seen:
                    seen.add(key)
                    steps.append({
                        "step": step_num,
                        "service": service,
                        "action": action,
                        "description": f"{action.replace('_', ' ').title()} via {service}",
                        "requires_step_up": action in SENSITIVE_ACTIONS,
                        "params": {},
                    })
                    step_num += 1

        if not steps:
            # Generic fallback
            for svc in (connected_services or ["github", "google", "slack"]):
                steps.append({
                    "step": step_num,
                    "service": svc,
                    "action": "list_" + ("emails" if svc == "google" else "repos" if svc == "github" else "channels"),
                    "description": f"Fetch data from {svc}",
                    "requires_step_up": False,
                    "params": {},
                })
                step_num += 1
                if step_num > 3:
                    break

        return steps

    async def _execute_action(self, service: str, action: str, token: str, params: dict) -> dict:
        """Execute a single action against the service API."""
        try:
            if service == "github":
                return await self._github_action(action, token, params)
            elif service == "google":
                return await self._google_action(action, token, params)
            elif service == "slack":
                return await self._slack_action(action, token, params)
            else:
                return {"status": "error", "error": f"Unknown service: {service}"}
        except Exception as e:
            logger.error(f"Action {service}/{action} failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _github_action(self, action: str, token: str, params: dict) -> dict:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            if action == "list_repos":
                r = await client.get("https://api.github.com/user/repos?per_page=10&sort=updated", headers=headers)
                r.raise_for_status()
                repos = r.json()
                return {"status": "success", "count": len(repos), "data": [{"name": x["full_name"], "stars": x["stargazers_count"]} for x in repos[:5]]}
            elif action == "list_issues":
                r = await client.get("https://api.github.com/issues?per_page=10&state=open", headers=headers)
                r.raise_for_status()
                issues = r.json()
                return {"status": "success", "count": len(issues), "data": [{"title": x["title"], "repo": x["repository"]["full_name"]} for x in issues[:5]]}
            elif action == "list_prs":
                r = await client.get("https://api.github.com/search/issues?q=is:pr+is:open+author:@me&per_page=10", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"status": "success", "count": data.get("total_count", 0), "data": [{"title": x["title"]} for x in data.get("items", [])[:5]]}
            elif action == "create_issue":
                repo = params.get("repo", "")
                title = params.get("title", "Action item from AgentVault")
                body = params.get("body", "Created automatically by AgentVault agent.")
                if not repo:
                    return {"status": "skipped", "reason": "No repo specified"}
                r = await client.post(f"https://api.github.com/repos/{repo}/issues", headers=headers, json={"title": title, "body": body})
                r.raise_for_status()
                issue = r.json()
                return {"status": "success", "issue_url": issue["html_url"], "number": issue["number"]}
            else:
                return {"status": "demo", "action": action, "message": f"Demo: {action} executed successfully"}

    async def _google_action(self, action: str, token: str, params: dict) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            if action == "list_emails":
                r = await client.get("https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10&q=is:unread", headers=headers)
                r.raise_for_status()
                data = r.json()
                return {"status": "success", "count": data.get("resultSizeEstimate", 0), "message_ids": [m["id"] for m in data.get("messages", [])[:5]]}
            elif action == "send_email":
                return {"status": "demo", "message": "Demo: email send simulated (step-up required in production)"}
            else:
                return {"status": "demo", "action": action, "message": f"Demo: {action} executed"}

    async def _slack_action(self, action: str, token: str, params: dict) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            if action == "list_channels":
                r = await client.get("https://slack.com/api/conversations.list?limit=10", headers=headers)
                r.raise_for_status()
                data = r.json()
                channels = data.get("channels", [])
                return {"status": "success", "count": len(channels), "data": [{"name": c["name"]} for c in channels[:5]]}
            elif action == "send_message":
                channel = params.get("channel", "#general")
                text = params.get("text", "Message from AgentVault")
                r = await client.post("https://slack.com/api/chat.postMessage", headers=headers, json={"channel": channel, "text": text})
                r.raise_for_status()
                data = r.json()
                return {"status": "success" if data.get("ok") else "error", "ts": data.get("ts")}
            else:
                return {"status": "demo", "action": action, "message": f"Demo: {action} executed"}
