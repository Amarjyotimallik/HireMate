"""
Seed Script - Populate initial tasks from mock data

Converts the existing frontend mock questions into backend tasks with risk levels.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import connect_to_mongodb, close_mongodb_connection, get_tasks_collection, get_users_collection
from app.core import hash_password
from datetime import datetime, timezone


# Convert frontend mock questions to backend tasks with risk levels
SEED_TASKS = [
    {
        "title": "Production Bug Response",
        "description": "A critical bug is affecting users. Evaluate the candidate's crisis response approach.",
        "scenario": "You notice a critical bug in production affecting 10% of users. The fix requires rolling back a recent feature. What do you do?",
        "category": "problem_solving",
        "difficulty": "hard",
        "time_limit_seconds": 180,
        "options": [
            {
                "id": "opt_1",
                "text": "Immediately roll back the feature to stop the issue",
                "risk_level": "high",
                "behavioral_tags": ["decisive", "action_oriented", "quick_response"]
            },
            {
                "id": "opt_2",
                "text": "Investigate the root cause before taking action",
                "risk_level": "low",
                "behavioral_tags": ["analytical", "cautious", "methodical"]
            },
            {
                "id": "opt_3",
                "text": "Notify stakeholders and coordinate a response plan",
                "risk_level": "medium",
                "behavioral_tags": ["collaborative", "cautious", "process_oriented"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Code Review Disagreement",
        "description": "Handling technical disagreements in a collaborative environment.",
        "scenario": "A team member disagrees with your technical approach during code review. How do you respond?",
        "category": "communication",
        "difficulty": "medium",
        "time_limit_seconds": 150,
        "options": [
            {
                "id": "opt_1",
                "text": "Defend your approach with technical justification",
                "risk_level": "medium",
                "behavioral_tags": ["confident", "assertive", "technical"]
            },
            {
                "id": "opt_2",
                "text": "Schedule a meeting to discuss alternatives",
                "risk_level": "low",
                "behavioral_tags": ["collaborative", "open_minded", "diplomatic"]
            },
            {
                "id": "opt_3",
                "text": "Escalate to the team lead for a decision",
                "risk_level": "high",
                "behavioral_tags": ["process_oriented", "risk_averse", "hierarchical"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Estimation Under Uncertainty",
        "description": "Approaching estimation when facing unknowns.",
        "scenario": "You're asked to estimate a feature that touches unfamiliar parts of the codebase. What's your approach?",
        "category": "decision_confidence",
        "difficulty": "medium",
        "time_limit_seconds": 150,
        "options": [
            {
                "id": "opt_1",
                "text": "Provide a rough estimate and refine later",
                "risk_level": "high",
                "behavioral_tags": ["confident", "agile", "risk_tolerant"]
            },
            {
                "id": "opt_2",
                "text": "Spend time exploring the codebase first",
                "risk_level": "low",
                "behavioral_tags": ["thorough", "analytical", "methodical"]
            },
            {
                "id": "opt_3",
                "text": "Give a conservative high estimate",
                "risk_level": "medium",
                "behavioral_tags": ["cautious", "risk_averse", "protective"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Deadline Pressure with Misunderstood Requirements",
        "description": "Handling project constraints when facing unexpected challenges.",
        "scenario": "Your project deadline is in 2 days, but you discover the requirements were misunderstood. What do you do?",
        "category": "analytical_thinking",
        "difficulty": "hard",
        "time_limit_seconds": 180,
        "options": [
            {
                "id": "opt_1",
                "text": "Work overtime to meet the original deadline",
                "risk_level": "high",
                "behavioral_tags": ["dedicated", "risk_tolerant", "self_sacrificing"]
            },
            {
                "id": "opt_2",
                "text": "Immediately inform stakeholders and request extension",
                "risk_level": "medium",
                "behavioral_tags": ["transparent", "communicative", "realistic"]
            },
            {
                "id": "opt_3",
                "text": "Reprioritize to deliver core functionality on time",
                "risk_level": "low",
                "behavioral_tags": ["strategic", "analytical", "prioritization"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Performance Improvement Opportunity",
        "description": "Balancing improvement opportunities with existing commitments.",
        "scenario": "You find a more efficient algorithm that would improve performance by 40%, but requires refactoring. Do you:",
        "category": "speed_accuracy",
        "difficulty": "medium",
        "time_limit_seconds": 150,
        "options": [
            {
                "id": "opt_1",
                "text": "Implement it now even if it delays other tasks",
                "risk_level": "high",
                "behavioral_tags": ["perfectionist", "optimization_focused", "risk_tolerant"]
            },
            {
                "id": "opt_2",
                "text": "Add it to the backlog for future sprint",
                "risk_level": "low",
                "behavioral_tags": ["process_oriented", "patient", "organized"]
            },
            {
                "id": "opt_3",
                "text": "Implement only if time permits this sprint",
                "risk_level": "medium",
                "behavioral_tags": ["flexible", "opportunistic", "balanced"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Stakeholder Feature Request Conflict",
        "description": "Managing stakeholder expectations during demonstrations.",
        "scenario": "During a demo, a stakeholder requests a feature change that conflicts with the original requirements. You:",
        "category": "communication",
        "difficulty": "hard",
        "time_limit_seconds": 180,
        "options": [
            {
                "id": "opt_1",
                "text": "Agree and add it to scope immediately",
                "risk_level": "high",
                "behavioral_tags": ["accommodating", "eager_to_please", "flexible"]
            },
            {
                "id": "opt_2",
                "text": "Explain the conflict and suggest alternatives",
                "risk_level": "medium",
                "behavioral_tags": ["diplomatic", "problem_solver", "communicative"]
            },
            {
                "id": "opt_3",
                "text": "Defer decision to product manager",
                "risk_level": "low",
                "behavioral_tags": ["process_oriented", "hierarchical", "risk_averse"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Security Vulnerability in Code Review",
        "description": "Handling sensitive issues in code review with senior colleagues.",
        "scenario": "You're reviewing code and notice security vulnerabilities. The author is a senior engineer. You:",
        "category": "problem_solving",
        "difficulty": "medium",
        "time_limit_seconds": 150,
        "options": [
            {
                "id": "opt_1",
                "text": "Comment directly on the security issues",
                "risk_level": "medium",
                "behavioral_tags": ["direct", "principled", "courageous"]
            },
            {
                "id": "opt_2",
                "text": "Message them privately first",
                "risk_level": "low",
                "behavioral_tags": ["diplomatic", "empathetic", "respectful"]
            },
            {
                "id": "opt_3",
                "text": "Approve and fix it yourself later",
                "risk_level": "high",
                "behavioral_tags": ["non_confrontational", "self_reliant", "risky"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Implementation Speed vs Maintainability",
        "description": "Classic trade-off between short-term delivery and long-term quality.",
        "scenario": "Two approaches exist: one is faster to implement, the other is more maintainable. Deadline is tight. You choose:",
        "category": "speed_accuracy",
        "difficulty": "hard",
        "time_limit_seconds": 180,
        "options": [
            {
                "id": "opt_1",
                "text": "Faster implementation to meet deadline",
                "risk_level": "high",
                "behavioral_tags": ["pragmatic", "deadline_focused", "risk_tolerant"]
            },
            {
                "id": "opt_2",
                "text": "Hybrid approach balancing both",
                "risk_level": "medium",
                "behavioral_tags": ["balanced", "creative", "diplomatic"]
            },
            {
                "id": "opt_3",
                "text": "Discuss trade-offs with team",
                "risk_level": "low",
                "behavioral_tags": ["collaborative", "transparent", "inclusive"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Junior Developer Help Request",
        "description": "Managing competing priorities when asked for help.",
        "scenario": "A junior developer asks for help while you're deep in debugging a critical issue. You:",
        "category": "communication",
        "difficulty": "easy",
        "time_limit_seconds": 120,
        "options": [
            {
                "id": "opt_1",
                "text": "Drop your task and help them immediately",
                "risk_level": "high",
                "behavioral_tags": ["helpful", "mentoring", "team_focused"]
            },
            {
                "id": "opt_2",
                "text": "Ask them to wait until you finish",
                "risk_level": "low",
                "behavioral_tags": ["focused", "prioritizing", "boundary_setting"]
            },
            {
                "id": "opt_3",
                "text": "Point them to documentation",
                "risk_level": "medium",
                "behavioral_tags": ["resourceful", "self_sufficiency_promoting", "efficient"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
    {
        "title": "Library Vulnerability Response",
        "description": "Handling security vulnerabilities in dependencies.",
        "scenario": "You discover that a library you depend on has a critical vulnerability. The fix requires upgrading with breaking changes. You:",
        "category": "analytical_thinking",
        "difficulty": "hard",
        "time_limit_seconds": 180,
        "options": [
            {
                "id": "opt_1",
                "text": "Upgrade immediately and fix breaking changes",
                "risk_level": "high",
                "behavioral_tags": ["security_focused", "decisive", "action_oriented"]
            },
            {
                "id": "opt_2",
                "text": "Apply a temporary patch/workaround",
                "risk_level": "medium",
                "behavioral_tags": ["pragmatic", "creative", "risk_managing"]
            },
            {
                "id": "opt_3",
                "text": "Assess risk and prioritize accordingly",
                "risk_level": "low",
                "behavioral_tags": ["analytical", "measured", "strategic"]
            }
        ],
        "reasoning_required": True,
        "reasoning_min_length": 20,
    },
]

# Default admin user
DEFAULT_ADMIN = {
    "email": "admin@hiremate.com",
    "full_name": "HireMate Admin",
    "password": "admin123456",  # Change in production!
    "role": "admin",
}


async def seed_database():
    """Seed the database with initial data."""
    print("[*] Starting database seed...")
    
    await connect_to_mongodb()
    
    try:
        # Seed admin user
        users = get_users_collection()
        existing_admin = await users.find_one({"email": DEFAULT_ADMIN["email"]})
        
        if not existing_admin:
            now = datetime.now(timezone.utc)
            admin_doc = {
                "email": DEFAULT_ADMIN["email"],
                "full_name": DEFAULT_ADMIN["full_name"],
                "password_hash": hash_password(DEFAULT_ADMIN["password"]),
                "role": DEFAULT_ADMIN["role"],
                "organization_id": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            result = await users.insert_one(admin_doc)
            print(f"[OK] Created admin user: {DEFAULT_ADMIN['email']}")
            admin_id = str(result.inserted_id)
        else:
            print(f"[i] Admin user already exists: {DEFAULT_ADMIN['email']}")
            admin_id = str(existing_admin["_id"])
        
        # Seed tasks
        tasks = get_tasks_collection()
        existing_count = await tasks.count_documents({})
        
        if existing_count == 0:
            now = datetime.now(timezone.utc)
            for task_data in SEED_TASKS:
                task_doc = {
                    **task_data,
                    "created_by": admin_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
                await tasks.insert_one(task_doc)
            
            print(f"[OK] Seeded {len(SEED_TASKS)} tasks")
        else:
            print(f"[i] Tasks already exist ({existing_count} found), skipping seed")
        
        print("\n[OK] Database seed completed!")
        print(f"\nAdmin credentials:")
        print(f"   Email: {DEFAULT_ADMIN['email']}")
        print(f"   Password: {DEFAULT_ADMIN['password']}")
        print(f"\n[!] Remember to change the admin password in production!")
        
    finally:
        await close_mongodb_connection()


if __name__ == "__main__":
    asyncio.run(seed_database())
