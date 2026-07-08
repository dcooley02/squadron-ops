from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
    """Require an authenticated user whose role is in ``roles`` (or ADMIN).

    When ``settings.demo_open_rbac`` is true, any authenticated user is allowed
    (portfolio open-ACL mode). ADMIN always passes when RBAC is enforced.
    """

    def checker(user: Person = Depends(get_current_user)) -> Person:
        if get_settings().demo_open_rbac:
            return user
        if user.role == Role.ADMIN:
            return user
        if roles and user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role; requires one of: {allowed}",
            )
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
