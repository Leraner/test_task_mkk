from src.shared.web.api_settings import APISettings


def get_cors_middleware_kwargs(settings: APISettings) -> dict:
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "HEAD"],
        "allow_headers": ["*"],
    }
