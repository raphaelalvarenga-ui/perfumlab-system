from fastapi import HTTPException

from app.services.exceptions import ServiceError


def service_error_to_http(error: ServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)
