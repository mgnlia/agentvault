# AgentVault — AI Agent with Auth0 Token Vault

> Auth0 "Authorized to Act" Hackathon submission

AgentVault is a **secure, multi-service AI agent** that uses **Auth0 Token Vault** to store and retrieve OAuth tokens on behalf of users — enabling it to take actions across GitHub, Gmail, and Slack with full human oversight and step-up authentication for sensitive operations.

## 🏆 Hackathon Track

**Auth0 "Authorized to Act" — AI Agent with Token Vault ($10K prize)**

## 🎯 What It Does

1. **Connect your services** — GitHub, Gmail, Slack via Auth0 Token Vault (tokens encrypted at rest, never in AgentVault's DB)
2. **Give natural language commands** — "Summarize my unread emails and create GitHub issues for action items"
3. **Agent plans & executes** — Claude AI parses intent, builds a multi-step plan, executes each step using the stored OAuth tokens
4. **Step-up auth for sensitive actions** — Sending email, posting Slack messages, merging PRs all require explicit user re-confirmation
5. **Full audit trail** — Every action logged with user, service, action, timestamp, and result

## 🔐 Security Model

```
User → Auth0 Login → Dashboard
                         ↓
              Connect GitHub/Gmail/Slack
                         ↓
              Auth0 Token Vault stores OAuth tokens
              (encrypted, scoped, per-user)
                         ↓
              User gives natural language command
                         ↓
              Agent retrieves token from Token Vault
              (per-request, never cached in AgentVault)
                         ↓
              Executes action against service API
                         ↓
              Sensitive actions → step-up re-auth required
```

## 🏗 Architecture

```
frontend/          Next.js 14 + Auth0 React SDK
  ├── app/
  │   ├── page.tsx           Landing page
  │   ├── dashboard/         Main agent dashboard
  │   └── demo/              Interactive demo (no auth required)
  └── components/
      ├── CommandBar          Natural language input
      ├── ServiceCard         Connect/disconnect services
      ├── PermissionsPanel    Per-action permission controls
      ├── ActivityFeed        Command history
      └── StepUpModal         Step-up auth confirmation

backend/           FastAPI + Auth0 Token Vault
  └── app/
      ├── main.py
      ├── config.py
      ├── auth/
      │   └── token_vault.py  Auth0 Token Vault client
      ├── routers/
      │   ├── agent.py        POST /api/agent/command
      │   ├── vault.py        GET/POST/DELETE /api/vault/tokens
      │   ├── auth.py         OAuth callback handlers
      │   └── permissions.py  Per-user action permissions
      └── services/
          └── agent_engine.py Claude-powered intent parser + executor
```

## 🚀 Quick Start

### Frontend
```bash
cd frontend
cp .env.example .env.local
# Set AUTH0_* and NEXT_PUBLIC_API_URL
npm install
npm run dev
```

### Backend
```bash
cd backend
cp .env.example .env
# Set AUTH0_DOMAIN, AUTH0_MGMT_TOKEN, ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload
```

## 🔑 Auth0 Token Vault Integration

The key innovation is using **Auth0 Token Vault** as the secure credential store:

```python
# Store token after OAuth callback
await vault.store_token(
    user_id=user_id,
    service="github",
    access_token=access_token,
    scopes=["repo", "read:user"],
)

# Retrieve token per-request (never cached)
token = await vault.get_token(user_id, "github")

# Use token to call service API
headers = {"Authorization": f"Bearer {token}"}
response = await client.get("https://api.github.com/user/repos", headers=headers)
```

This means:
- ✅ Tokens encrypted at rest in Auth0's infrastructure
- ✅ No token storage in AgentVault database
- ✅ Tokens scoped per-user, per-service
- ✅ Revocable at any time from the permissions panel

## 🌐 Live Demo

- **Frontend**: https://agentvault.vercel.app
- **Interactive Demo**: https://agentvault.vercel.app/demo (no login required)
- **API Docs**: https://agentvault-api.railway.app/docs

## 📋 Environment Variables

### Frontend (`.env.local`)
```
NEXT_PUBLIC_AUTH0_DOMAIN=your-tenant.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your_client_id
NEXT_PUBLIC_AUTH0_AUDIENCE=https://agentvault-api
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Backend (`.env`)
```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_MGMT_TOKEN=your_management_api_token  # For Token Vault
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_CLIENT_ID=...
GOOGLE_CLIENT_ID=...
SLACK_CLIENT_ID=...
```

## 🏅 Why AgentVault Wins

1. **Token Vault is the core** — not bolted on. Every API call goes through Token Vault retrieval
2. **Step-up auth** — sensitive actions (send email, post Slack, merge PR) require explicit re-confirmation
3. **Real multi-service orchestration** — not a toy; actually calls GitHub/Gmail/Slack APIs
4. **Permission granularity** — users can enable/disable individual actions per service
5. **Production-ready** — Dockerfile, env validation, error handling, audit trail
