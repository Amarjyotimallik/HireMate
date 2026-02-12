"""
Email Service

Sends assessment invitation emails to candidates using Resend API.
"""

import httpx
from typing import Optional
from app.config import get_settings


async def send_assessment_email(
    to_email: str,
    candidate_name: str,
    assessment_link: str,
    position: str = "the position",
    expires_days: int = 7,
) -> dict:
    """
    Send an assessment invitation email to a candidate.
    
    Returns dict with {"success": True, "message_id": "..."} on success.
    Raises exception on failure.
    """
    settings = get_settings()
    
    if not settings.resend_api_key:
        raise ValueError("RESEND_API_KEY not configured. Please add it to your .env file.")
    
    # Build beautiful HTML email (use single-line links for email client compatibility)
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f5;">
<div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
<div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 16px 16px 0 0; padding: 40px; text-align: center;">
<h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">🎯 HireMate</h1>
<p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">AI-Powered Behavioral Assessment</p>
</div>
<div style="background: white; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h2 style="color: #1f2937; margin: 0 0 20px 0; font-size: 22px;">Hello {candidate_name}! 👋</h2>
<p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
You've been invited to complete a behavioral assessment for <strong>{position}</strong>.
</p>
<p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
This assessment evaluates your decision-making approach through realistic workplace scenarios. 
There are no right or wrong answers – we're interested in understanding <em>how</em> you think.
</p>
<div style="text-align: center; margin: 30px 0;">
<a href="{assessment_link}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);">Start Assessment →</a>
</div>
<div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 30px 0;">
<h3 style="color: #374151; margin: 0 0 15px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">What to Expect</h3>
<ul style="color: #4b5563; margin: 0; padding: 0 0 0 20px; line-height: 1.8;">
<li>📝 10 scenario-based questions</li>
<li>⏱️ Approximately 15-20 minutes</li>
<li>💻 Works best on desktop browser</li>
<li>📅 Link expires in {expires_days} days</li>
</ul>
</div>
<p style="color: #9ca3af; font-size: 12px; margin: 30px 0 0 0; word-break: break-all;">
If the button doesn't work, copy this link:<br>
<a href="{assessment_link}" style="color: #6366f1;">{assessment_link}</a>
</p>
</div>
<div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
<p style="margin: 0;">Powered by HireMate – AI-Driven Hiring Intelligence</p>
<p style="margin: 5px 0 0 0;">© 2026 Xplora Innovation</p>
</div>
</div>
</body>
</html>"""
    
    # Plain text fallback
    text_content = f"""
Hello {candidate_name}!

You've been invited to complete a behavioral assessment for {position}.

This assessment evaluates your decision-making approach through realistic workplace scenarios.
There are no right or wrong answers – we're interested in understanding how you think.

Start your assessment here: {assessment_link}

What to Expect:
• 10 scenario-based questions
• Approximately 15-20 minutes
• Works best on desktop browser
• Link expires in {expires_days} days

Good luck!

---
Powered by HireMate – AI-Driven Hiring Intelligence
© 2026 Xplora Innovation
    """
    
    # Send via Resend API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from_address,
                "to": [to_email],
                "subject": f"🎯 {candidate_name}, Your Assessment is Ready!",
                "html": html_content,
                "text": text_content,
            },
            timeout=30.0,
        )
        
        # Accept any 2xx status code
        if 200 <= response.status_code < 300:
            data = response.json()
            return {"success": True, "message_id": data.get("id")}
        else:
            # Try to parse error details
            try:
                error_data = response.json()
                error_msg = error_data.get("message") or error_data.get("error") or str(error_data)
            except Exception:
                error_msg = response.text
            print(f"[EMAIL ERROR] Resend API returned {response.status_code}: {error_msg}")
            raise Exception(f"Resend API error ({response.status_code}): {error_msg}")
