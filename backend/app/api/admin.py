from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.setting import Setting
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.schemas.setting import SettingOut, SettingUpdate
from app.core.security import get_current_superuser, hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Settings ──────────────────────────────────────────────────────────────────

@router.get("/settings", response_model=List[SettingOut])
async def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Return all configuration settings"""
    return db.query(Setting).order_by(Setting.key).all()


@router.put("/settings/{key}", response_model=SettingOut)
async def update_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Update a single setting by key"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' nicht gefunden")
    setting.value = body.value
    db.commit()
    db.refresh(setting)
    return setting


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
async def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Return all users"""
    return db.query(User).order_by(User.username).all()


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Create a new user"""
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Benutzername '{body.username}' bereits vergeben")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        is_superuser=body.is_superuser,
        is_active=body.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_superuser),
):
    """Update user data (username, password, flags)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    if body.username is not None:
        # Check uniqueness
        conflict = db.query(User).filter(User.username == body.username, User.id != user_id).first()
        if conflict:
            raise HTTPException(status_code=409, detail=f"Benutzername '{body.username}' bereits vergeben")
        user.username = body.username

    if body.password is not None:
        user.hashed_password = hash_password(body.password)

    if body.is_superuser is not None:
        user.is_superuser = body.is_superuser

    if body.is_active is not None:
        user.is_active = body.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_superuser),
):
    """Delete a user (admin cannot be deleted)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Der Admin-Benutzer kann nicht gelöscht werden")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="Sie können sich nicht selbst löschen")

    db.delete(user)
    db.commit()
