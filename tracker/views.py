from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Sum, Count
import json
from datetime import date, timedelta
from .models import User, Expense, Income, Habit, HabitLog, Task, Mood, History,Budget


def save_history(user, type, title, amount=None, category="", note=""):
    today = timezone.localdate()
    History.objects.create(
        user=user, type=type, title=title,
        amount=amount, category=category, note=note,
        date=today, month=today.month, year=today.year,
    )


@csrf_exempt
def login_view(request):
    if request.method == "GET":
        return JsonResponse({"message": "Login API working"})
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return JsonResponse({"status": "error", "message": "Missing fields"})
        user = User.objects.filter(email=email).first()
        if user and check_password(password, user.password):
            return JsonResponse({
                "status": "success",
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "login_time": localtime(timezone.now()).strftime('%d-%m-%Y %I:%M %p'),
            })
        return JsonResponse({"status": "error", "message": "Invalid email or password"})
    return JsonResponse({"status": "error", "message": "Invalid request method"})


@csrf_exempt
def signup_view(request):
    if request.method == "GET":
        return JsonResponse({"message": "Signup API working"})
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        name = data.get("name", "").strip()
        email = data.get("email")
        password = data.get("password")
        if not email or not password or not name:
            return JsonResponse({"status": "error", "message": "All fields are required"})
        if User.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "Email already registered"})
        user = User.objects.create(
            name=name, email=email, password=make_password(password)
        )
        return JsonResponse({
            "status": "success",
            "user_id": user.id,
            "name": user.name,
            "created_at": localtime(timezone.now()).strftime('%d-%m-%Y %I:%M %p'),
        })
    return JsonResponse({"status": "error", "message": "Invalid request method"})


@csrf_exempt
def dashboard_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    total_expense = sum(e.amount for e in Expense.objects.filter(user=user))
    total_income = sum(i.amount for i in Income.objects.filter(user=user))
    balance = total_income - total_expense
    recent_expenses = Expense.objects.filter(user=user).order_by('-date')[:5]
    recent_incomes = Income.objects.filter(user=user).order_by('-date')[:5]
    transactions = []
    for e in recent_expenses:
        transactions.append({
            "type": "expense", "title": e.title,
            "category": e.category, "amount": e.amount, "date": str(e.date),
        })
    for i in recent_incomes:
        transactions.append({
            "type": "income", "title": i.title,
            "category": i.category, "amount": i.amount, "date": str(i.date),
        })
    transactions.sort(key=lambda x: x["date"], reverse=True)
    total_habits = Habit.objects.filter(user=user).count()
    today = timezone.localdate()
    completed_habits = HabitLog.objects.filter(
        habit__user=user, date=today, completed=True).count()
    pending_tasks = Task.objects.filter(user=user, completed=False).count()
    completed_tasks = Task.objects.filter(user=user, completed=True).count()
    return JsonResponse({
        "status": "success",
        "balance": balance,
        "total_income": total_income,
        "total_expense": total_expense,
        "transactions": transactions[:5],
        "total_habits": total_habits,
        "completed_habits": completed_habits,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
    })


@csrf_exempt
def expense_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        expenses = Expense.objects.filter(user=user).order_by('-date')
        return JsonResponse({
            "status": "success",
            "expenses": [{"id": e.id, "title": e.title, "amount": e.amount,
                          "category": e.category, "date": str(e.date), "note": e.note}
                         for e in expenses]
        })
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        title = data.get("title")
        amount = data.get("amount")
        category = data.get("category", "other")
        note = data.get("note", "")
        if not title or not amount:
            return JsonResponse({"status": "error", "message": "Title and amount required"})
        expense = Expense.objects.create(
            user=user, title=title, amount=float(amount), category=category, note=note)
        save_history(user=user, type='expense', title=title,
                     amount=float(amount), category=category, note=note)
        return JsonResponse({"status": "success", "id": expense.id})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        Expense.objects.filter(id=data.get("id"), user=user).delete()
        return JsonResponse({"status": "success"})


@csrf_exempt
def income_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        incomes = Income.objects.filter(user=user).order_by('-date')
        return JsonResponse({
            "status": "success",
            "incomes": [{"id": i.id, "title": i.title, "amount": i.amount,
                         "category": i.category, "date": str(i.date), "note": i.note}
                        for i in incomes]
        })
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        title = data.get("title")
        amount = data.get("amount")
        category = data.get("category", "other")
        note = data.get("note", "")
        if not title or not amount:
            return JsonResponse({"status": "error", "message": "Title and amount required"})
        income = Income.objects.create(
            user=user, title=title, amount=float(amount), category=category, note=note)
        save_history(user=user, type='income', title=title,
                     amount=float(amount), category=category, note=note)
        return JsonResponse({"status": "success", "id": income.id})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        Income.objects.filter(id=data.get("id"), user=user).delete()
        return JsonResponse({"status": "success"})


@csrf_exempt
def habit_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        today = timezone.localdate()
        habits = Habit.objects.filter(user=user)
        return JsonResponse({
            "status": "success",
            "habits": [{"id": h.id, "name": h.name, "icon": h.icon,
                        "completed_today": HabitLog.objects.filter(
                            habit=h, date=today, completed=True).exists()}
                       for h in habits]
        })
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        name = data.get("name")
        icon = data.get("icon", "⭐")
        if not name:
            return JsonResponse({"status": "error", "message": "Habit name required"})
        habit = Habit.objects.create(user=user, name=name, icon=icon)
        return JsonResponse({"status": "success", "id": habit.id})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        Habit.objects.filter(id=data.get("id"), user=user).delete()
        return JsonResponse({"status": "success"})


@csrf_exempt
def habit_log_view(request, habit_id):
    try:
        habit = Habit.objects.get(id=habit_id)
    except Habit.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Habit not found"})
    if request.method == "POST":
        today = timezone.localdate()
        log, created = HabitLog.objects.get_or_create(habit=habit, date=today)
        log.completed = not log.completed
        log.save()
        if log.completed:
            save_history(user=habit.user, type='habit',
                         title=f"Completed habit: {habit.name}", category=habit.icon)
        return JsonResponse({"status": "success", "completed": log.completed})


@csrf_exempt
def task_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        tasks = Task.objects.filter(user=user).order_by('completed', '-created_at')
        return JsonResponse({
            "status": "success",
            "tasks": [{"id": t.id, "title": t.title, "priority": t.priority,
                       "completed": t.completed,
                       "completed_at": str(t.completed_at) if t.completed_at else None,
                       "due_date": str(t.due_date) if t.due_date else None,
                       "created_at": str(t.created_at)}
                      for t in tasks]
        })
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        title = data.get("title")
        priority = data.get("priority", "medium")
        due_date = data.get("due_date")
        if not title:
            return JsonResponse({"status": "error", "message": "Task title required"})
        task = Task.objects.create(user=user, title=title, priority=priority, due_date=due_date)
        return JsonResponse({"status": "success", "id": task.id})
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        task = Task.objects.filter(id=data.get("id"), user=user).first()
        if task:
            task.completed = not task.completed
            if task.completed:
                task.completed_at = timezone.localdate()
                save_history(user=user, type='task',
                             title=f"Completed task: {task.title}", category=task.priority)
            else:
                task.completed_at = None
            task.save()
        return JsonResponse({"status": "success"})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        Task.objects.filter(id=data.get("id"), user=user).delete()
        return JsonResponse({"status": "success"})


@csrf_exempt
def mood_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        moods = Mood.objects.filter(user=user).order_by('-date')[:30]
        return JsonResponse({
            "status": "success",
            "moods": [{"id": m.id, "mood": m.mood, "note": m.note, "date": str(m.date)}
                      for m in moods]
        })
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        mood = data.get("mood")
        note = data.get("note", "")
        if not mood:
            return JsonResponse({"status": "error", "message": "Mood required"})
        mood_obj = Mood.objects.create(user=user, mood=mood, note=note)
        save_history(user=user, type='mood', title=f"Mood logged: {mood}", note=note)
        return JsonResponse({"status": "success", "id": mood_obj.id})


@csrf_exempt
def history_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        month = request.GET.get("month")
        year = request.GET.get("year")
        type_filter = request.GET.get("type")
        history = History.objects.filter(user=user)
        if month:
            history = history.filter(month=int(month))
        if year:
            history = history.filter(year=int(year))
        if type_filter:
            history = history.filter(type=type_filter)
        history = history.order_by('-date', '-id')
        return JsonResponse({
            "status": "success",
            "history": [{"id": h.id, "type": h.type, "title": h.title,
                         "amount": h.amount, "category": h.category,
                         "note": h.note, "date": str(h.date),
                         "month": h.month, "year": h.year}
                        for h in history]
        })


# ============================================================
# NEW FEATURE 1 — ANALYTICS
# ============================================================
@csrf_exempt
def analytics_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    # Expense by category
    expenses = Expense.objects.filter(user=user, date__month=month, date__year=year)
    category_data = {}
    for e in expenses:
        category_data[e.category] = category_data.get(e.category, 0) + e.amount

    # Monthly expense last 6 months
    monthly_expense = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        total = sum(e.amount for e in Expense.objects.filter(
            user=user, date__month=d.month, date__year=d.year))
        monthly_expense.append({
            "month": d.strftime("%b"),
            "year": d.year,
            "total": total
        })

    # Monthly income last 6 months
    monthly_income = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        total = sum(inc.amount for inc in Income.objects.filter(
            user=user, date__month=d.month, date__year=d.year))
        monthly_income.append({
            "month": d.strftime("%b"),
            "year": d.year,
            "total": total
        })

    total_expense_month = sum(category_data.values())
    total_income_month = sum(
        i.amount for i in Income.objects.filter(
            user=user, date__month=month, date__year=year))

    return JsonResponse({
        "status": "success",
        "category_breakdown": category_data,
        "monthly_expense": monthly_expense,
        "monthly_income": monthly_income,
        "total_expense_month": total_expense_month,
        "total_income_month": total_income_month,
        "savings_month": total_income_month - total_expense_month,
    })


# ============================================================
# NEW FEATURE 2 — LIFE SCORE
# ============================================================
@csrf_exempt
def life_score_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()

    # Habits score (25 points)
    total_habits = Habit.objects.filter(user=user).count()
    completed_habits = HabitLog.objects.filter(
        habit__user=user, date=today, completed=True).count()
    habit_score = int((completed_habits / total_habits * 25)) if total_habits > 0 else 0

    # Tasks score (25 points)
    total_tasks = Task.objects.filter(user=user, created_at=today).count()
    completed_tasks = Task.objects.filter(user=user, completed_at=today).count()
    task_score = int((completed_tasks / total_tasks * 25)) if total_tasks > 0 else 12

    # Mood score (25 points)
    mood_today = Mood.objects.filter(user=user, date=today).first()
    mood_scores = {'great': 25, 'good': 20, 'okay': 15, 'bad': 8, 'terrible': 3}
    mood_score = mood_scores.get(mood_today.mood, 12) if mood_today else 12

    # Budget score (25 points)
    month_expense = sum(e.amount for e in Expense.objects.filter(
        user=user, date__month=today.month, date__year=today.year))
    month_income = sum(i.amount for i in Income.objects.filter(
        user=user, date__month=today.month, date__year=today.year))
    if month_income > 0:
        spend_ratio = month_expense / month_income
        if spend_ratio <= 0.5:
            budget_score = 25
        elif spend_ratio <= 0.7:
            budget_score = 20
        elif spend_ratio <= 0.9:
            budget_score = 15
        else:
            budget_score = 5
    else:
        budget_score = 12

    total_score = habit_score + task_score + mood_score + budget_score

    if total_score >= 85:
        grade = "Excellent 🏆"
        message = "Amazing day! You are crushing it!"
    elif total_score >= 70:
        grade = "Great 🌟"
        message = "Really good day! Keep it up!"
    elif total_score >= 55:
        grade = "Good 👍"
        message = "Decent day! Room to improve!"
    elif total_score >= 40:
        grade = "Average 😐"
        message = "Could be better. Try harder tomorrow!"
    else:
        grade = "Poor 😔"
        message = "Tough day. Tomorrow is a new start!"

    return JsonResponse({
        "status": "success",
        "total_score": total_score,
        "grade": grade,
        "message": message,
        "breakdown": {
            "habit_score": habit_score,
            "task_score": task_score,
            "mood_score": mood_score,
            "budget_score": budget_score,
        },
        "details": {
            "habits_completed": f"{completed_habits}/{total_habits}",
            "tasks_completed": f"{completed_tasks}/{total_tasks}",
            "mood_today": mood_today.mood if mood_today else "Not logged",
            "spending_ratio": f"{int(spend_ratio * 100)}%" if month_income > 0 else "No income",
        }
    })


# ============================================================
# NEW FEATURE 3 — BUDGET PLANNER
# ============================================================
@csrf_exempt
def budget_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()

    if request.method == "GET":
        budgets = Budget.objects.filter(user=user,
                                        month=today.month, year=today.year)
        result = []
        for b in budgets:
            spent = sum(e.amount for e in Expense.objects.filter(
                user=user, category=b.category,
                date__month=today.month, date__year=today.year))
            percentage = int((spent / b.amount * 100)) if b.amount > 0 else 0
            result.append({
                "id": b.id,
                "category": b.category,
                "budget": b.amount,
                "spent": spent,
                "remaining": b.amount - spent,
                "percentage": percentage,
                "status": "danger" if percentage >= 90 else
                          "warning" if percentage >= 70 else "safe"
            })
        return JsonResponse({"status": "success", "budgets": result})

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        category = data.get("category")
        amount = data.get("amount")
        if not category or not amount:
            return JsonResponse({"status": "error", "message": "Category and amount required"})
        budget, created = Budget.objects.update_or_create(
            user=user, category=category,
            month=today.month, year=today.year,
            defaults={"amount": float(amount)}
        )
        return JsonResponse({"status": "success", "id": budget.id})

    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        Budget.objects.filter(id=data.get("id"), user=user).delete()
        return JsonResponse({"status": "success"})


# ============================================================
# NEW FEATURE 4 — FUTURE PREDICTOR
# ============================================================
@csrf_exempt
def predictor_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()

    # ===== LAST 3 MONTHS AVG =====
    total_expense_3months = 0
    total_income_3months = 0
    months_count = 0

    category_data = {}

    for i in range(1, 4):
        d = today.replace(day=1) - timedelta(days=i * 30)

        expenses = Expense.objects.filter(
            user=user, date__month=d.month, date__year=d.year
        )

        incomes = Income.objects.filter(
            user=user, date__month=d.month, date__year=d.year
        )

        exp_total = sum(e.amount for e in expenses)
        inc_total = sum(i.amount for i in incomes)

        if exp_total > 0 or inc_total > 0:
            total_expense_3months += exp_total
            total_income_3months += inc_total
            months_count += 1

        # 📊 Category tracking
        for e in expenses:
            category_data[e.category] = category_data.get(e.category, 0) + e.amount

    avg_expense = total_expense_3months / months_count if months_count else 0
    avg_income = total_income_3months / months_count if months_count else 0
    avg_savings = avg_income - avg_expense

    # ===== CURRENT MONTH =====
    days_passed = today.day
    days_in_month = 30
    days_remaining = days_in_month - days_passed

    this_month_expense = sum(e.amount for e in Expense.objects.filter(
        user=user, date__month=today.month, date__year=today.year))

    this_month_income = sum(i.amount for i in Income.objects.filter(
        user=user, date__month=today.month, date__year=today.year))

    daily_spend = this_month_expense / days_passed if days_passed > 0 else 0

    predicted_month_expense = this_month_expense + (daily_spend * days_remaining)
    predicted_savings = this_month_income - predicted_month_expense

    savings_6months = avg_savings * 6
    savings_1year = avg_savings * 12

    # ===== 🔥 SMART INSIGHTS =====
    insights = []
    suggestions = []

    # 🧠 Top spending category
    if category_data:
        top_category = max(category_data, key=category_data.get)
        insights.append(f"💸 Most spending is on {top_category}")

    # 📅 Weekend behavior
    weekend = sum(e.amount for e in Expense.objects.filter(
        user=user) if e.date.weekday() >= 5)
    weekday = sum(e.amount for e in Expense.objects.filter(
        user=user) if e.date.weekday() < 5)

    if weekend > weekday:
        insights.append("📅 You spend more on weekends")
        suggestions.append("Try limiting weekend spending")

    # ⚠ Spending ratio
    if avg_income > 0:
        ratio = avg_expense / avg_income

        if ratio > 0.9:
            suggestions.append("⚠ You spend almost all income! Save more")
        elif ratio > 0.7:
            suggestions.append("📊 Reduce expenses by 10% to improve savings")
        else:
            insights.append("✅ Good saving habit")

    # 🧠 Daily spend warning
    if daily_spend > 0:
        insights.append(f"💡 You spend around ₹{int(daily_spend)}/day")

    # 🎯 Smart saving tip
    if predicted_savings < 0:
        suggestions.append("❌ You may go negative this month!")
    else:
        suggestions.append(f"💰 You can save ₹{int(predicted_savings)} this month")

    return JsonResponse({
        "status": "success",

        # 📊 core data
        "avg_monthly_expense": round(avg_expense, 2),
        "avg_monthly_income": round(avg_income, 2),
        "avg_monthly_savings": round(avg_savings, 2),

        "predicted_month_expense": round(predicted_month_expense, 2),
        "predicted_month_savings": round(predicted_savings, 2),

        "savings_6months": round(savings_6months, 2),
        "savings_1year": round(savings_1year, 2),

        "daily_spend_rate": round(daily_spend, 2),
        "days_remaining": days_remaining,

        # 🔥 NEW INTELLIGENCE
        "insights": insights,
        "suggestions": suggestions,
    })
# ============================================================
# NEW FEATURE 5 — COMPARE MONTH
# ============================================================
@csrf_exempt
def compare_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()

    # This month
    this_expense = sum(e.amount for e in Expense.objects.filter(
        user=user, date__month=today.month, date__year=today.year))
    this_income = sum(i.amount for i in Income.objects.filter(
        user=user, date__month=today.month, date__year=today.year))
    this_tasks = Task.objects.filter(
        user=user, completed=True, completed_at__month=today.month,
        completed_at__year=today.year).count()
    this_habits = HabitLog.objects.filter(
        habit__user=user, date__month=today.month,
        date__year=today.year, completed=True).count()
    this_mood = Mood.objects.filter(
        user=user, date__month=today.month,
        date__year=today.year).first()

    # Last month
    last_month = today.replace(day=1) - timedelta(days=1)
    last_expense = sum(e.amount for e in Expense.objects.filter(
        user=user, date__month=last_month.month, date__year=last_month.year))
    last_income = sum(i.amount for i in Income.objects.filter(
        user=user, date__month=last_month.month, date__year=last_month.year))
    last_tasks = Task.objects.filter(
        user=user, completed=True, completed_at__month=last_month.month,
        completed_at__year=last_month.year).count()
    last_habits = HabitLog.objects.filter(
        habit__user=user, date__month=last_month.month,
        date__year=last_month.year, completed=True).count()

    def diff_label(current, previous):
        if previous == 0:
            return "No data last month"
        diff = current - previous
        pct = abs(int(diff / previous * 100))
        if diff > 0:
            return f"↑ {pct}% more than last month"
        elif diff < 0:
            return f"↓ {pct}% less than last month"
        return "Same as last month"

    return JsonResponse({
        "status": "success",
        "this_month": today.strftime("%B %Y"),
        "last_month": last_month.strftime("%B %Y"),
        "expense": {
            "this": this_expense,
            "last": last_expense,
            "diff": diff_label(this_expense, last_expense),
            "better": this_expense <= last_expense,
        },
        "income": {
            "this": this_income,
            "last": last_income,
            "diff": diff_label(this_income, last_income),
            "better": this_income >= last_income,
        },
        "savings": {
            "this": this_income - this_expense,
            "last": last_income - last_expense,
            "diff": diff_label(this_income - this_expense, last_income - last_expense),
            "better": (this_income - this_expense) >= (last_income - last_expense),
        },
        "tasks": {
            "this": this_tasks,
            "last": last_tasks,
            "diff": diff_label(this_tasks, last_tasks),
            "better": this_tasks >= last_tasks,
        },
        "habits": {
            "this": this_habits,
            "last": last_habits,
            "diff": diff_label(this_habits, last_habits),
            "better": this_habits >= last_habits,
        },
    })
@csrf_exempt
def smart_alerts_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    today = timezone.localdate()
    alerts = []

    # 🔴 1. High spending alert
    month_expense = sum(e.amount for e in Expense.objects.filter(
        user=user, date__month=today.month, date__year=today.year))
    month_income = sum(i.amount for i in Income.objects.filter(
        user=user, date__month=today.month, date__year=today.year))

    if month_income > 0:
        ratio = month_expense / month_income
        if ratio > 0.9:
            alerts.append("⚠️ You are spending more than 90% of your income!")
        elif ratio > 0.7:
            alerts.append("📊 You have used 70% of your income")

    # 🟡 2. Budget alert
    budgets = Budget.objects.filter(user=user, month=today.month, year=today.year)
    for b in budgets:
        spent = sum(e.amount for e in Expense.objects.filter(
            user=user, category=b.category,
            date__month=today.month, date__year=today.year))
        if b.amount > 0:
            percent = spent / b.amount
            if percent >= 0.9:
                alerts.append(f"⚠️ {b.category} budget almost exceeded!")
            elif percent >= 0.7:
                alerts.append(f"📊 {b.category} budget 70% used")

    # 🟢 3. Habit alert
    total_habits = Habit.objects.filter(user=user).count()
    completed = HabitLog.objects.filter(
        habit__user=user, date=today, completed=True).count()

    if total_habits > 0 and completed == 0:
        alerts.append("😴 No habits completed today!")

    # 🔵 4. Task alert
    pending_tasks = Task.objects.filter(user=user, completed=False).count()
    if pending_tasks >= 5:
        alerts.append("📋 You have many pending tasks!")

    if not alerts:
        alerts.append("✅ Everything looks good! Keep going!")

    return JsonResponse({
        "status": "success",
        "alerts": alerts
    })
@csrf_exempt
def behavior_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})

    insights = []
    expenses = Expense.objects.filter(user=user)

    # 📊 Weekend spending
    weekend_expense = 0
    weekday_expense = 0

    for e in expenses:
        if e.date.weekday() >= 5:
            weekend_expense += e.amount
        else:
            weekday_expense += e.amount

    if weekend_expense > weekday_expense:
        insights.append("📅 You spend more on weekends")
    else:
        insights.append("📅 Your spending is balanced across week")

    # 🧠 Habit consistency
    total_logs = HabitLog.objects.filter(habit__user=user).count()
    completed_logs = HabitLog.objects.filter(
        habit__user=user, completed=True).count()

    if total_logs > 0:
        ratio = completed_logs / total_logs
        if ratio > 0.7:
            insights.append("🔥 You are highly consistent with habits!")
        elif ratio > 0.4:
            insights.append("👍 You are moderately consistent")
        else:
            insights.append("⚠️ Try to improve your habit consistency")

    # 📋 Task productivity
    completed_tasks = Task.objects.filter(user=user, completed=True).count()
    total_tasks = Task.objects.filter(user=user).count()

    if total_tasks > 0:
        task_ratio = completed_tasks / total_tasks
        if task_ratio > 0.7:
            insights.append("🚀 You are very productive!")
        else:
            insights.append("📉 Try completing more tasks")

    return JsonResponse({
        "status": "success",
        "insights": insights
    })
def alerts_view(request, user_id):
    alerts = []

    # Example logic
    total_expense = 12000
    budget = 10000
    pending_tasks = 3
    missed_habits = 2

    if total_expense > budget:
        alerts.append("You exceeded your budget")

    if total_expense > 0.8 * budget:
        alerts.append("You are near budget limit")

    if pending_tasks > 0:
        alerts.append("You have pending tasks")

    if missed_habits > 0:
        alerts.append("You missed habits today")

    return JsonResponse({
        "status": "success",
        "alerts": alerts
    })
@csrf_exempt
def goal_view(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "GET":
        goals = Goal.objects.filter(user=user)

        result = []
        for g in goals:
            savings = sum(i.amount for i in Income.objects.filter(user=user)) - \
                      sum(e.amount for e in Expense.objects.filter(user=user))

            progress = (savings / g.target_amount * 100) if g.target_amount > 0 else 0

            result.append({
                "id": g.id,
                "title": g.title,
                "target": g.target_amount,
                "saved": savings,
                "progress": int(progress)
            })

        return JsonResponse({"status": "success", "goals": result})

    if request.method == "POST":
        data = json.loads(request.body)

        g = Goal.objects.create(
            user=user,
            title=data["title"],
            target_amount=float(data["target"])
        )

        return JsonResponse({"status": "success", "id": g.id})
@csrf_exempt

def daily_summary_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error",
            "message": "User not found"
        })

    today = timezone.localdate()

    # 💰 TODAY EXPENSE
    today_expense = sum(

        e.amount for e in Expense.objects.filter(
            user=user,
            date=today
        )
    )

    # 💵 TODAY INCOME
    today_income = sum(

        i.amount for i in Income.objects.filter(
            user=user,
            date=today
        )
    )

    # ✅ TASKS
    total_tasks = Task.objects.filter(
        user=user
    ).count()

    completed_tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    # 🔥 HABITS
    total_habits = Habit.objects.filter(
        user=user
    ).count()

    completed_habits = HabitLog.objects.filter(
        habit__user=user,
        date=today,
        completed=True
    ).count()

    # 😊 MOOD
    mood = Mood.objects.filter(
        user=user,
        date=today
    ).first()

    mood_text = (
        mood.mood if mood else "Not logged"
    )

    # 🧠 PRODUCTIVITY SCORE
    productivity = 0

    if total_tasks > 0:

        productivity += int(
            (completed_tasks / total_tasks)
            * 50
        )

    if total_habits > 0:

        productivity += int(
            (completed_habits / total_habits)
            * 50
        )

    # 🧠 AI MESSAGE
    ai_message = (
        "Good progress today!"
    )

    if today_expense > today_income:

        ai_message = (
            "⚠ You spent more than you earned today."
        )

    elif productivity >= 80:

        ai_message = (
            "🔥 Very productive day!"
        )

    elif productivity <= 40:

        ai_message = (
            "📉 Try improving your productivity tomorrow."
        )

    return JsonResponse({

        "status": "success",

        "today_expense":
            today_expense,

        "today_income":
            today_income,

        "completed_tasks":
            completed_tasks,

        "total_tasks":
            total_tasks,

        "completed_habits":
            completed_habits,

        "total_habits":
            total_habits,

        "mood":
            mood_text,

        "productivity":
            productivity,

        "ai_message":
            ai_message,
    })

@csrf_exempt
def heatmap_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    today = timezone.localdate()

    result = []

    for i in range(30):

        d = today - timedelta(days=i)

        score = 0

        # 🔥 HABITS
        habits = HabitLog.objects.filter(
            habit__user=user,
            date=d,
            completed=True
        ).count()

        score += habits * 2

        # ✅ TASKS
        tasks = Task.objects.filter(
            user=user,
            completed=True
        ).count()

        score += min(tasks, 5)

        # 😊 MOOD
        mood = Mood.objects.filter(
            user=user,
            date=d
        ).exists()

        if mood:
            score += 2

        # 💰 EXPENSE
        expense = Expense.objects.filter(
            user=user,
            date=d
        ).exists()

        if expense:
            score += 1

        result.append({

            "date": str(d),

            "score": score,
        })

    return JsonResponse({

        "status": "success",

        "days": result
    })