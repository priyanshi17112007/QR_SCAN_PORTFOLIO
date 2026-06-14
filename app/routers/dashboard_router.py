from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Profile
from app.auth import decode_access_token

router = APIRouter(tags=["UI Rendering"])

async def get_current_user_from_cookie(request: Request, db: AsyncSession):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None
    token_str = token.split(" ")[1]
    payload = decode_access_token(token_str)
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    result = await db.execute(
        select(User)
        .where(User.email == email)
        .options(
            selectinload(User.profile).selectinload(Profile.projects),
            selectinload(User.profile).selectinload(Profile.internships),
            selectinload(User.profile).selectinload(Profile.certificate_files)
        )
    )
    return result.scalars().first()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(request, "login.html")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return request.app.state.templates.TemplateResponse(request, "register.html")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Defensive programming: create a profile on the fly if missing
    if not user.profile:
        import re
        default_slug = re.sub(r'[^a-z0-9]', '', user.email.split('@')[0].lower())
        new_profile = Profile(
            user_id=user.id,
            slug=default_slug,
            full_name=user.email.split('@')[0].capitalize(),
            email=user.email
        )
        db.add(new_profile)
        await db.commit()
        # Re-fetch user details
        result = await db.execute(
            select(User)
            .where(User.id == user.id)
            .options(
                selectinload(User.profile).selectinload(Profile.projects),
                selectinload(User.profile).selectinload(Profile.internships),
                selectinload(User.profile).selectinload(Profile.certificate_files)
            )
        )
        user = result.scalars().first()

    return request.app.state.templates.TemplateResponse(
        request,
        "dashboard.html", 
        {
            "user": user, 
            "profile": user.profile, 
            "projects": user.profile.projects,
            "internships": user.profile.internships,
            "certificates": user.profile.certificate_files
        }
    )

@router.get("/profile/{slug}", response_class=HTMLResponse)
async def public_profile_page(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Profile)
        .where(Profile.slug == slug)
        .options(
            selectinload(Profile.projects),
            selectinload(Profile.internships),
            selectinload(Profile.certificate_files)
        )
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return request.app.state.templates.TemplateResponse(request, "profile_view.html", {"profile": profile})