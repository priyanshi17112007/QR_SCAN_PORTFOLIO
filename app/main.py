import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routers import auth_router, dashboard_router, profile_router

app = FastAPI(
    title="AI Smart QR Portfolio",
    description="Digital modern business profiles with adaptive scanning QR integration.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

def make_upload_dirs():
    directories = [
        "static/uploads/avatars",
        "static/uploads/resumes",
        "static/uploads/projects",
        "static/uploads/qrs",
        "static/uploads/certificates"
    ]
    for directory in directories:
        if os.path.exists(directory) and not os.path.isdir(directory):
            try:
                os.remove(directory)
            except OSError:
                pass

        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            if not os.path.isdir(directory):
                raise

make_upload_dirs()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(dashboard_router.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/register")