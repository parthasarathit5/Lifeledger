"""
LifeLedger ML Training Pipeline
Trains, evaluates, and exports 4 production-grade Machine Learning models:
1. NLP Categorizer Pipeline (TF-IDF + Calibrated Classifier)
2. Expense & Savings Forecaster (RandomForest Regressor)
3. Anomaly & Overspending Detector (IsolationForest + Category Encoders)
4. LifeScore & Financial Health Predictor (GradientBoosting + Multi-factor Regressor)
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, mean_absolute_error, r2_score
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'saved_models')
os.makedirs(MODELS_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. TRAIN NLP AUTO-CATEGORIZATION MODEL
# -------------------------------------------------------------
def train_categorizer():
    print("\n" + "="*60)
    print("1. TRAINING NLP AUTO-CATEGORIZATION MODEL")
    print("="*60)
    
    csv_path = os.path.join(DATA_DIR, 'lifeledger_transactions.csv')
    df = pd.read_csv(csv_path)
    
    X = df['text']
    y = df['category']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=8000, lowercase=True, stop_words='english')),
        ('clf', RandomForestClassifier(n_estimators=120, max_depth=25, random_state=42, n_jobs=-1))
    ])
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    print(f"-> Categorizer Test Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))
    
    model_path = os.path.join(MODELS_DIR, 'categorizer_pipeline.joblib')
    joblib.dump(pipeline, model_path)
    print(f"Saved NLP Categorizer -> {model_path}")
    return pipeline

# -------------------------------------------------------------
# 2. TRAIN TIME-SERIES & BEHAVIORAL EXPENSE FORECASTER
# -------------------------------------------------------------
def train_forecaster():
    print("\n" + "="*60)
    print("2. TRAINING TIME-SERIES EXPENSE FORECASTER")
    print("="*60)
    
    csv_path = os.path.join(DATA_DIR, 'lifeledger_forecasting.csv')
    df = pd.read_csv(csv_path)
    
    feature_cols = [
        'income', 'total_expense', 'savings', 'savings_rate',
        'food_expense', 'rent_expense', 'transport_expense', 'shopping_expense',
        'health_expense', 'entertainment_expense', 'education_expense', 'other_expense',
        'habit_completion_rate', 'task_completion_rate', 'mood_index'
    ]
    
    X = df[feature_cols]
    y = df['target_next_month_expense']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    regressor = RandomForestRegressor(n_estimators=150, max_depth=15, random_state=42, n_jobs=-1)
    regressor.fit(X_train, y_train)
    
    y_pred = regressor.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"-> Forecaster R² Score: {r2:.4f} (Explained Variance: {r2*100:.1f}%)")
    print(f"-> Forecaster Mean Absolute Error (MAE): INR {mae:.2f}")
    
    model_artifact = {
        'model': regressor,
        'feature_cols': feature_cols,
        'r2_score': r2,
        'mae': mae
    }
    model_path = os.path.join(MODELS_DIR, 'forecaster_model.joblib')
    joblib.dump(model_artifact, model_path)
    print(f"Saved Expense Forecaster -> {model_path}")
    return regressor

# -------------------------------------------------------------
# 3. TRAIN ANOMALY & OVERSPENDING DETECTION MODEL
# -------------------------------------------------------------
def train_anomaly_detector():
    print("\n" + "="*60)
    print("3. TRAINING ANOMALY & OVERSPENDING DETECTOR")
    print("="*60)
    
    csv_path = os.path.join(DATA_DIR, 'lifeledger_anomalies.csv')
    df = pd.read_csv(csv_path)
    
    # One-hot encode category
    ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    cat_encoded = ohe.fit_transform(df[['category']])
    cat_cols = [f"cat_{c}" for c in ohe.categories_[0]]
    
    num_features = df[['amount', 'frequency_deviation', 'day_of_month', 'is_weekend']].values
    X = np.hstack([num_features, cat_encoded])
    
    # Train Isolation Forest
    iso = IsolationForest(n_estimators=120, contamination=0.08, random_state=42, n_jobs=-1)
    iso.fit(X)
    
    # Prediction: -1 for anomaly, 1 for normal
    preds = iso.predict(X)
    anomaly_count = (preds == -1).sum()
    print(f"-> Detected {anomaly_count} potential anomalies out of {len(X)} records ({anomaly_count/len(X)*100:.1f}%)")
    
    model_artifact = {
        'model': iso,
        'encoder': ohe,
        'num_cols': ['amount', 'frequency_deviation', 'day_of_month', 'is_weekend'],
        'categories': list(ohe.categories_[0])
    }
    model_path = os.path.join(MODELS_DIR, 'anomaly_detector.joblib')
    joblib.dump(model_artifact, model_path)
    print(f"Saved Anomaly Detector -> {model_path}")
    return iso

# -------------------------------------------------------------
# 4. TRAIN LIFESCORE & FINANCIAL HEALTH CLASSIFIER
# -------------------------------------------------------------
def train_lifescore_models():
    print("\n" + "="*60)
    print("4. TRAINING LIFESCORE & FINANCIAL HEALTH CLASSIFIER")
    print("="*60)
    
    csv_path = os.path.join(DATA_DIR, 'lifeledger_forecasting.csv')
    df = pd.read_csv(csv_path)
    
    feature_cols = [
        'income', 'total_expense', 'savings_rate',
        'habit_completion_rate', 'task_completion_rate', 'mood_index'
    ]
    
    X = df[feature_cols]
    y_score = df['life_score']
    y_risk = df['risk_class']
    
    X_train, X_test, y_score_train, y_score_test, y_risk_train, y_risk_test = train_test_split(
        X, y_score, y_risk, test_size=0.2, random_state=42
    )
    
    # Regressor for Score
    score_reg = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    score_reg.fit(X_train, y_score_train)
    score_r2 = r2_score(y_score_test, score_reg.predict(X_test))
    
    # Classifier for Risk Class
    risk_clf = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
    risk_clf.fit(X_train, y_risk_train)
    risk_acc = accuracy_score(y_risk_test, risk_clf.predict(X_test))
    
    print(f"-> LifeScore Regressor R² Score: {score_r2:.4f}")
    print(f"-> Financial Risk Classifier Accuracy: {risk_acc*100:.2f}%")
    
    model_artifact = {
        'score_regressor': score_reg,
        'risk_classifier': risk_clf,
        'feature_cols': feature_cols
    }
    model_path = os.path.join(MODELS_DIR, 'lifescore_model.joblib')
    joblib.dump(model_artifact, model_path)
    print(f"Saved LifeScore & Risk Models -> {model_path}")
    return model_artifact

if __name__ == '__main__':
    print("Starting LifeLedger Machine Learning Training Pipeline...")
    train_categorizer()
    train_forecaster()
    train_anomaly_detector()
    train_lifescore_models()
    print("\n" + "="*60)
    print("ALL 4 MACHINE LEARNING MODELS TRAINED & SAVED SUCCESSFULLY!")
    print("="*60)
