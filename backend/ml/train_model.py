
import os
import sys
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Ensure we can import app modules if needed (though we're hardcoding logic here to be standalone)
sys.path.append(os.path.join(os.getcwd(), '..'))

def generate_synthetic_data(n_samples=1000):
    """
    Generate synthetic candidate profiles based on behavioral psychology personas.
    """
    np.random.seed(42)
    
    data = []
    
    for _ in range(n_samples):
        # Assign a persona
        persona = np.random.choice(['high_performer', 'average', 'anxious', 'cheater', 'disengaged'], p=[0.2, 0.4, 0.2, 0.1, 0.1])
        
        if persona == 'high_performer':
            # High consistency, high reasoning, good completion
            decision_firmness = np.random.normal(85, 10)
            reasoning_depth = np.random.normal(80, 15)
            completion_rate = np.random.beta(9, 1) # Skewed towards 1.0
            attention_stability = np.random.normal(90, 5)
            decision_consistency = np.random.normal(85, 10)
            
        elif persona == 'average':
            # Mixed bag
            decision_firmness = np.random.normal(60, 15)
            reasoning_depth = np.random.normal(50, 20)
            completion_rate = np.random.beta(7, 3) 
            attention_stability = np.random.normal(70, 15)
            decision_consistency = np.random.normal(60, 15)
            
        elif persona == 'anxious':
            # Low firmness (many changes), high reasoning (overthinking), high focus
            decision_firmness = np.random.normal(30, 15)
            reasoning_depth = np.random.normal(75, 15)
            completion_rate = np.random.beta(5, 5)
            attention_stability = np.random.normal(85, 10)
            decision_consistency = np.random.normal(40, 20)
            
        elif persona == 'cheater':
            # High firmness (copy-paste), zero reasoning, low stability (tab switching)
            decision_firmness = np.random.normal(90, 5) # Quick/pasted answers look "firm"
            reasoning_depth = np.random.normal(10, 10)
            completion_rate = np.random.beta(8, 2)
            attention_stability = np.random.normal(20, 15) # Lots of focus loss
            decision_consistency = np.random.normal(90, 5) # Robotic
            
        elif persona == 'disengaged':
            # Random clicking, fast, no reasoning
            decision_firmness = np.random.normal(80, 20)
            reasoning_depth = np.random.normal(5, 5)
            completion_rate = np.random.beta(2, 8) # Quits early
            attention_stability = np.random.normal(50, 20)
            decision_consistency = np.random.normal(50, 20)

        # Clip values to valid ranges
        row = {
            'decision_firmness': np.clip(decision_firmness, 0, 100),
            'reasoning_depth': np.clip(reasoning_depth, 0, 100),
            'completion_rate': np.clip(completion_rate, 0, 1) * 100, # Normalize to 0-100 for model
            'attention_stability': np.clip(attention_stability, 0, 100), # Assuming this is 0-100 scale now or we convert
            'decision_consistency': np.clip(decision_consistency, 0, 100)
        }
        
        # GROUND TRUTH LABEL GENERATION (The "Expert Formula" we are mimicking)
        # We use a slightly more complex version of the linear formula to make the tree learn non-linearities
        score = (
            0.25 * row['decision_firmness'] +
            0.30 * row['reasoning_depth'] +  # Higher weight on reasoning
            0.20 * row['completion_rate'] +
            0.15 * row['attention_stability'] +
            0.10 * row['decision_consistency']
        )
        
        # Penalties (Non-linear rules the tree will learn)
        if row['attention_stability'] < 40: score -= 20 # Cheater penalty
        if row['reasoning_depth'] < 15: score -= 15 # No reasoning penalty
        if row['completion_rate'] < 50: score -= 30 # Incomplete penalty
        
        row['success_probability'] = np.clip(score, 0, 100)
        data.append(row)
        
    return pd.DataFrame(data)

def train():
    print("Generating 1,000 synthetic candidate profiles...")
    df = generate_synthetic_data(1000)
    
    print("Preview of Synthetic Data:")
    print(df.head())
    
    X = df[['decision_firmness', 'reasoning_depth', 'completion_rate', 'attention_stability', 'decision_consistency']]
    y = df['success_probability']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\nTraining Random Forest Regressor on {len(X_train)} samples...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Model Mean Absolute Error: {mae:.2f} points (on 0-100 scale)")
    
    # Save features and model
    output_dir = os.path.join(os.getcwd(), 'app', 'ml_models')
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, 'interview_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"\n[SUCCESS] Model saved to: {model_path}")
    print("This model captures the behavioral nuances of High Performers vs Cheaters.")

if __name__ == "__main__":
    train()
