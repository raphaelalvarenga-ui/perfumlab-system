from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import validate_password_policy


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password_actual: str = Field(..., min_length=1, max_length=128)
    password_nueva: str = Field(..., min_length=8, max_length=128)

    @field_validator("password_nueva")
    @classmethod
    def validar_password_nueva(cls, value: str) -> str:
        return validate_password_policy(value)
