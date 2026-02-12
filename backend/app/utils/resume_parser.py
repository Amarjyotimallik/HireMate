"""
Resume Parser Utility

Extracts text from uploaded documents (PDF, plain text) and parses
name, email, phone, position for use in candidate_info when creating attempts.
"""

import re
import os
from typing import Optional

# PDF text extraction
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def extract_text_from_file(content: bytes, content_type: str, filename: str) -> str:
    """
    Extract raw text from file content.
    Supports PDF and plain text.
    """
    if not content or len(content) == 0:
        return ""

    # PDF
    if content_type == "application/pdf" or (filename and filename.lower().endswith(".pdf")):
        if not HAS_PYPDF:
            raise ValueError("PDF support requires pypdf. Install with: pip install pypdf")
        try:
            import io
            reader = PdfReader(io.BytesIO(content))
            parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            return "\n".join(parts) if parts else ""
        except Exception as e:
            raise ValueError(f"Could not extract text from PDF: {e}")

    # Plain text
    if content_type.startswith("text/") or (filename and filename.lower().endswith(".txt")):
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return content.decode("latin-1", errors="replace")

    raise ValueError("Unsupported file type. Use PDF or plain text (.txt).")


import json
from groq import Groq

from app.config import get_settings

def parse_resume_with_groq(text: str) -> dict:
    """
    Parse resume text using Groq LLM (gpt-oss-120b) for high accuracy.
    """
    api_key = get_settings().groq_api_key
    if not api_key:
        print("[WARNING] GROQ_API_KEY not found in settings. Falling back to regex.")
        return None

    try:
        client = Groq(api_key=api_key)
        settings = get_settings()
        
        system_msg = "You are a high-precision document parser. Extract candidate information into structured JSON. Be concise and accurate."
        
        prompt = f"""
        Extract candidate information from the following resume text.
        Return ONLY a JSON object with strictly these keys: "name", "email", "phone", "position", "skills" (list of technical skills).
        
        Guidelines:
        - "name": The candidate's full name.
        - "email": Primary email address.
        - "phone": Contact number.
        - "position": Extract their most recent professional job title. If a student/fresher, use "Student" or "Fresher".
        - "skills": Top 5-10 specific technical skills found in the text.
        
        Wait, if a field is not found, use null (or empty list for skills). 
        Do not make up information.
        
        Resume Text:
        ---
        {text[:8000]}
        ---
        
        JSON Response:
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_msg,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=settings.ai_model_120b,  # Switched to 120B as requested
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        content = chat_completion.choices[0].message.content.strip()
        
        # Robust JSON extraction (handle markdown blocks if any)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"[ERROR] Groq parsing failed: {e}")
        return None


def parse_resume_text(text: str) -> dict:
    """
    Parse extracted text for name, email, phone, position.
    Uses Groq 120B first, then falls back to regex.
    """
    # 1. Try Groq AI Parsing (Primary - 120B)
    ai_result = parse_resume_with_groq(text)
    if ai_result:
        return {
            "name": ai_result.get("name"),
            "email": ai_result.get("email"),
            "phone": str(ai_result.get("phone")) if ai_result.get("phone") else None,
            "position": ai_result.get("position"),
            "skills": ai_result.get("skills") or [],
        }

    # 2. Fallback to Regex
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "position": None,
        "skills": [],
    }
    if not text or not text.strip():
        return result

    # Email
    email_re = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    email_match = email_re.search(text)
    if email_match:
        result["email"] = email_match.group(0).strip()

    # Phone (common formats)
    phone_re = re.compile(
        r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
        r"|(?:\+?[0-9]{1,3}[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
    )
    phone_match = phone_re.search(text)
    if phone_match:
        result["phone"] = re.sub(r"\s+", " ", phone_match.group(0).strip())[:20]

    # Name: "Name:" label or first line that looks like a full name (2+ capitalized words)
    name_patterns = [
        re.compile(r"Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", re.IGNORECASE),
        re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*$", re.MULTILINE),
    ]
    for pat in name_patterns:
        m = pat.search(text)
        if m and m.group(1) and len(m.group(1).split()) >= 2:
            result["name"] = m.group(1).strip()[:100]
            break
    if not result["name"]:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for line in lines[:5]:
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", line) and not re.search(r"\d", line):
                result["name"] = line[:100]
                break

    # Position / job title (keywords common in resumes)
    position_keywords = [
        "Developer", "Engineer", "Designer", "Manager", "Analyst", "Architect",
        "Consultant", "Specialist", "Lead", "Senior", "Junior", "Full Stack",
        "Backend", "Frontend", "DevOps", "Product", "Data", "Software", "UX",
        "UI", "QA", "Test", "Security", "Cloud",
    ]
    for keyword in position_keywords:
        pat = re.compile(r"[\w\s]*" + re.escape(keyword) + r"[\w\s]*", re.IGNORECASE)
        m = pat.search(text)
        if m and len(m.group(0).strip()) < 80:
            result["position"] = m.group(0).strip()[:100]
            break

    return result
