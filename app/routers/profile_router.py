import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User, Profile, Project, Internship, CertificateFile
from app.routers.dashboard_router import get_current_user_from_cookie
from app.services.ai_service import ai_service
from app.services.qr_service import qr_service
from app.config import settings

router = APIRouter(prefix="/api/profile", tags=["Profile Actions"])

@router.post("/update")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    college: str = Form(""),
    degree: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    location: str = Form(""),
    academic_year: str = Form(""),
    sgpa_percentage: str = Form(""),
    linkedin_url: str = Form(""),
    github_url: str = Form(""),
    portfolio_url: str = Form(""),
    about_me: str = Form(""),
    tagline: str = Form(""),
    skills: str = Form(""),
    certifications: str = Form(""),
    achievements: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    profile = user.profile
    profile.full_name = full_name
    profile.college = college
    profile.degree = degree
    profile.email = email
    profile.phone = phone
    profile.location = location
    profile.academic_year = academic_year
    profile.sgpa_percentage = sgpa_percentage
    profile.linkedin_url = linkedin_url
    profile.github_url = github_url
    profile.portfolio_url = portfolio_url
    profile.about_me = about_me
    profile.tagline = tagline
    profile.skills = skills
    profile.certifications = certifications
    profile.achievements = achievements

    public_url = f"{settings.BASE_URL}/profile/{profile.slug}"
    qr_filename = f"{profile.slug}_qr.png"
    qr_path_on_disk = os.path.join("static", "uploads", "qrs", qr_filename)
    qr_service.generate_profile_qr(public_url, qr_path_on_disk)
    profile.qr_code_path = f"/static/uploads/qrs/{qr_filename}"

    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/upload-media")
async def upload_media(
    request: Request,
    profile_pic: UploadFile = File(None),
    resume: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    profile = user.profile

    if profile_pic and profile_pic.filename:
        ext = os.path.splitext(profile_pic.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Invalid profile image type.")
        pic_filename = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(os.path.join("static", "uploads", "avatars"), exist_ok=True)
        pic_path = os.path.join("static", "uploads", "avatars", pic_filename)
        with open(pic_path, "wb") as f:
            f.write(await profile_pic.read())
        profile.profile_pic_path = f"/static/uploads/avatars/{pic_filename}"

    if resume and resume.filename:
        ext = os.path.splitext(resume.filename)[1].lower()
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(status_code=400, detail="Unsupported resume document format (PDF/Docx only).")
        resume_filename = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(os.path.join("static", "uploads", "resumes"), exist_ok=True)
        res_path = os.path.join("static", "uploads", "resumes", resume_filename)
        with open(res_path, "wb") as f:
            f.write(await resume.read())
        profile.resume_path = f"/static/uploads/resumes/{resume_filename}"

    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/projects/add")
async def add_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    tech_stack: str = Form(""),
    github_url: str = Form(""),
    live_url: str = Form(""),
    project_image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    proj_img_path = ""
    if project_image and project_image.filename:
        ext = os.path.splitext(project_image.filename)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            img_filename = f"{uuid.uuid4().hex}{ext}"
            os.makedirs(os.path.join("static", "uploads", "projects"), exist_ok=True)
            saved_path = os.path.join("static", "uploads", "projects", img_filename)
            with open(saved_path, "wb") as f:
                f.write(await project_image.read())
            proj_img_path = f"/static/uploads/projects/{img_filename}"

    new_project = Project(
        profile_id=user.profile.id,
        name=name,
        description=description,
        tech_stack=tech_stack,
        github_url=github_url,
        live_url=live_url,
        image_path=proj_img_path
    )
    db.add(new_project)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/projects/delete/{project_id}")
async def delete_project(request: Request, project_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.profile_id == user.profile.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    await db.delete(project)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/internships/add")
async def add_internship(
    request: Request,
    company: str = Form(...),
    role: str = Form(...),
    duration: str = Form(""),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    new_internship = Internship(
        profile_id=user.profile.id,
        company=company,
        role=role,
        duration=duration,
        description=description
    )
    db.add(new_internship)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/internships/delete/{internship_id}")
async def delete_internship(request: Request, internship_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    result = await db.execute(
        select(Internship).where(Internship.id == internship_id, Internship.profile_id == user.profile.id)
    )
    intern = result.scalars().first()
    if not intern:
        raise HTTPException(status_code=404, detail="Internship not found.")

    await db.delete(intern)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/certificates/add")
async def add_certificate(
    request: Request,
    title: str = Form(...),
    issuer: str = Form(""),
    certificate_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    if not certificate_file.filename:
         raise HTTPException(status_code=400, detail="Invalid certificate attachment file.")

    ext = os.path.splitext(certificate_file.filename)[1].lower()
    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
         raise HTTPException(status_code=400, detail="Unsupported file format (PDF, JPG, PNG only).")

    cert_filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(os.path.join("static", "uploads", "certificates"), exist_ok=True)
    save_path = os.path.join("static", "uploads", "certificates", cert_filename)
    
    with open(save_path, "wb") as f:
        f.write(await certificate_file.read())

    new_cert = CertificateFile(
        profile_id=user.profile.id,
        title=title,
        issuer=issuer,
        file_path=f"/static/uploads/certificates/{cert_filename}"
    )
    db.add(new_cert)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/certificates/delete/{cert_id}")
async def delete_certificate(request: Request, cert_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
         raise HTTPException(status_code=401, detail="Unauthorized session.")

    result = await db.execute(
        select(CertificateFile).where(CertificateFile.id == cert_id, CertificateFile.profile_id == user.profile.id)
    )
    cert = result.scalars().first()
    if not cert:
         raise HTTPException(status_code=404, detail="Certificate file not found.")

    await db.delete(cert)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/ai-improve")
async def run_ai_improvement(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user or not user.profile:
        raise HTTPException(status_code=401, detail="Unauthorized session.")

    profile = user.profile
    ai_data = ai_service.generate_portfolio_enhancements(profile.about_me or "", profile.skills or "")
    
    profile.tagline = ai_data.get("tagline", profile.tagline)
    profile.ai_summary = ai_data.get("ai_summary", profile.ai_summary)
    
    improvement_text = f"Suggested focus skills: {ai_data.get('missing_skills', '')}. Recommendation: {ai_data.get('improvement_suggestions', '')}"
    profile.achievements = (profile.achievements + "\n" + improvement_text) if profile.achievements else improvement_text

    await db.commit()
    return RedirectResponse(url="/dashboard?ai_enhanced=true", status_code=status.HTTP_303_SEE_OTHER)