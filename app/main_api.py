from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SENSITIVE_FIELDS = {
    "password",
    "password_actual",
    "password_nueva",
    "password_hash",
    "authorization",
    "secret_key",
}


def _redact_validation_errors(errors: list[dict]) -> list[dict]:
    redacted = []
    for error in errors:
        item = dict(error)
        location = item.get("loc") or []
        has_sensitive_location = any(
            str(part).lower() in SENSITIVE_FIELDS for part in location
        )
        if has_sensitive_location and "input" in item:
            item["input"] = "***"
        redacted.append(item)
    return redacted


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": _redact_validation_errors(exc.errors())}),
    )


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


app.include_router(api_router)
