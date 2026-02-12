import os
import joblib
import numpy as np
import pandas as pd
import ollama
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Model paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "behavioral_anomaly_model.joblib")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_names.joblib")

class MLAnomalyDetector:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
                self.model = joblib.load(MODEL_PATH)
                self.feature_names = joblib.load(FEATURES_PATH)
                logger.info(f"✅ ML Anomaly Model loaded successfully from {MODEL_PATH}")
            else:
                logger.warning(f"⚠️ ML Anomaly Model not found at {MODEL_PATH}. Please run the training script.")
        except Exception as e:
            logger.error(f"❌ Failed to load ML Anomaly Model: {e}")
    
    def ensure_loaded(self):
        """Retry loading if model wasn't loaded initially."""
        if not self.model and os.path.exists(MODEL_PATH):
            logger.info("🔄 Retrying model load...")
            self._load_model()


    def compute_interaction_entropy(self, events: List[Dict]) -> float:
        """
        Calculate interaction entropy - measures unpredictability of behavior.
        Higher entropy = more natural/varied behavior (harder to game).
        Lower entropy = robotic/predictable patterns (suspicious).
        """
        if len(events) < 5:
            return 0.0
        
        # Extract revision events (option_changed)
        revision_events = [e for e in events if e.get("event_type") == "option_changed"]
        if len(revision_events) < 3:
            return 0.0
        
        # Calculate time intervals between revisions
        intervals = []
        for i in range(1, len(revision_events)):
            try:
                t1 = revision_events[i-1].get("timestamp")
                t2 = revision_events[i].get("timestamp")
                
                if isinstance(t1, str): t1 = datetime.fromisoformat(t1.replace('Z', '+00:00'))
                if isinstance(t2, str): t2 = datetime.fromisoformat(t2.replace('Z', '+00:00'))
                
                if t1 and t2:
                    intervals.append((t2 - t1).total_seconds())
            except:
                pass
        
        if not intervals:
            return 0.0
        
        # Bin intervals into discrete categories for entropy calculation
        # Bins: 0-5s, 5-15s, 15-30s, 30-60s, 60+s
        bins = [0, 5, 15, 30, 60, float('inf')]
        histogram = [0] * (len(bins) - 1)
        
        for interval in intervals:
            for i in range(len(bins) - 1):
                if bins[i] <= interval < bins[i+1]:
                    histogram[i] += 1
                    break
        
        # Calculate Shannon entropy
        total = sum(histogram)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in histogram:
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return entropy
    
    def compute_confidence_level(self, num_questions: int, num_events: int) -> tuple:
        """
        Calculate confidence level based on sample size.
        Returns (level_name, confidence_score, reliability_note)
        """
        if num_questions < 3:
            return "preliminary", 0.3, "Limited data - preliminary assessment only"
        elif num_questions < 7:
            return "moderate", 0.7, f"Based on {num_questions} questions - moderate confidence"
        else:
            return "stable", 0.95, f"Based on {num_questions} questions - stable behavioral signal"
    
    def compute_features(self, events: List[Dict]) -> Dict:
        """
        Extract same features used during training.
        """
        if not events:
            return {}
            
        total_events = len(events)
        unique_tasks = len(set([str(e.get("task_id")) for e in events if e.get("task_id")]))
        
        counts = {
            "paste_count": sum(1 for e in events if e.get("event_type") == "paste_detected"),
            "focus_lost_count": sum(1 for e in events if e.get("event_type") == "focus_lost"),
            "copy_count": sum(1 for e in events if e.get("event_type") == "copy_detected"),
            "idle_count": sum(1 for e in events if e.get("event_type") == "idle_detected"),
            "revision_rate": sum(1 for e in events if e.get("event_type") == "option_changed")
        }

        times = []
        for i in range(1, len(events)):
            try:
                # Handle both datetime objects and string timestamps
                t1 = events[i-1].get("timestamp")
                t2 = events[i].get("timestamp")
                
                if isinstance(t1, str): t1 = datetime.fromisoformat(t1.replace('Z', '+00:00'))
                if isinstance(t2, str): t2 = datetime.fromisoformat(t2.replace('Z', '+00:00'))
                
                if t1 and t2:
                    times.append((t2 - t1).total_seconds())
            except:
                pass
                
        avg_gap = np.mean(times) if times else 0
        std_gap = np.std(times) if times else 0
        cv_gap = std_gap / avg_gap if avg_gap > 0 else 0
        
        # Calculate interaction entropy (anti-gaming measure)
        entropy = self.compute_interaction_entropy(events)
        
        return {
            "paste_rate": counts["paste_count"] / max(1, unique_tasks),
            "focus_rate": counts["focus_lost_count"] / max(1, unique_tasks),
            "copy_rate": counts["copy_count"] / max(1, unique_tasks),
            "idle_rate": counts["idle_count"] / max(1, unique_tasks),
            "revision_rate": counts["revision_rate"] / max(1, unique_tasks),
            "avg_gap": avg_gap,
            "cv_gap": cv_gap,
            "event_density": total_events / max(1, unique_tasks),
            "interaction_entropy": entropy  # New: anti-gaming metric
        }

    async def predict_anomaly(self, events: List[Dict]) -> Dict:
        """
        Run scikit-learn prediction with confidence scoring.
        """
        # Ensure model is loaded (lazy loading)
        self.ensure_loaded()
        
        if not self.model or not events:
            return {"status": "model_not_ready", "score": 100}
        
        # Calculate number of questions for confidence scoring
        unique_tasks = len(set([str(e.get("task_id")) for e in events if e.get("task_id")]))
        
        features = self.compute_features(events)
        df = pd.DataFrame([features])
        
        # Ensure correct feature order (handling new entropy feature)
        if self.feature_names:
            # Only use features that exist in training
            available_features = [f for f in self.feature_names if f in df.columns]
            df = df[available_features]
            # Pad with zeros if needed (for backward compatibility)
            for f in self.feature_names:
                if f not in df.columns:
                    df[f] = 0
        
        # Isolation Forest returns -1 for anomalies, 1 for normal
        prediction = self.model.predict(df)[0]
        # Calculate a "Naturalness" score 0-100
        # decision_function returns lower values for anomalies
        raw_score = self.model.decision_function(df)[0]
        
        # Normalize decision_function (roughly -0.5 to 0.5) to 0-100
        anomaly_score = int(max(0, min(100, (raw_score + 0.5) * 100)))
        
        # Calculate confidence level based on sample size
        confidence_level, confidence_percentage, reliability_note = self.compute_confidence_level(
            unique_tasks, len(events)
        )
        
        return {
            "status": "success",
            "is_anomaly": bool(prediction == -1),
            "anomaly_score": 100 - anomaly_score,  # High means very anomalous
            "naturalness_score": anomaly_score,
            "confidence_level": confidence_level,
            "confidence_percentage": confidence_percentage,
            "sample_size": unique_tasks,
            "reliability_note": reliability_note,
            "features": features
        }

    async def get_ollama_narrative(self, features: Dict, candidate_name: str) -> str:
        """
        Ask Ollama to interpret the behavioral patterns.
        """
        try:
            prompt = f"""
            As a behavioral expert, analyze these metrics for candidate '{candidate_name}':
            - Avg time between actions: {features['avg_gap']:.1f}s
            - Timing Variation (CV): {features['cv_gap']:.2f} (Low = predictable, High = natural)
            - Revision Rate: {features['revision_rate']:.1f} per question
            - Paste Rate: {features['paste_rate']:.1f} per question
            - Focus Loss: {features['focus_rate']:.1f} per question
            
            Synthesize a 2-sentence 'Behavioral Fingerprint'. 
            If metrics look robotic (low variation, high pastes, zero revisions), flag it subtly.
            If metrics look like natural independent problem solving (varied timing, revisions), highlight the persistence.
            """
            
            response = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': 'You are a behavioral psychologist specialized in recruitment tech.'},
                {'role': 'user', 'content': prompt},
            ])
            
            return response['message']['content'].strip()
        except Exception as e:
            logger.warning(f"Ollama narrative failed: {e}")
            return "Unable to generate behavioral narrative at this time."

# Singleton instance
anomaly_detector = MLAnomalyDetector()
print(f"[ML] Anomaly Detector initialized: Model loaded = {anomaly_detector.model is not None}")

async def get_ml_behavior_report(events: List[Dict], candidate_name: str = "Candidate") -> Dict:
    """
    Main entry point for calculating ML behavioral anomaly report.
    """
    # 1. Prediction from trained model
    report = await anomaly_detector.predict_anomaly(events)
    
    # 2. Narrative from local LLM (Ollama)
    if report["status"] == "success":
        report["narrative"] = await anomaly_detector.get_ollama_narrative(report["features"], candidate_name)
        
    return report
