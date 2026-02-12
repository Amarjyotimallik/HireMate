"""
Seed Demo Candidates Script

Creates 3 pre-completed candidate assessments with distinct behavioral profiles
for instant hackathon demo capability:

1. Sarah Chen - "Analytical Thinker" (slow, methodical, detailed, low risk)
2. Mike Johnson - "Exploratory Thinker" (fast, many changes, brief, varied risk)
3. Test Candidate - "Suspicious Activity" (uniform timing, paste events, focus losses)

Run with: python -m app.scripts.seed_demo_candidates
"""

import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
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

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "hiremate")

# Demo recruiter ID (will use existing recruiter)
DEMO_RECRUITER_EMAIL = "admin@hiremate.com"


# ============================================================================
# DEMO CANDIDATE PROFILES
# ============================================================================

DEMO_CANDIDATES = [
    {
        "name": "Sarah Chen",
        "email": "sarah.chen@demo.hiremate.ai",
        "position": "Senior Product Manager",
        "profile_type": "analytical",
        "resume_text": "Experienced product manager with 8+ years in tech. Led cross-functional teams at Google and Microsoft. Strong analytical background with MBA from Stanford. Expert in data-driven decision making and stakeholder management.",
        "skills": ["Product Strategy", "Data Analysis", "Team Leadership", "Stakeholder Management"],
        "behavior": {
            "first_decision_range": (35, 50),  # seconds - slow, thoughtful
            "option_changes_range": (0, 1),     # very firm
            "explanation_words_range": (40, 60),  # detailed
            "explanation_has_keywords": True,   # uses logical connectors
            "risk_preference": "low",           # conservative
            "paste_events": 0,
            "focus_losses": 0,
            "long_idles": 0,
            "timing_variance": "high",  # natural human variance
        }
    },
    {
        "name": "Mike Johnson",
        "email": "mike.johnson@demo.hiremate.ai",
        "position": "Growth Marketing Lead",
        "profile_type": "exploratory",
        "resume_text": "Dynamic marketing professional with startup experience. Built growth teams from 0 to 50. Quick decision maker who thrives in fast-paced environments. Experience at Uber, Airbnb startups.",
        "skills": ["Growth Marketing", "Quick Decision Making", "Startup Experience", "Team Building"],
        "behavior": {
            "first_decision_range": (5, 12),   # seconds - fast, intuitive
            "option_changes_range": (2, 4),    # explores options
            "explanation_words_range": (10, 20),  # brief
            "explanation_has_keywords": False,
            "risk_preference": "mixed",        # varied risk choices
            "paste_events": 0,
            "focus_losses": 0,
            "long_idles": 0,
            "timing_variance": "high",
        }
    },
    {
        "name": "Test Candidate",
        "email": "test.candidate@demo.hiremate.ai",
        "position": "Software Engineer",
        "profile_type": "suspicious",
        "resume_text": "Software developer with 3 years experience. Proficient in Python and JavaScript.",
        "skills": ["Python", "JavaScript", "Web Development"],
        "behavior": {
            "first_decision_range": (7.8, 8.2),  # very uniform timing (suspicious)
            "option_changes_range": (0, 0),      # never changes
            "explanation_words_range": (5, 10),  # minimal
            "explanation_has_keywords": False,
            "risk_preference": "low",
            "paste_events": 3,         # 3 paste detections
            "focus_losses": 5,         # 5 tab switches
            "long_idles": 2,           # 2 long pauses (35+ seconds)
            "timing_variance": "low",  # robotic consistency
        }
    }
]

# Logical keywords for analytical explanations
LOGICAL_KEYWORDS = [
    "because", "therefore", "however", "although", "considering",
    "firstly", "secondly", "finally", "moreover", "furthermore"
]

# Sample explanations for different profiles
ANALYTICAL_EXPLANATIONS = [
    "I chose this option because it provides the best balance between risk and reward. Considering the constraints mentioned, this approach minimizes potential issues while still achieving the core objective. Furthermore, it allows for flexibility if circumstances change.",
    "After carefully analyzing all options, I believe this is optimal because it addresses both immediate needs and long-term considerations. However, I acknowledge there are trade-offs involved that would need monitoring.",
    "This decision is based on weighing multiple factors. Firstly, it aligns with standard best practices. Secondly, it accounts for stakeholder concerns. Therefore, despite some uncertainty, this represents the most balanced approach.",
    "Considering the scenario constraints, this option offers the strongest risk-to-benefit ratio. Although other options have merit, this one provides a more sustainable path forward. Moreover, it builds on proven approaches.",
    "I selected this because it represents a thoughtful middle ground. While aggressive options might yield faster results, the potential downsides outweigh the benefits. Therefore, this measured approach is preferable."
]

EXPLORATORY_EXPLANATIONS = [
    "Went with gut feeling here - seems right.",
    "This feels like the best option given time constraints.",
    "Quick decision - this covers the main points.",
    "Picked this one after scanning all options.",
    "Simplest path forward, should work fine."
]

SUSPICIOUS_EXPLANATIONS = [
    "Option selected.",
    "This is my choice.",
    "Selected option A.",
    "Chose this one.",
    "My selection."
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_explanation(profile_type: str, has_keywords: bool) -> str:
    """Generate an explanation based on profile type."""
    if profile_type == "analytical":
        return random.choice(ANALYTICAL_EXPLANATIONS)
    elif profile_type == "exploratory":
        return random.choice(EXPLORATORY_EXPLANATIONS)
    else:  # suspicious
        return random.choice(SUSPICIOUS_EXPLANATIONS)


def generate_events_for_task(
    attempt_id: ObjectId,
    task_id: str,
    task_index: int,
    behavior: dict,
    task_start_time: datetime,
    options: list,
    start_sequence: int = 0
) -> tuple:
    """
    Generate a realistic event stream for one task.
    Returns (list of events, task completion time, selected option, final_sequence).
    """
    events = []
    current_time = task_start_time
    sequence = start_sequence
    
    profile_type = behavior.get("profile_type", "normal")
    
    # Determine timing variance
    if behavior.get("timing_variance") == "low":
        # Suspicious: very uniform timing
        jitter = 0.1
    else:
        # Normal: human variance
        jitter = 3.0
    
    # 1. TASK_STARTED
    events.append({
        "_id": ObjectId(),
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": "task_started",
        "timestamp": current_time,
        "sequence_number": sequence,
        "payload": {"task_index": task_index},
        "client_timestamp": current_time,
    })
    sequence += 1
    current_time += timedelta(milliseconds=random.randint(100, 500))
    
    # 2. OPTION_VIEWED (view some options)
    options_to_view = random.sample(options, min(3, len(options)))
    for opt in options_to_view:
        view_duration = random.randint(1000, 4000)
        events.append({
            "_id": ObjectId(),
            "attempt_id": attempt_id,
            "task_id": task_id,
            "event_type": "option_viewed",
            "timestamp": current_time,
            "sequence_number": sequence,
            "payload": {"option_id": opt["id"], "view_duration_ms": view_duration},
            "client_timestamp": current_time,
        })
        sequence += 1
        current_time += timedelta(milliseconds=view_duration + random.randint(200, 800))
    
    # 3. First OPTION_SELECTED
    first_decision_min, first_decision_max = behavior["first_decision_range"]
    if behavior.get("timing_variance") == "low":
        first_decision_time = (first_decision_min + first_decision_max) / 2
    else:
        first_decision_time = random.uniform(first_decision_min, first_decision_max)
    
    # Select based on risk preference
    risk_pref = behavior["risk_preference"]
    if risk_pref == "low":
        selected_option = next((o for o in options if o.get("risk_level") == "low"), options[0])
    elif risk_pref == "high":
        selected_option = next((o for o in options if o.get("risk_level") == "high"), options[-1])
    else:  # mixed
        selected_option = random.choice(options)
    
    current_time = task_start_time + timedelta(seconds=first_decision_time)
    events.append({
        "_id": ObjectId(),
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": "option_selected",
        "timestamp": current_time,
        "sequence_number": sequence,
        "payload": {"option_id": selected_option["id"], "is_first_selection": True},
        "client_timestamp": current_time,
    })
    sequence += 1
    
    # 4. OPTION_CHANGED (if profile explores)
    changes_min, changes_max = behavior["option_changes_range"]
    num_changes = random.randint(changes_min, changes_max)
    
    for _ in range(num_changes):
        current_time += timedelta(seconds=random.uniform(2, 5))
        prev_option = selected_option
        available = [o for o in options if o["id"] != selected_option["id"]]
        if available:
            selected_option = random.choice(available)
            events.append({
                "_id": ObjectId(),
                "attempt_id": attempt_id,
                "task_id": task_id,
                "event_type": "option_changed",
                "timestamp": current_time,
                "sequence_number": sequence,
                "payload": {
                    "from_option_id": prev_option["id"],
                    "to_option_id": selected_option["id"],
                    "time_since_last_change_ms": random.randint(2000, 5000)
                },
                "client_timestamp": current_time,
            })
            sequence += 1
    
    # 5. FOCUS_LOST events (for suspicious profile)
    for i in range(behavior.get("focus_losses", 0)):
        focus_time = current_time + timedelta(seconds=random.uniform(1, 3))
        events.append({
            "_id": ObjectId(),
            "attempt_id": attempt_id,
            "task_id": task_id,
            "event_type": "focus_lost",
            "timestamp": focus_time,
            "sequence_number": sequence,
            "payload": {"trigger": "tab_switch"},
            "client_timestamp": focus_time,
        })
        sequence += 1
        
        # Focus gained after 2-8 seconds
        events.append({
            "_id": ObjectId(),
            "attempt_id": attempt_id,
            "task_id": task_id,
            "event_type": "focus_gained",
            "timestamp": focus_time + timedelta(seconds=random.uniform(2, 8)),
            "sequence_number": sequence,
            "payload": {"trigger": "tab_switch"},
            "client_timestamp": focus_time,
        })
        sequence += 1
    
    # 6. IDLE_DETECTED (long idles for suspicious)
    for i in range(behavior.get("long_idles", 0)):
        idle_time = current_time + timedelta(seconds=random.uniform(5, 15))
        events.append({
            "_id": ObjectId(),
            "attempt_id": attempt_id,
            "task_id": task_id,
            "event_type": "idle_detected",
            "timestamp": idle_time,
            "sequence_number": sequence,
            "payload": {"idle_duration_ms": 35000 + random.randint(0, 10000), "last_activity_type": "option_selected"},
            "client_timestamp": idle_time,
        })
        sequence += 1
    
    # 7. REASONING events
    current_time += timedelta(seconds=random.uniform(3, 8))
    events.append({
        "_id": ObjectId(),
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": "reasoning_started",
        "timestamp": current_time,
        "sequence_number": sequence,
        "payload": {"time_since_task_start_ms": int((current_time - task_start_time).total_seconds() * 1000)},
        "client_timestamp": current_time,
    })
    sequence += 1
    
    # Generate explanation
    explanation = generate_explanation(
        behavior.get("profile_type", "normal"),
        behavior.get("explanation_has_keywords", False)
    )
    word_count = len(explanation.split())
    
    # PASTE_DETECTED events (for suspicious)
    for i in range(behavior.get("paste_events", 0)):
        paste_time = current_time + timedelta(seconds=random.uniform(0.5, 2))
        events.append({
            "_id": ObjectId(),
            "attempt_id": attempt_id,
            "task_id": task_id,
            "event_type": "paste_detected",
            "timestamp": paste_time,
            "sequence_number": sequence,
            "payload": {"char_count": random.randint(50, 200), "source": "reasoning"},
            "client_timestamp": paste_time,
        })
        sequence += 1
    
    current_time += timedelta(seconds=random.uniform(10, 30))
    events.append({
        "_id": ObjectId(),
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": "reasoning_submitted",
        "timestamp": current_time,
        "sequence_number": sequence,
        "payload": {
            "final_text": explanation,
            "word_count": word_count,
            "character_count": len(explanation)
        },
        "client_timestamp": current_time,
    })
    sequence += 1
    
    # 8. TASK_COMPLETED
    current_time += timedelta(seconds=random.uniform(1, 3))
    task_duration_ms = int((current_time - task_start_time).total_seconds() * 1000)
    events.append({
        "_id": ObjectId(),
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": "task_completed",
        "timestamp": current_time,
        "sequence_number": sequence,
        "payload": {
            "final_option_id": selected_option["id"],
            "task_duration_ms": task_duration_ms
        },
        "client_timestamp": current_time,
    })
    
    return events, current_time, selected_option, sequence + 1


# ============================================================================
# MAIN SEED FUNCTION
# ============================================================================

async def seed_demo_candidates():
    """Seed demo candidates with completed assessments."""
    print(f"Connecting to MongoDB: {MONGODB_URL}")
    print(f"Database: {MONGODB_DATABASE}")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    
    # Verify connection
    await client.admin.command("ping")
    print("[OK] Connected to MongoDB")
    
    # Get collections
    attempts_coll = db.task_attempts
    events_coll = db.behavior_events
    tasks_coll = db.tasks
    users_coll = db.users
    
    # Get or create demo recruiter
    recruiter = await users_coll.find_one({"email": DEMO_RECRUITER_EMAIL})
    if not recruiter:
        print(f"[!] Demo recruiter not found. Using 'system' as created_by.")
        recruiter_id = "system"
    else:
        recruiter_id = str(recruiter["_id"])
        print(f"[OK] Found demo recruiter: {recruiter_id}")
    
    # Get available tasks
    tasks = await tasks_coll.find({"is_active": True}).to_list(length=10)
    if not tasks:
        print("[ERROR] No tasks found. Run seed_tasks.py first.")
        return
    
    task_ids = [str(t["_id"]) for t in tasks[:5]]  # Use first 5 tasks
    print(f"[OK] Found {len(task_ids)} tasks for assessment")
    
    # Delete existing demo candidates
    demo_emails = [c["email"] for c in DEMO_CANDIDATES]
    existing = await attempts_coll.count_documents({"candidate_info.email": {"$in": demo_emails}})
    if existing > 0:
        print(f"[!] Deleting {existing} existing demo attempts...")
        
        # Get attempt IDs to delete events
        existing_attempts = await attempts_coll.find(
            {"candidate_info.email": {"$in": demo_emails}}
        ).to_list(length=100)
        
        for att in existing_attempts:
            await events_coll.delete_many({"attempt_id": att["_id"]})
        
        await attempts_coll.delete_many({"candidate_info.email": {"$in": demo_emails}})
        print("[OK] Deleted existing demo data")
    
    # Create demo candidates
    created = 0
    for candidate in DEMO_CANDIDATES:
        print(f"\n[+] Creating: {candidate['name']} ({candidate['profile_type']})")
        
        attempt_id = ObjectId()
        now = datetime.utcnow()
        assessment_start = now - timedelta(minutes=random.randint(30, 120))
        
        # Create attempt document
        attempt_doc = {
            "_id": attempt_id,
            "token": f"demo-{candidate['profile_type']}-{str(attempt_id)[:8]}",
            "candidate_info": {
                "name": candidate["name"],
                "email": candidate["email"],
                "position": candidate["position"],
                "resume_text": candidate.get("resume_text", ""),
                "skills": candidate.get("skills", []),
            },
            "task_ids": task_ids,
            "status": "completed",
            "created_by": recruiter_id,
            "started_at": assessment_start,
            "completed_at": None,  # Will update after events
            "expires_at": now + timedelta(days=7),
            "current_task_index": len(task_ids),
            "created_at": assessment_start - timedelta(minutes=5),
            "updated_at": now,
            "is_demo": True,  # Mark as demo data
        }
        
        # Generate events for each task
        all_events = []
        current_time = assessment_start
        behavior = candidate["behavior"].copy()
        behavior["profile_type"] = candidate["profile_type"]
        global_sequence = 0  # Track sequence across all tasks
        
        for i, task_id in enumerate(task_ids):
            task = next((t for t in tasks if str(t["_id"]) == task_id), None)
            if not task:
                continue
            
            options = task.get("options", [])
            
            task_events, end_time, _, global_sequence = generate_events_for_task(
                attempt_id=attempt_id,
                task_id=task_id,
                task_index=i,
                behavior=behavior,
                task_start_time=current_time,
                options=options,
                start_sequence=global_sequence
            )
            
            all_events.extend(task_events)
            current_time = end_time + timedelta(seconds=random.uniform(2, 5))
        
        # Update completion time
        attempt_doc["completed_at"] = current_time
        
        # Insert attempt
        await attempts_coll.insert_one(attempt_doc)
        print(f"    → Created attempt: {attempt_id}")
        
        # Insert events
        if all_events:
            await events_coll.insert_many(all_events)
            print(f"    → Created {len(all_events)} events")
        
        # Summarize behavior flags
        paste_count = behavior.get("paste_events", 0)
        focus_count = behavior.get("focus_losses", 0)
        idle_count = behavior.get("long_idles", 0)
        
        if paste_count > 0 or focus_count > 0:
            print(f"    → Anti-cheat flags: {paste_count} pastes, {focus_count} focus losses, {idle_count} long idles")
        else:
            print(f"    → Clean behavior: No anti-cheat flags")
        
        created += 1
    
    print(f"\n[DONE] Created {created} demo candidates")
    print("\n=== DEMO CANDIDATES READY ===")
    print("Open the Recruiter Dashboard to see:")
    print("  • Sarah Chen → Analytical Thinker (High Fit)")
    print("  • Mike Johnson → Exploratory Thinker (Moderate Fit)")
    print("  • Test Candidate → Suspicious Activity (Low Fit, Anti-Cheat Flags)")
    print("="*40)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_candidates())
