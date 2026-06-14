from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User, Profile
from app.schemas import UserRegister, UserLogin
from app.auth import hash_password, verify_password, create_access_token
import re

router = APIRouter(prefix="/auth", tags=["Authentication"])

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

@router.post("/register")
async def register_user(response: Response, email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    hashed = hash_password(password)
    new_user = User(email=email, hashed_password=hashed)
    db.add(new_user)
    await db.flush()  # Populates user ID

    default_slug = slugify(email.split('@')[0])
    
    # Check if slug exists, make unique if necessary
    slug_result = await db.execute(select(Profile).where(Profile.slug == default_slug))
    if slug_result.scalars().first():
        import uuid
        default_slug = f"{default_slug}-{uuid.uuid4().hex[:4]}"

    # Save Profile record corresponding to identity
    new_profile = Profile(
        user_id=new_user.id,
        slug=default_slug,
        full_name=email.split('@')[0].capitalize(),
        email=email
    )
    db.add(new_profile)
    await db.commit()

    token = create_access_token(data={"sub": new_user.email})
    resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, samesite="lax")
    return resp

@router.post("/login")
async def login_user(response: Response, email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password credentials.")

    token = create_access_token(data={"sub": user.email})
    resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, samesite="lax")
    return resp

@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    return resp