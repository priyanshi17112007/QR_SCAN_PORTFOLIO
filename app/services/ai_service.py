import json
from google import genai
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.enabled = bool(self.api_key)
        if self.enabled:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-3.5-flash"  # Applied modern 3.5 core
        else:
            self.client = None

    def generate_portfolio_enhancements(self, bio: str, skills: str) -> dict:
        if not self.enabled or not self.client:
            return {
                "tagline": "Software Engineer & Designer",
                "ai_summary": f"Experienced builder skilled in {skills or 'software engineering'}. Proven background details: {bio or 'reliable codebase creations'}.",
                "missing_skills": "CI/CD, Kubernetes, Redis",
                "improvement_suggestions": "Try adding visual proof of active deployments and link live production URLs for maximum response rates."
            }
        
        prompt = f"""
        Act as an elite tech recruiter and software architect. Analyze this developer's profile:
        Bio: {bio}
        Skills: {skills}

        Generate a JSON output matching this structure exactly (provide nothing else):
        {{
            "tagline": "Impactful tagline, max 10 words",
            "ai_summary": "Polished, professional 3-sentence summary highlighting core values",
            "missing_skills": "Comma-separated list of 3 highly recommended industry-standard skills for their profile",
            "improvement_suggestions": "One quick action item to optimize their resume or page conversion"
        }}
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            return json.loads(raw_text.strip())
        except Exception:
            return {
                "tagline": "Software Engineer & Professional Developer",
                "ai_summary": f"Passionate professional focused on high-quality performance. Specialized in {skills or 'scalable engineering solutions'}.",
                "missing_skills": "TypeScript, AWS Architecture, Docker Compose",
                "improvement_suggestions": "Incorporate metrics like page rendering speeds or active API users to emphasize scalability."
            }

ai_service = AIService()