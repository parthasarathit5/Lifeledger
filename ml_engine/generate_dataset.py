"""
LifeLedger ML Dataset Generator
Generates realistic financial and lifestyle datasets for training Machine Learning models:
1. Transaction & Categorization NLP Dataset (Merchant names, notes, categories, amounts)
2. Time-Series & Behavioral Expense Dataset (Historical daily/monthly trends, income, habits, tasks, mood)
3. Anomaly & Overspending Dataset (Normal vs Outlier spending patterns)
4. LifeScore & Financial Health Dataset (Holistic lifestyle and savings factors)
"""

import os
import random
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure reproducibility
random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. NLP TRANSACTION CATEGORIZATION DATASET
# -------------------------------------------------------------
MERCHANT_TEMPLATES = {
    'food': [
        "Swiggy order for dinner", "Zomato lunch delivery", "Starbucks coffee & snack", "McDonald's burger meal",
        "Grocery shopping at DMart", "BigBasket weekly vegetables", "Blinkit instant grocery", "Dominos pizza party",
        "KFC chicken bucket", "Subway sub & drink", "Local bakery bread and cake", "Cafe Coffee Day latte",
        "Chai Point tea with biscuits", "Supermarket food supplies", "Organic fruit market", "Haldirams snacks & sweets",
        "Barbeque Nation buffet", "Zepto milk and eggs", "Nature's Basket gourmet items", "Dinner with friends at restaurant",
        "Lunch thali at office canteen", "Pizza Hut dinner", "Ice cream at Baskin Robbins", "Groceries at Reliance Smart",
        "Fresh meat and fish store", "Street food evening snacks", "Oatmeal and cereal pack", "Biryani takeaway",
        "Juice center fresh juice", "Midnight food delivery", "Breakfast at Saravana Bhavan", "Coffee beans purchase"
    ],
    'rent': [
        "Monthly apartment rent", "House rent payment via UPI", "PG accommodation fee", "Flat maintenance charge",
        "Society maintenance bill", "Room rent for current month", "Hostel fees payment", "Co-living monthly rent",
        "Security deposit installment", "Quarterly rent transfer to landlord", "Office space rent share",
        "Storage locker monthly rental", "Parking space monthly rent", "Brokerage fee for apartment", "Water tanker for society"
    ],
    'transport': [
        "Uber cab ride to office", "Ola auto ride", "Metro card monthly recharge", "Petrol pump fuel refill",
        "Diesel filling for car", "Rapido bike taxi", "Bus pass monthly renewal", "Train ticket booking IRCTC",
        "Flight ticket Indigo to Mumbai", "Toll plaza FASTag recharge", "Car servicing & oil change",
        "Bike maintenance and repair", "Airport cab taxi fare", "Parking fee at mall", "EV charging station fee",
        "Cycle repair & parts", "Auto rickshaw cash fare", "Interstate Volvo bus ticket", "Car wash & detailing"
    ],
    'shopping': [
        "Amazon online purchase", "Flipkart electronics sale", "Myntra clothes shopping", "Zara shirt and jeans",
        "H&M summer collection", "Nike running shoes", "Apple store accessories", "IKEA home furniture",
        "Decathlon sportswear and gear", "Ajio discount clothes", "Sneakers purchase", "Casual t-shirt and hoodie",
        "Perfume & cosmetics store", "Watch purchase at Titan", "Bedsheet and pillow covers", "Winter jacket shopping",
        "Backpack for travel", "Croma electronics cable & charger", "Sunglasses purchase", "Kitchen cookware set"
    ],
    'health': [
        "Apollo Pharmacy medicines", "Doctor consultation fee", "Dental clinic root canal visit",
        "Blood test and full body checkup", "Gym membership monthly renewal", "Cult.fit fitness pass",
        "Medplus health supplements", "Eye checkup and new glasses", "Ayurvedic medicines purchase",
        "Physiotherapy session", "Health insurance premium", "Vitamin D & Calcium tablets", "First aid kit supplies",
        "Yoga class subscription", "Protein powder supplement", "Dermatologist skin treatment", "Hospital OPD registration"
    ],
    'entertainment': [
        "Netflix monthly subscription", "Spotify premium music renewal", "BookMyShow movie tickets",
        "PVR cinemas IMAX tickets", "Amazon Prime annual membership", "Hotstar subscription plan",
        "PlayStation PS Plus subscription", "Steam video game purchase", "Concert musical event pass",
        "Bowling & gaming arcade", "Amusement park entry ticket", "YouTube Premium family plan",
        "Club weekend party entry", "Board game cafe bill", "Standup comedy show ticket", "Audible audiobooks"
    ],
    'education': [
        "Udemy online programming course", "Coursera specialization certification", "College semester tuition fee",
        "Books and stationery store", "Kindle e-book purchase", "Skillshare creative subscription",
        "GRE / TOEFL exam registration", "Coding bootcamp installment", "Technical reference book",
        "Language learning app subscription", "Notebooks and pens set", "Online test series subscription",
        "Web development workshop fee", "Academic journal access fee", "Tuition fee for coaching"
    ],
    'other': [
        "Electricity bill payment", "Broadband WiFi internet bill", "Mobile postpaid monthly bill",
        "Water utility bill", "LPG gas cylinder refill", "Charity donation to NGO", "Gift for friend birthday",
        "Bank transaction charge", "Home repair and plumbing", "Courier speed post delivery", "Laundry dry cleaning",
        "Pet food and veterinary care", "House cleaning service Urban Company", "Legal notary & document stamps",
        "ATM cash withdrawal unaccounted", "Gardening plants and soil", "Tax filing CA consultancy fee"
    ]
}

AMOUNT_RANGES = {
    'food': (120, 3500),
    'rent': (5000, 45000),
    'transport': (50, 4500),
    'shopping': (400, 18000),
    'health': (200, 8000),
    'entertainment': (199, 3000),
    'education': (499, 25000),
    'other': (100, 6000)
}

def generate_transaction_nlp_dataset(total_records=6000):
    rows = []
    categories = list(MERCHANT_TEMPLATES.keys())
    
    # Variations & noise additions to simulate real-world user entries
    prefixes = ["", "Paid for ", "Spent on ", "Txn: ", "Purchase at ", "Bill for ", "Quick ", "Online "]
    suffixes = ["", " with card", " via GPay", " at store", " urgent", " for home", " today", " with discount"]
    
    for i in range(total_records):
        cat = random.choice(categories)
        template = random.choice(MERCHANT_TEMPLATES[cat])
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        title = f"{prefix}{template}{suffix}".strip()
        min_a, max_a = AMOUNT_RANGES[cat]
        amount = round(random.uniform(min_a, max_a), 2)
        
        # Note generation
        notes = [
            f"Monthly {cat} budget expense",
            f"Personal spending on {cat}",
            f"Routine {cat} item",
            f"Paid via UPI for {cat}",
            ""
        ]
        note = random.choice(notes)
        
        # Days and seasonal indicators
        day_of_month = random.randint(1, 28)
        day_of_week = random.randint(0, 6) # 0: Mon, 6: Sun
        is_weekend = 1 if day_of_week in [5, 6] else 0
        
        rows.append({
            'text': f"{title} {note}".strip(),
            'title': title,
            'note': note,
            'category': cat,
            'amount': amount,
            'day_of_month': day_of_month,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend
        })
        
    df = pd.DataFrame(rows)
    csv_path = os.path.join(DATA_DIR, 'lifeledger_transactions.csv')
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} transaction records -> {csv_path}")
    return df

# -------------------------------------------------------------
# 2. TIME-SERIES & BEHAVIORAL FORECASTING DATASET
# -------------------------------------------------------------
def generate_forecasting_dataset(num_users=150, months_per_user=24):
    """
    Generates realistic month-over-month and day-over-day financial histories:
    Income, Spending in each category, Habit Completion %, Task Completion %, Mood Score,
    and Next-Month Total Expense target for Regression Forecaster.
    """
    rows = []
    
    for uid in range(1, num_users + 1):
        base_income = random.choice([25000, 45000, 65000, 85000, 120000, 180000, 250000])
        # User spending personality archetype
        spending_ratio = random.uniform(0.40, 0.85) # frugal vs big spender
        habit_baseline = random.uniform(0.3, 0.9)
        task_baseline = random.uniform(0.4, 0.95)
        
        for m in range(months_per_user):
            month_income = base_income * (1 + (0.01 * (m // 6))) # slight growth
            # Random variations
            habit_score = np.clip(habit_baseline + random.uniform(-0.15, 0.15), 0.1, 1.0)
            task_score = np.clip(task_baseline + random.uniform(-0.15, 0.15), 0.1, 1.0)
            mood_score = np.clip((habit_score + task_score) / 2 + random.uniform(-0.1, 0.1), 0.1, 1.0)
            
            # Correlation: Higher habit discipline -> better budget control (less impulse spending)
            discipline_discount = (habit_score - 0.5) * 0.10
            actual_spending_ratio = np.clip(spending_ratio - discipline_discount + random.uniform(-0.08, 0.08), 0.30, 0.95)
            
            total_expense = month_income * actual_spending_ratio
            
            # Category breakdown shares
            food_exp = total_expense * random.uniform(0.20, 0.35)
            rent_exp = total_expense * random.uniform(0.25, 0.40)
            transport_exp = total_expense * random.uniform(0.08, 0.15)
            shopping_exp = total_expense * random.uniform(0.05, 0.20)
            health_exp = total_expense * random.uniform(0.03, 0.10)
            entertainment_exp = total_expense * random.uniform(0.04, 0.12)
            education_exp = total_expense * random.uniform(0.02, 0.08)
            other_exp = total_expense - (food_exp + rent_exp + transport_exp + shopping_exp + health_exp + entertainment_exp + education_exp)
            if other_exp < 0:
                other_exp = total_expense * 0.05
                
            savings = month_income - total_expense
            savings_rate = savings / month_income
            
            # Next month expected expense with seasonal/random component
            next_month_expense = total_expense * (1.0 + random.uniform(-0.06, 0.07))
            
            # Financial Health & LifeScore target (0 - 100)
            # Higher savings rate + higher habit score + higher task completion = High LifeScore
            life_score = int(np.clip((savings_rate * 45) + (habit_score * 30) + (task_score * 25), 15, 99))
            
            risk_class = 'Low' if savings_rate >= 0.30 and habit_score >= 0.6 else ('High' if savings_rate < 0.10 else 'Moderate')
            
            rows.append({
                'user_id': uid,
                'month_idx': m,
                'income': round(month_income, 2),
                'total_expense': round(total_expense, 2),
                'savings': round(savings, 2),
                'savings_rate': round(savings_rate, 4),
                'food_expense': round(food_exp, 2),
                'rent_expense': round(rent_exp, 2),
                'transport_expense': round(transport_exp, 2),
                'shopping_expense': round(shopping_exp, 2),
                'health_expense': round(health_exp, 2),
                'entertainment_expense': round(entertainment_exp, 2),
                'education_expense': round(education_exp, 2),
                'other_expense': round(other_exp, 2),
                'habit_completion_rate': round(habit_score, 4),
                'task_completion_rate': round(task_score, 4),
                'mood_index': round(mood_score, 4),
                'life_score': life_score,
                'risk_class': risk_class,
                'target_next_month_expense': round(next_month_expense, 2)
            })
            
    df = pd.DataFrame(rows)
    csv_path = os.path.join(DATA_DIR, 'lifeledger_forecasting.csv')
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} forecasting & behavioral records -> {csv_path}")
    return df

# -------------------------------------------------------------
# 3. ANOMALY DETECTION DATASET
# -------------------------------------------------------------
def generate_anomaly_dataset(total_records=4000):
    rows = []
    categories = list(MERCHANT_TEMPLATES.keys())
    
    for i in range(total_records):
        cat = random.choice(categories)
        is_anomaly = 1 if random.random() < 0.08 else 0 # 8% anomalies
        
        min_a, max_a = AMOUNT_RANGES[cat]
        if is_anomaly:
            # 3x to 8x normal spending spike
            amount = round(random.uniform(max_a * 2.5, max_a * 6.5), 2)
            freq_dev = random.uniform(3.0, 7.0)
            note = f"Unusual high spike in {cat}"
        else:
            amount = round(random.uniform(min_a, max_a), 2)
            freq_dev = random.uniform(0.2, 1.8)
            note = f"Normal transaction in {cat}"
            
        rows.append({
            'category': cat,
            'amount': amount,
            'frequency_deviation': round(freq_dev, 2),
            'day_of_month': random.randint(1, 28),
            'is_weekend': random.choice([0, 1]),
            'is_anomaly': is_anomaly,
            'note': note
        })
        
    df = pd.DataFrame(rows)
    csv_path = os.path.join(DATA_DIR, 'lifeledger_anomalies.csv')
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} anomaly records -> {csv_path}")
    return df

if __name__ == '__main__':
    print("Generating LifeLedger ML Datasets...")
    generate_transaction_nlp_dataset(6000)
    generate_forecasting_dataset(150, 24)
    generate_anomaly_dataset(4000)
    print("All datasets generated successfully in:", DATA_DIR)
