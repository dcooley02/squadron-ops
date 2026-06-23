from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.models import Person, Role


def _user_id_from_request(request: Request) -> int | None:
    return getattr(request.state, "user_id", None)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Person:
    user_id = _user_id_from_request(request)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    person = db.query(Person).filter(Person.id == user_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return person


def require_roles(*roles: Role):
    """Authenticate only — role checks deferred until per-route permissions ship."""

    def checker(user: Person = Depends(get_current_user)) -> Person:
        return user

    return checker


def actor_from_request(request: Request) -> str | None:
    return getattr(request.state, "username", None)


def bearer_user_id(authorization: str | None) -> int | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = decode_access_token(token)
        return int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        return None