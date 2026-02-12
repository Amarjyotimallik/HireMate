import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
import joblib
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import get_settings

async def extract_features(db):
    """
    Extract features from all attempts in the database.
    """
    attempts_coll = db["task_attempts"]
    events_coll = db["behavior_events"]
    
    features_list = []
    attempt_ids = []
    
    async for attempt in attempts_coll.find({"status": "completed"}):
        attempt_id = str(attempt["_id"])
        
        # Get events for this attempt
        cursor = events_coll.find({
            "$or": [
                {"attempt_id": attempt_id},
                {"attempt_id": ObjectId(attempt_id)}
            ]
        }).sort("sequence_number", 1)
        events = await cursor.to_list(length=10000)
        
        if not events:
            continue
            
        # Feature extraction
        feature = compute_attempt_features(events)
        features_list.append(feature)
        attempt_ids.append(attempt_id)
        
    return pd.DataFrame(features_list), attempt_ids

def compute_attempt_features(events):
    """
    Compute raw feature vector from an event sequence.
    """
    total_events = len(events)
    
    # Event types counts
    counts = {
        "paste_count": 0,
        "focus_lost_count": 0,
        "copy_count": 0,
        "idle_count": 0,
        "option_changed_count": 0
    }
    
    for e in events:
        etype = e.get("event_type")
        if etype == "paste_detected": counts["paste_count"] += 1
        elif etype == "focus_lost": counts["focus_lost_count"] += 1
        elif etype == "copy_detected": counts["copy_count"] += 1
        elif etype == "idle_detected": counts["idle_count"] += 1
        elif etype == "option_changed": counts["option_changed_count"] += 1

    # Time-based features
    times = []
    for i in range(1, len(events)):
        try:
            prev_ts = events[i-1].get("timestamp")
            curr_ts = events[i].get("timestamp")
            if prev_ts and curr_ts:
                diff = (curr_ts - prev_ts).total_seconds()
                times.append(diff)
        except:
            pass
            
    avg_gap = np.mean(times) if times else 0
    std_gap = np.std(times) if times else 0
    cv_gap = std_gap / avg_gap if avg_gap > 0 else 0
    
    # Unique tasks
    unique_tasks = len(set([str(e.get("task_id")) for e in events if e.get("task_id")]))
    
    return {
        "paste_rate": counts["paste_count"] / max(1, unique_tasks),
        "focus_rate": counts["focus_lost_count"] / max(1, unique_tasks),
        "copy_rate": counts["copy_count"] / max(1, unique_tasks),
        "idle_rate": counts["idle_count"] / max(1, unique_tasks),
        "revision_rate": counts["option_changed_count"] / max(1, unique_tasks),
        "avg_gap": avg_gap,
        "cv_gap": cv_gap,
        "event_density": total_events / max(1, unique_tasks)
    }

def generate_synthetic_data(num_samples=50):
    """
    Generate synthetic data for 'normal' behavior to augment small datasets.
    Creates both normal and some anomalous patterns for better training.
    """
    samples = []
    
    # 80% Normal behavior (honest candidates)
    num_normal = int(num_samples * 0.8)
    for _ in range(num_normal):
        samples.append({
            "paste_rate": np.random.uniform(0, 0.2),      # Low pasting
            "focus_rate": np.random.uniform(0, 1.5),      # Some tab switches
            "copy_rate": np.random.uniform(0, 0.1),       # Minimal copying
            "idle_rate": np.random.uniform(0.5, 2.0),     # Natural pauses
            "revision_rate": np.random.uniform(0.5, 3.0), # Regular revisions
            "avg_gap": np.random.uniform(5, 15),          # Normal thinking time
            "cv_gap": np.random.uniform(1.5, 4.0),        # Natural variation
            "event_density": np.random.uniform(20, 50)    # Engaged behavior
        })
    
    # 20% Anomalous behavior (suspicious patterns)
    num_anomalous = num_samples - num_normal
    for _ in range(num_anomalous):
        # Random anomaly type
        anomaly_type = np.random.choice(['paster', 'switcher', 'rusher'])
        
        if anomaly_type == 'paster':
            # High paste rate, low variation
            samples.append({
                "paste_rate": np.random.uniform(1.0, 3.0),    # Lots of pasting!
                "focus_rate": np.random.uniform(0, 0.5),
                "copy_rate": np.random.uniform(0, 0.2),
                "idle_rate": np.random.uniform(0.1, 0.5),
                "revision_rate": np.random.uniform(0, 0.3),   # Few revisions
                "avg_gap": np.random.uniform(2, 5),           # Fast
                "cv_gap": np.random.uniform(0.3, 1.0),        # Low variation (robotic)
                "event_density": np.random.uniform(15, 30)
            })
        elif anomaly_type == 'switcher':
            # Lots of tab switching (looking things up)
            samples.append({
                "paste_rate": np.random.uniform(0, 0.5),
                "focus_rate": np.random.uniform(3.0, 6.0),    # Many tab switches!
                "copy_rate": np.random.uniform(0.5, 2.0),     # Copying questions
                "idle_rate": np.random.uniform(1.0, 3.0),
                "revision_rate": np.random.uniform(0.2, 1.0),
                "avg_gap": np.random.uniform(8, 20),          # Slow (researching)
                "cv_gap": np.random.uniform(2.0, 5.0),
                "event_density": np.random.uniform(25, 45)
            })
        else:  # rusher
            # Too fast, no thought (pre-written answers)
            samples.append({
                "paste_rate": np.random.uniform(0.5, 1.5),
                "focus_rate": np.random.uniform(0, 1.0),
                "copy_rate": np.random.uniform(0, 0.2),
                "idle_rate": np.random.uniform(0.1, 0.5),     # No pausing
                "revision_rate": np.random.uniform(0, 0.2),   # No revisions
                "avg_gap": np.random.uniform(1, 3),           # Very fast!
                "cv_gap": np.random.uniform(0.2, 0.8),        # Very consistent (sus)
                "event_density": np.random.uniform(10, 25)
            })
        
    return pd.DataFrame(samples)

async def train():
    print("🚀 Starting Behavioral Anomaly Model Training...")
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    # 1. Extract real data
    real_df, _ = await extract_features(db)
    print(f"✅ Extracted features from {len(real_df)} real candidates.")
    
    # 2. Augment with synthetic "normal" data
    synthetic_df = generate_synthetic_data(100)
    train_df = pd.concat([real_df, synthetic_df], ignore_index=True)
    
    # 3. Train Isolation Forest
    # contamination=0.1 means we expect roughly 10% of candidates to be anomalous
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(train_df)
    
    # 4. Save model
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "behavioral_anomaly_model.joblib")
    
    joblib.dump(model, model_path)
    print(f"🎯 Model trained and saved to: {model_path}")
    
    # Save feature names for reference in detection
    feature_names_path = os.path.join(model_dir, "feature_names.joblib")
    joblib.dump(list(train_df.columns), feature_names_path)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(train())
