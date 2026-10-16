from dataclasses import dataclass
import os


def _env_origins(value: str | None) -> tuple[str, ...]:
    """Read a comma-separated list of origins, keeping local development safe."""
    if not value:
        return ("http://127.0.0.1:5173", "http://localhost:5173")
    origins = tuple(origin.strip().rstrip("/") for origin in value.split(",") if origin.strip())
    return origins or ("http://127.0.0.1:5173", "http://localhost:5173")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Paywise API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("PAYWISE_APP_NAME", cls.app_name),
            app_version=os.getenv("PAYWISE_APP_VERSION", cls.app_version),
            api_v1_prefix=os.getenv("PAYWISE_API_PREFIX", cls.api_v1_prefix),
            cors_origins=_env_origins(os.getenv("PAYWISE_CORS_ORIGINS")),
        )


settings = Settings.from_env()
