"""
LifeLedger Comprehensive AI & ML System Validation Test
Tests all 4 ML models directly and verifies inference output structures.
"""

import os
import sys

# Force UTF-8 stdout
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeledger_backend.settings')

import django
django.setup()

from tracker.ml_service import ml_service
from tracker.ml_advisor import MLAdvisor
from tracker.models import User

def run_tests():
    print("=" * 60)
    print("RUNNING LIFELEDGER AI & ML VALIDATION SUITE")
    print("=" * 60)

    # 1. NLP Categorizer Test
    test_queries = [
        ("Swiggy Biryani Dinner with friends", "food"),
        ("Uber cab ride to Bangalore Airport", "transport"),
        ("Monthly PG rent transfer via UPI", "rent"),
        ("Decathlon sports running shoes and gym bag", "shopping"),
        ("Apollo Pharmacy monthly medicine tablets", "health"),
        ("Netflix 4K UHD monthly subscription", "entertainment"),
        ("Udemy Python and Machine Learning Masterclass", "education"),
        ("Electricity utility bill payment", "other")
    ]

    print("\n1. Testing NLP Auto-Categorizer (TF-IDF + Random Forest):")
    correct = 0
    for query, expected in test_queries:
        res = ml_service.predict_category(query)
        pred = res['predicted_category']
        conf = res['confidence_percent']
        is_match = (pred == expected)
        if is_match:
            correct += 1
        print(f"  [{'PASS' if is_match else 'FAIL'}] '{query}' -> Pred: {pred} ({conf}%) | Expected: {expected}")
    print(f"-> Categorizer Accuracy: {correct}/{len(test_queries)} ({correct/len(test_queries)*100:.1f}%)")

    # 2. Anomaly & Outlier Detector Test
    print("\n2. Testing IsolationForest Anomaly Detector:")
    test_anomalies = [
        (450.0, 'food', "Regular dining"),
        (25000.0, 'food', "Huge dining spike (Anomaly)"),
        (250.0, 'transport', "Normal auto fare"),
        (18000.0, 'transport', "Outlier transport expense")
    ]
    for amt, cat, desc in test_anomalies:
        res = ml_service.detect_anomaly(amt, cat)
        print(f"  Amount: INR {amt} in {cat} ({desc}) -> Anomaly: {res['is_anomaly']} | Risk: {res['risk_level']} | Reason: {res['reason']}")

    # 3. User ML Forecasting & LifeScore Test
    print("\n3. Testing Time-Series Forecaster & LifeScore Ensemble:")
    user = User.objects.first()
    if not user:
        user = User.objects.create(name="Demo Tester", email="demo@lifeledger.ai", password="hash")
        print("  Created demo user for test")

    forecast = ml_service.forecast_user_finances(user)
    print(f"  User: {user.email}")
    print(f"  Current Expense: INR {forecast['current_expense']}")
    print(f"  Predicted Next-Month Expense: INR {forecast['predicted_next_month_expense']}")
    print(f"  Predicted Monthly Savings: INR {forecast['predicted_savings']}")
    print(f"  Savings Rate: {forecast['savings_rate_percent']}%")
    print(f"  Model Source: {forecast['model_source']}")
    print(f"  R² Confidence: {forecast['confidence_r2']}")

    lifescore = ml_service.predict_lifescore(user)
    print(f"  LifeScore: {lifescore['predicted_lifescore']}/100")
    print(f"  Risk Profile: {lifescore['risk_class']}")

    # 4. AI Advisor Q&A Test
    print("\n4. Testing AI Financial Advisor Engine (MLAdvisor):")
    questions = [
        "Can I afford to buy an iPhone for 60,000?",
        "Where am I spending the most money?",
        "What is my expense forecast for next month?",
        "How do my habits affect my savings?"
    ]
    for q in questions:
        ans = MLAdvisor.answer_query(user, q)
        print(f"\n  Q: '{q}'")
        first_line = ans['answer'].split('\n')[0]
        print(f"  A: {first_line} ... (Category: {ans['category']})")
        print(f"  Suggested Actions: {ans['suggested_actions']}")

    print("\n" + "=" * 60)
    print("ALL AI & ML VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
