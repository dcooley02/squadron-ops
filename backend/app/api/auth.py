from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.models import Person, Role
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.username == payload.username).first()
    if not person or not person.is_active or not verify_password(payload.password, person.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token(
        subject=str(person.id),
        username=person.username,
        role=person.role.value,
    )
    return TokenResponse(access_token=token)


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2-compatible login for tooling."""
    return login(LoginRequest(username=form.username, password=form.password), db)


@router.get("/me", response_model=UserMe)
def me(user: Person = Depends(get_current_user)):
    return user


@router.post("/persons/{person_id}/reset-password", status_code=204, response_class=Response)
def reset_password(
    person_id: int,
    _: Person = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin-only demo reset — sets password to configured demo password."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
    person.password_hash = hash_password(get_settings().demo_password)
    db.commit()
    return None