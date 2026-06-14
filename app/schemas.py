from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    college: Optional[str] = ""
    degree: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    portfolio_url: Optional[str] = ""
    about_me: Optional[str] = ""
    tagline: Optional[str] = ""
    skills: Optional[str] = ""
    certifications: Optional[str] = ""
    achievements: Optional[str] = ""

class ProjectAdd(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str
    tech_stack: Optional[str] = ""
    github_url: Optional[str] = ""
    live_url: Optional[str] = ""

class AIImproveRequest(BaseModel):
    current_bio: str
    skills: str