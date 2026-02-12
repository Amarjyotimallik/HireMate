"""
Interview success probability predictor.
Uses behavioral metrics (+ optional ATS/resume) to predict likelihood of interview success.
Formula-based for hackathon (no training data); can be replaced with XGBoost when labels exist.
"""


import os
import pickle
import pandas as pd
from typing import Dict, Any, List

# --- ML Model Configuration ---
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_models", "interview_model.pkl")
ML_MODEL = None

try:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            ML_MODEL = pickle.load(f)
        print(f"[ML] Successfully loaded random forest model from {MODEL_PATH}")
    else:
        print(f"[ML-WARNING] Model file not found at {MODEL_PATH}. Using heuristic fallback.")
except Exception as e:
    print(f"[ML-ERROR] Failed to load model: {e}. Using heuristic fallback.")

# Weights for formula (fallback) or blending
WEIGHTS = {
    "decision_firmness": 0.25,
    "reasoning_depth": 0.25,
    "completion_rate": 0.20,
    "attention_stability": 0.15,
    "decision_consistency": 0.15,
}
# Optional resume component
ATS_WEIGHT = 0.20  # Blend: 80% behavioral + 20% ATS

def predict(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Predict interview success probability using Random Forest (if available) or Heuristic Formula.
    """
    # 1. Normalize Features (0-100 scale)
    firmness = max(0.0, min(100.0, float(features.get("decision_firmness", 50.0))))
    reasoning = max(0.0, min(100.0, float(features.get("reasoning_depth", 50.0))))
    completion = max(0.0, min(1.0, float(features.get("completion_rate", 0.5)))) * 100.0
    stability = max(0.0, min(1.0, float(features.get("attention_stability", 0.5)))) * 100.0
    consistency = max(0.0, min(1.0, float(features.get("decision_consistency", 0.5)))) * 100.0
    ats_score = features.get("ats_score")

    # 2. ML Prediction (Primary)
    ml_probability = 0.0
    used_model = False
    
    if ML_MODEL:
        try:
            # Create dataframe matching training format
            input_df = pd.DataFrame([{
                'decision_firmness': firmness,
                'reasoning_depth': reasoning,
                'completion_rate': completion,
                'attention_stability': stability,
                'decision_consistency': consistency
            }])
            ml_probability = float(ML_MODEL.predict(input_df)[0])
            used_model = True
        except Exception as e:
            print(f"[ML-ERROR] Prediction failed: {e}. Falling back to formula.")

    # 3. Heuristic Fallback (Secondary)
    if not used_model:
        ml_probability = (
            WEIGHTS["decision_firmness"] * firmness +
            WEIGHTS["reasoning_depth"] * reasoning +
            WEIGHTS["completion_rate"] * completion +
            WEIGHTS["attention_stability"] * stability +
            WEIGHTS["decision_consistency"] * consistency
        )

    # 4. Blend with ATS (if present)
    if ats_score is not None:
        ats_score = max(0.0, min(100.0, float(ats_score)))
        final_probability = ml_probability * (1.0 - ATS_WEIGHT) + ats_score * ATS_WEIGHT
    else:
        final_probability = ml_probability

    # 5. Determine Confidence
    num_tasks = max(1, int(features.get("total_tasks", 5)))
    tasks_done = int(features.get("tasks_completed", 0))
    if tasks_done >= num_tasks and num_tasks >= 3:
        confidence = "high"
    elif tasks_done >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    # 6. Explainable Factors
    factors: List[Dict[str, Any]] = [
        {"name": "decision_firmness", "value": round(firmness, 1), "weight": WEIGHTS["decision_firmness"]},
        {"name": "reasoning_depth", "value": round(reasoning, 1), "weight": WEIGHTS["reasoning_depth"]},
        {"name": "completion_rate", "value": round(completion, 1), "weight": WEIGHTS["completion_rate"]},
        {"name": "attention_stability", "value": round(stability, 1), "weight": WEIGHTS["attention_stability"]},
        {"name": "decision_consistency", "value": round(consistency, 1), "weight": WEIGHTS["decision_consistency"]},
    ]
    if ats_score is not None:
        factors.append({"name": "ats_score", "value": round(ats_score, 1), "weight": ATS_WEIGHT})

    return {
        "probability": round(min(100.0, max(0.0, final_probability)), 1),
        "confidence": confidence,
        "factors": factors,
        "model_used": "RandomForest" if used_model else "Heuristic"
    }
