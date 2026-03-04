from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    AUTH0_DOMAIN: str = "demo.auth0.com"
    AUTH0_CLIENT_ID: str = "demo_client_id"
    AUTH0_CLIENT_SECRET: str = "demo_client_secret"
    AUTH0_AUDIENCE: str = "https://agentvault-api"
    AUTH0_CALLBACK_URL: str = "http://localhost:8000/api/auth/callback"
    AUTH0_MGMT_TOKEN: str = ""

    ANTHROPIC_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # OAuth client IDs/secrets for each service
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""


settings = Settings()
