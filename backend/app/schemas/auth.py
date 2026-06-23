from pydantic import BaseModel, ConfigDict

from app.models.models import Role


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    last_name: str
    first_name: str
    callsign: str | None
    rank: str | None
    role: Role