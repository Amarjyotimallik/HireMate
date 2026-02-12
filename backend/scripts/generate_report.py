"""
Metric Analysis Report Generator

Fetches the latest completed assessment and generates a detailed performance report.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, get_attempts_collection
from app.services.live_metrics_service import compute_live_metrics

async def generate_report():
    await connect_to_mongodb()
    attempts = get_attempts_collection()
    
    # Get the most recent active or completed attempt
    cursor = attempts.find({}).sort("updated_at", -1).limit(1)
    attempt = await cursor.next()
    
    if not attempt:
        print("No assessments found.")
        await close_mongodb_connection()
        return

    print(f"Analyzing attempt: {attempt['_id']} ({attempt['candidate_info']['name']})")
    
    # Compute full metrics
    metrics = await compute_live_metrics(str(attempt["_id"]))
    
    if not metrics:
        print("Failed to compute metrics.")
        return

    # Generate Markdown Report
    report = f"""
# 📊 HireMate Assessment Report
**Candidate:** {metrics['candidate']['name']}
**Role:** {metrics['candidate']['position']}
**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

---

## 1. Executive Summary
**Role Fit Score:** {metrics['role_fit']['overall_score']}/100
**Recommendation:** {metrics['role_fit']['recommendation']}
**Behavioral Profile:** {metrics['behavioral_summary']['decision_style']} Decision Maker

## 2. Key Metrics
| Metric | Value | Rating |
| :--- | :--- | :--- |
| **Decision Speed** | {metrics['metrics']['avg_response_time']}s | {metrics['metrics']['decision_speed']} |
| **Hesitation** | {metrics['metrics']['hesitation_level']}/100 | {'Low' if metrics['metrics']['hesitation_level'] < 30 else 'High'} |
| **Focus Score** | {metrics['metrics']['focus_score']}/100 | {'High' if metrics['metrics']['focus_score'] > 80 else 'Moderate'} |
| **Technical Confidence** | {metrics['metrics']['confidence_indicator']}/100 | - |

## 3. Skill Radar Analysis
- **Problem Solving:** {metrics['skill_profile']['problem_solving']}
- **Decision Speed:** {metrics['skill_profile']['decision_speed']}
- **Analytical Thinking:** {metrics['skill_profile']['analytical_thinking']}
- **Creativity:** {metrics['skill_profile']['creativity']}
- **Risk Assessment:** {metrics['skill_profile']['risk_assessment']}

## 4. Bluff Detection & Resume Fit
**Verified Skills:** {metrics['resume_comparison']['skills_verified']} / {metrics['resume_comparison']['skills_total']}
**Overall Claim Match:** {metrics['resume_comparison']['overall_match']}%

### Detailed Claim Analysis
| Skill | Claimed Level | Verified Level | Status |
| :--- | :--- | :--- | :--- |
"""
    
    for claim in metrics['resume_comparison']['claims']:
        report += f"| {claim['skill']} | {claim['claimed']} | {claim['verified']} | {claim['status']} |\n"

    report += f"""
---
## 5. Candidate Insights
"""
    for insight in metrics['candidate_insights']:
         icon = "✅" if insight['type'] == 'positive' else ("⚠️" if insight['type'] == 'warning' else "ℹ️")
         report += f"- {icon} **{insight['label']}**\n"
         
    print(report)
    
    # Save to file
    with open("assessment_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    print("\n[SUCCESS] Report generated: assessment_report.md")

    await close_mongodb_connection()

if __name__ == "__main__":
    asyncio.run(generate_report())
