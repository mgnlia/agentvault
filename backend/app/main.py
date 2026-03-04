"""AgentVault FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import agent, vault, auth, permissions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AgentVault starting up")
    logger.info(f"Auth0 domain: {settings.AUTH0_DOMAIN}")
    logger.info(f"Demo mode: {settings.AUTH0_MGMT_TOKEN == ''}")
    yield
    logger.info("AgentVault shutting down")


app = FastAPI(
    title="AgentVault API",
    description="Secure AI agent with Auth0 Token Vault — executes tasks across GitHub, Gmail, Slack",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(vault.router, prefix="/api/vault", tags=["vault"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])


@app.get("/")
async def root():
    return {
        "service": "AgentVault API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "auth0_domain": settings.AUTH0_DOMAIN}
