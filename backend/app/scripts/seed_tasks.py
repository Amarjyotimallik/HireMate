"""
Seed Tasks Script

Populates MongoDB with behavior-based decision tasks for candidate assessments.
Each task presents a scenario where:
- There is NO correct answer
- The system observes HOW the candidate decides, not WHAT they choose
- Options have risk_level (low/medium/high) for behavior profiling

Run with: python -m app.scripts.seed_tasks
Or: python backend/app/scripts/seed_tasks.py
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from bson import ObjectId

# Add parent path for imports
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

# Load .env file from backend root
from dotenv import load_dotenv
env_path = backend_root / ".env"
load_dotenv(env_path)

from motor.motor_asyncio import AsyncIOMotorClient

# Configuration - load from .env
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "hiremate")


# ============================================================================
# TASK DEFINITIONS - Using correct TaskOption schema
# ============================================================================

TASKS = [
    {
        "task_code": "TASK_001",
        "title": "Project Deadline Decision",
        "description": "Navigate a challenging project timeline scenario",
        "category": "decision_confidence",
        "difficulty": "medium",
        "scenario": "Your team is behind on a critical project deadline. You have limited resources and must choose how to proceed. What approach do you take?",
        "options": [
            {"id": "opt_1", "text": "Request a deadline extension from stakeholders - communicate challenges and negotiate more time", "risk_level": "low", "behavioral_tags": ["conservative", "communicative"]},
            {"id": "opt_2", "text": "Cut non-essential features to meet the deadline - prioritize core functionality", "risk_level": "medium", "behavioral_tags": ["pragmatic", "decisive"]},
            {"id": "opt_3", "text": "Push the team to work overtime to complete everything - maintain scope with extra effort", "risk_level": "high", "behavioral_tags": ["aggressive", "risk-taking"]},
            {"id": "opt_4", "text": "Bring in additional resources from other teams - expand capacity by borrowing help", "risk_level": "medium", "behavioral_tags": ["resourceful", "collaborative"]}
        ]
    },
    {
        "task_code": "TASK_002",
        "title": "Bug vs Feature Priority",
        "description": "Prioritize between stability and growth",
        "category": "problem_solving",
        "difficulty": "easy",
        "scenario": "A production bug affects 5% of users but a new feature could increase revenue by 10%. Development can only focus on one. What do you prioritize?",
        "options": [
            {"id": "opt_1", "text": "Fix the bug first - prioritize stability and user trust over new features", "risk_level": "low", "behavioral_tags": ["quality-focused", "user-centric"]},
            {"id": "opt_2", "text": "Ship the feature first - prioritize business growth while the bug affects few users", "risk_level": "high", "behavioral_tags": ["growth-oriented", "risk-taking"]},
            {"id": "opt_3", "text": "Split the team to work on both - attempt to address both issues simultaneously", "risk_level": "medium", "behavioral_tags": ["balanced", "multitasking"]},
            {"id": "opt_4", "text": "Gather more data before deciding - analyze bug impact and feature projections in detail", "risk_level": "low", "behavioral_tags": ["analytical", "methodical"]}
        ]
    },
    {
        "task_code": "TASK_003",
        "title": "Client Expectation Mismatch",
        "description": "Handle a difficult client situation",
        "category": "communication",
        "difficulty": "hard",
        "scenario": "A client has expectations that differ significantly from what was initially agreed. They're unhappy with the current deliverables. How do you handle this?",
        "options": [
            {"id": "opt_1", "text": "Refer them to the original contract terms - stand firm on agreed scope", "risk_level": "high", "behavioral_tags": ["firm", "boundary-setting"]},
            {"id": "opt_2", "text": "Accommodate their requests within reason - find middle ground with some changes", "risk_level": "medium", "behavioral_tags": ["flexible", "customer-focused"]},
            {"id": "opt_3", "text": "Schedule a meeting to understand their concerns - invest time in dialogue first", "risk_level": "low", "behavioral_tags": ["empathetic", "communicative"]},
            {"id": "opt_4", "text": "Escalate to senior management - involve leadership for complex situations", "risk_level": "low", "behavioral_tags": ["procedural", "cautious"]}
        ]
    },
    {
        "task_code": "TASK_004",
        "title": "Technology Stack Decision",
        "description": "Choose between proven and innovative solutions",
        "category": "analytical_thinking",
        "difficulty": "medium",
        "scenario": "Your team must choose between a proven but older technology and a newer, more efficient but less tested one for a critical system. What do you recommend?",
        "options": [
            {"id": "opt_1", "text": "Use the proven older technology - prioritize reliability and team familiarity", "risk_level": "low", "behavioral_tags": ["conservative", "practical"]},
            {"id": "opt_2", "text": "Use the newer technology for everything - embrace innovation fully", "risk_level": "high", "behavioral_tags": ["innovative", "risk-taking"]},
            {"id": "opt_3", "text": "Pilot the new tech in a non-critical area first - test before committing", "risk_level": "medium", "behavioral_tags": ["measured", "experimental"]},
            {"id": "opt_4", "text": "Build with old tech but design for future migration - start safe, plan ahead", "risk_level": "medium", "behavioral_tags": ["strategic", "forward-thinking"]}
        ]
    },
    {
        "task_code": "TASK_005",
        "title": "Team Disagreement Resolution",
        "description": "Resolve a conflict between senior team members",
        "category": "communication",
        "difficulty": "medium",
        "scenario": "Two senior team members strongly disagree on an architectural approach. The conflict is causing delays. As the decision-maker, what do you do?",
        "options": [
            {"id": "opt_1", "text": "Make a unilateral decision to move forward - exercise authority to break deadlock", "risk_level": "high", "behavioral_tags": ["decisive", "authoritative"]},
            {"id": "opt_2", "text": "Facilitate a structured debate with clear criteria - create framework for evaluation", "risk_level": "low", "behavioral_tags": ["facilitative", "process-oriented"]},
            {"id": "opt_3", "text": "Bring in an external expert opinion - get outside perspective", "risk_level": "medium", "behavioral_tags": ["collaborative", "open-minded"]},
            {"id": "opt_4", "text": "Have each person build a small proof of concept - let data guide the decision", "risk_level": "medium", "behavioral_tags": ["empirical", "fair"]}
        ]
    },
    {
        "task_code": "TASK_006",
        "title": "Limited Budget Allocation",
        "description": "Allocate limited resources across competing priorities",
        "category": "decision_confidence",
        "difficulty": "hard",
        "scenario": "You have budget for only one of three equally important initiatives: hiring, tooling, or training. How do you decide where to invest?",
        "options": [
            {"id": "opt_1", "text": "Invest in hiring new talent - add capacity and fresh perspectives", "risk_level": "high", "behavioral_tags": ["growth-oriented", "ambitious"]},
            {"id": "opt_2", "text": "Invest in better tooling and infrastructure - improve existing productivity", "risk_level": "medium", "behavioral_tags": ["efficiency-focused", "practical"]},
            {"id": "opt_3", "text": "Invest in training and upskilling current team - develop existing talent", "risk_level": "low", "behavioral_tags": ["people-focused", "developmental"]},
            {"id": "opt_4", "text": "Split the budget across all three - make smaller investments in each", "risk_level": "medium", "behavioral_tags": ["balanced", "risk-averse"]}
        ]
    },
    {
        "task_code": "TASK_007",
        "title": "Security vs Delivery Speed",
        "description": "Balance security concerns with business deadlines",
        "category": "problem_solving",
        "difficulty": "hard",
        "scenario": "A security audit found medium-severity vulnerabilities in code scheduled for release tomorrow. The business is counting on this release. What do you do?",
        "options": [
            {"id": "opt_1", "text": "Delay the release until vulnerabilities are fixed - prioritize security", "risk_level": "low", "behavioral_tags": ["security-conscious", "principled"]},
            {"id": "opt_2", "text": "Release on schedule with documented risk acceptance - meet deadline transparently", "risk_level": "high", "behavioral_tags": ["business-focused", "risk-accepting"]},
            {"id": "opt_3", "text": "Apply quick patches and release with monitoring - mitigate risks partially", "risk_level": "medium", "behavioral_tags": ["pragmatic", "adaptive"]},
            {"id": "opt_4", "text": "Release reduced scope avoiding vulnerable code - deliver something safe", "risk_level": "medium", "behavioral_tags": ["cautious", "scope-aware"]}
        ]
    },
    {
        "task_code": "TASK_008",
        "title": "Delivering Difficult Feedback",
        "description": "Address a team member's declining performance",
        "category": "communication",
        "difficulty": "medium",
        "scenario": "A team member's performance has declined noticeably over the past month. Others have started to notice. How do you address this?",
        "options": [
            {"id": "opt_1", "text": "Have a direct conversation immediately - address the issue head-on", "risk_level": "medium", "behavioral_tags": ["direct", "proactive"]},
            {"id": "opt_2", "text": "Document instances first, then have formal discussion - build clear case", "risk_level": "low", "behavioral_tags": ["methodical", "thorough"]},
            {"id": "opt_3", "text": "Wait to see if performance improves on its own - give time for self-correction", "risk_level": "high", "behavioral_tags": ["patient", "hands-off"]},
            {"id": "opt_4", "text": "Check in casually to understand if something is wrong - approach with empathy", "risk_level": "low", "behavioral_tags": ["empathetic", "supportive"]}
        ]
    },
    {
        "task_code": "TASK_009",
        "title": "Innovation vs Maintenance",
        "description": "Balance innovation time with operational needs",
        "category": "analytical_thinking",
        "difficulty": "easy",
        "scenario": "Your team wants to dedicate 20% of time to innovation projects, but there's a backlog of maintenance work. How do you balance this?",
        "options": [
            {"id": "opt_1", "text": "Clear the maintenance backlog first - prioritize stability before innovation", "risk_level": "low", "behavioral_tags": ["responsible", "disciplined"]},
            {"id": "opt_2", "text": "Start innovation time immediately - prioritize creativity and motivation", "risk_level": "high", "behavioral_tags": ["innovative", "morale-focused"]},
            {"id": "opt_3", "text": "Dedicate 10% to innovation, 10% extra to maintenance - balanced compromise", "risk_level": "medium", "behavioral_tags": ["balanced", "diplomatic"]},
            {"id": "opt_4", "text": "Use innovation time to build tools that reduce maintenance - align both needs", "risk_level": "medium", "behavioral_tags": ["strategic", "efficient"]}
        ]
    },
    {
        "task_code": "TASK_010",
        "title": "External Vendor Dependency",
        "description": "Handle an unreliable third-party service",
        "category": "problem_solving",
        "difficulty": "hard",
        "scenario": "A critical third-party service your product depends on is becoming unreliable. Switching vendors would take 3 months of engineering effort. What do you do?",
        "options": [
            {"id": "opt_1", "text": "Start vendor migration immediately - invest upfront to eliminate risk", "risk_level": "medium", "behavioral_tags": ["proactive", "long-term focused"]},
            {"id": "opt_2", "text": "Build redundancy with a second vendor - reduce single-point-of-failure", "risk_level": "high", "behavioral_tags": ["thorough", "risk-aware"]},
            {"id": "opt_3", "text": "Negotiate SLAs and escalation paths - try to improve without changing", "risk_level": "low", "behavioral_tags": ["diplomatic", "cost-conscious"]},
            {"id": "opt_4", "text": "Build an in-house fallback solution - create internal capability as backup", "risk_level": "medium", "behavioral_tags": ["self-reliant", "strategic"]}
        ]
    },
]


# ============================================================================
# SEED FUNCTION
# ============================================================================

async def seed_tasks():
    """Seed all tasks into MongoDB."""
    print(f"Connecting to MongoDB: {MONGODB_URL}")
    print(f"Database: {MONGODB_DATABASE}")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    tasks_coll = db.tasks
    
    # Verify connection
    await client.admin.command("ping")
    print("[OK] Connected to MongoDB")
    
    # Delete all existing tasks to ensure clean seed
    existing_count = await tasks_coll.count_documents({})
    if existing_count > 0:
        print(f"[!] Found {existing_count} existing tasks - deleting all...")
        await tasks_coll.delete_many({})
        print("[OK] Deleted existing tasks")
    
    # Insert tasks
    inserted = 0
    for task_data in TASKS:
        task_doc = {
            "_id": ObjectId(),
            "task_code": task_data["task_code"],
            "title": task_data["title"],
            "description": task_data["description"],
            "scenario": task_data["scenario"],
            "category": task_data["category"],
            "difficulty": task_data["difficulty"],
            "time_limit_seconds": 120,
            "options": task_data["options"],
            "reasoning_required": True,
            "reasoning_min_length": 20,
            "created_by": "system",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await tasks_coll.insert_one(task_doc)
        print(f"[+] Inserted: {task_data['task_code']} - {task_data['title']}")
        inserted += 1
    
    print(f"\n[DONE] Inserted {inserted} tasks")
    print(f"[INFO] Total tasks in database: {await tasks_coll.count_documents({})}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_tasks())
