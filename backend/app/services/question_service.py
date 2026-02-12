"""
Question Generation Service

Generates tailored interview questions based on candidate resume and skills using Groq AI.
"""

import json
import re
from typing import List, Dict, Any
from groq import Groq
from app.config import get_settings
from app.schemas.task import TaskCreate, TaskCategory, TaskDifficulty, TaskOption, RiskLevel

async def generate_questions_from_resume(resume_text: str, skills: List[str], num_questions: int = 10) -> List[TaskCreate]:
    """
    Generate behavioral/technical questions based on resume context.
    """
    api_key = get_settings().groq_api_key
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    client = Groq(api_key=api_key)
    
    # Construct a rich prompt
    skills_str = ", ".join(skills) if skills else "General Professional Skills"
    
    prompt = f"""
    You are an expert technical interviewer at a top-tier tech company. Create {num_questions} multiple-choice scenario-based questions to assess a candidate with the following profile:
    
    Skills: {skills_str}
    Resume Excerpt:
    {resume_text[:2000]}...
    
    GUIDELINES:
    1. **Readability is Key**: Use simple, professional English. Short sentences. No complex jargon unless technical.
    2. **Scenario-Based**: Each question must describe a specific, realistic workplace situation (1-2 sentences max).
    3. **Bluff Detection**: Questions should test *depth* of understanding. Avoid surface-level definition questions. Ask "What would you do if..." or "Why did this fail...".
    4. **Distinct Options**: Options must be clearly different. One is the "best" (low risk), others show varying degrees of bad judgment (medium/high risk).
    
    For each question, provide:
    - "title": A short, catchy title (e.g., "Database Latency").
    - "scenario": The situation (e.g., "Production is down due to High CPU...").
    - "question": (Optional) The specific question to ask. If omitted, implied by options.
    - "category": One of [problem_solving, communication, decision_confidence, analytical_thinking, speed_accuracy].
    - "difficulty": [easy, medium, hard].
    - "options": Exactly 3 options. One low risk (best answer), one medium risk, one high risk.
       - "text": The answer text.
       - "risk_level": [low, medium, high]. 'low' is the best answer.
    
    Return ONLY a JSON array of objects.
    """

    try:
        settings = get_settings()
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only API. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model=settings.ai_model_120b,
            response_format={"type": "json_object"},
            temperature=0.6,
        )
        
        content = completion.choices[0].message.content
        # Extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        data = json.loads(content)
        
        # Handle if wrapped in a key like "questions": [...]
        questions_data = data if isinstance(data, list) else data.get("questions", [])
        
        tasks = []
        for q in questions_data:
            # Map strings to Enums to ensure validation
            try:
                category = TaskCategory(q.get("category", "problem_solving").lower())
            except ValueError:
                category = TaskCategory.PROBLEM_SOLVING
                
            try:
                difficulty = TaskDifficulty(q.get("difficulty", "medium").lower())
            except ValueError:
                difficulty = TaskDifficulty.MEDIUM
                
            options = []
            for i, opt in enumerate(q.get("options", [])):
                try:
                    risk = RiskLevel(opt.get("risk_level", "medium").lower())
                except ValueError:
                    risk = RiskLevel.MEDIUM
                    
                options.append(TaskOption(
                    id=f"opt_{i+1}",
                    text=opt.get("text", "Option text"),
                    risk_level=risk
                ))
            
            # Ensure we have 3 options
            while len(options) < 3:
                options.append(TaskOption(id=f"opt_{len(options)+1}", text="N/A", risk_level=RiskLevel.HIGH))
                
            # Determine time limit based on difficulty
            TIME_LIMITS = {
                "easy": 90,
                "medium": 120,
                "hard": 150
            }
            time_limit = TIME_LIMITS.get(difficulty.value, 120)
            
            task = TaskCreate(
                title=q.get("title", "Interview Question")[:100],
                scenario=q.get("scenario", "Scenario")[:2000],
                category=category,
                difficulty=difficulty,
                options=options,
                reasoning_required=True,
                reasoning_min_length=20,
                time_limit_seconds=time_limit
            )
            tasks.append(task)
            
            tasks.append(task)
            
        if not tasks:
            print("[ERROR] AI returned empty list of tasks/questions")
            raise ValueError("AI returned 0 questions")
            
        print(f"[INFO] Successfully generated {len(tasks)} tasks from AI")
        return tasks

    except Exception as e:
        print(f"[ERROR] Question generation failed: {e}")
        import traceback
        traceback.print_exc()
        # Return static fallback questions so assessment is not empty
        print("[INFO] Using fallback questions due to AI error")
        from app.schemas.task import TaskCreate, TaskCategory, TaskDifficulty, TaskOption, RiskLevel
        
        fallback_tasks = [
            TaskCreate(
                title="Challenge Resolution",
                scenario="Describe a specific situation where you faced a significant technical challenge or blocker.",
                category=TaskCategory.PROBLEM_SOLVING,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I analyzed the root cause, researched solutions, and implemented a fix.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I asked a senior team member to fix it for me.", risk_level=RiskLevel.MEDIUM),
                    TaskOption(id="opt_3", text="I ignored the issue and worked on something else.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Conflict Management",
                scenario="You disagree with a coworker about the implementation of a feature. How do you handle it?",
                category=TaskCategory.COMMUNICATION,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I schedule a discussion to understand their perspective and find a compromise.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I report them to the manager immediately.", risk_level=RiskLevel.HIGH),
                    TaskOption(id="opt_3", text="I just do it my way without telling them.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
             TaskCreate(
                title="Learning New Tech",
                scenario="You are required to use a new framework you have never used before. What is your approach?",
                category=TaskCategory.ANALYTICAL_THINKING,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I read the documentation and build a small prototype to learn.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I copy-paste code from StackOverflow without understanding it.", risk_level=RiskLevel.HIGH),
                    TaskOption(id="opt_3", text="I say I cannot do the task.", risk_level=RiskLevel.MEDIUM)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
             TaskCreate(
                title="Deadline Pressure",
                scenario="You realize you will not be able to meet a deadline for a critical deliverable.",
                category=TaskCategory.DECISION_CONFIDENCE,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I communicate early to stakeholders and propose a revised timeline or scope.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I work 24 hours a day to try to finish.", risk_level=RiskLevel.MEDIUM),
                    TaskOption(id="opt_3", text="I don't say anything and hope nobody notices.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Ambiguous Requirements",
                scenario="You receive a task with very vague requirements. What do you do?",
                category=TaskCategory.ANALYTICAL_THINKING,
                difficulty=TaskDifficulty.HARD,
                options=[
                    TaskOption(id="opt_1", text="I ask clarifying questions to the stakeholders to define the scope.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I make assumptions and build what I think is right.", risk_level=RiskLevel.MEDIUM),
                    TaskOption(id="opt_3", text="I wait until someone gives me better instructions.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Customer Feedback",
                scenario="A customer reports a critical bug in production, but you are working on a new feature.",
                category=TaskCategory.COMMUNICATION,
                difficulty=TaskDifficulty.HARD,
                options=[
                    TaskOption(id="opt_1", text="I investigate the bug immediately to assess severity and fix if critical.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I finish my feature first because it is important.", risk_level=RiskLevel.HIGH),
                    TaskOption(id="opt_3", text="I tell the customer to file a ticket and wait.", risk_level=RiskLevel.MEDIUM)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Production Bug",
                scenario="You deployed code that caused a minor bug in production. No one has noticed yet.",
                category=TaskCategory.SPEED_ACCURACY,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I create a fix/hotfix and deploy it immediately.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I hope no one notices and fix it later.", risk_level=RiskLevel.HIGH),
                    TaskOption(id="opt_3", text="I blame it on a deployed library.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Mentoring Junior",
                scenario="A junior developer keeps making the same mistake in their code.",
                category=TaskCategory.COMMUNICATION,
                difficulty=TaskDifficulty.MEDIUM,
                options=[
                    TaskOption(id="opt_1", text="I pair program with them to explain the concept and best practices.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I fix their code for them every time.", risk_level=RiskLevel.MEDIUM),
                    TaskOption(id="opt_3", text="I complain about them to the manager.", risk_level=RiskLevel.HIGH)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Legacy Code Refactor",
                scenario="You encounter a piece of messy legacy code that is hard to understand but works.",
                category=TaskCategory.PROBLEM_SOLVING,
                difficulty=TaskDifficulty.HARD,
                options=[
                    TaskOption(id="opt_1", text="I write tests for it first, then refactor it incrementally.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I rewrite the entire thing from scratch.", risk_level=RiskLevel.MEDIUM),
                    TaskOption(id="opt_3", text="I leave it alone and add more code on top.", risk_level=RiskLevel.MEDIUM)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            ),
            TaskCreate(
                title="Feature Prioritization",
                scenario="You have two important features to build but only enough time for one.",
                category=TaskCategory.DECISION_CONFIDENCE,
                difficulty=TaskDifficulty.HARD,
                options=[
                    TaskOption(id="opt_1", text="I discuss with the product manager to prioritize based on business value.", risk_level=RiskLevel.LOW),
                    TaskOption(id="opt_2", text="I try to do both and end up finishing neither.", risk_level=RiskLevel.HIGH),
                    TaskOption(id="opt_3", text="I pick the one I like more.", risk_level=RiskLevel.MEDIUM)
                ],
                reasoning_required=True,
                reasoning_min_length=50,
                time_limit_seconds=120
            )
        ]
        return fallback_tasks
