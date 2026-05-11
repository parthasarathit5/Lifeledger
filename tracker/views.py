from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Sum, Count
import json
from django.core.mail import send_mail
import random
from datetime import date, timedelta
from .models import User, Expense, Income, Habit, HabitLog, Task, History,Budget,Goal,Achievement,Streak


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

        return JsonResponse({

            "score": 0,

            "insight":
                "User not found."
        })

    income = sum(

        i.amount for i in
        Income.objects.filter(
            user=user
        )
    )

    expense = sum(

        e.amount for e in
        Expense.objects.filter(
            user=user
        )
    )

    habits = HabitLog.objects.filter(

        habit__user=user,

        completed=True
    ).count()

    tasks = Task.objects.filter(

        user=user,

        completed=True
    ).count()

    moods = Mood.objects.filter(
        user=user
    ).count()

    savings = income - expense

    score = 0

    # 💰 FINANCE
    if savings > 0:

        score += 30

    elif income > 0:

        score += 15

    # 🔥 HABITS
    score += min(habits, 20)

    # ✅ TASKS
    score += min(tasks, 25)

    # 😊 MOODS
    score += min(moods, 25)

    score = min(score, 100)

    # 🤖 AI INSIGHT
    if score >= 80:

        insight = (
            "Excellent lifestyle balance and productivity detected."
        )

    elif score >= 50:

        insight = (
            "Your habits and financial behavior are improving steadily."
        )

    elif score >= 20:

        insight = (
            "Growth has started, but more consistency is needed."
        )

    else:

        insight = (
            "Start tracking activities to unlock advanced AI analysis."
        )

    return JsonResponse({

        "score":
            score,

        "insight":
            insight,
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

        return JsonResponse({
            "status": "error"
        })

    incomes = Income.objects.filter(
        user=user
    )

    expenses = Expense.objects.filter(
        user=user
    )

    habits = Habit.objects.filter(
        user=user
    )

    tasks = Task.objects.filter(
        user=user
    )

    total_income = sum(
        i.amount for i in incomes
    )

    total_expense = sum(
        e.amount for e in expenses
    )

    savings = (
        total_income -
        total_expense
    )

    # 🔮 FUTURE SAVINGS
    predicted_savings = int(
        savings * 1.15
    )

    # ⚠ RISK
    if total_expense > total_income:

        risk = "High Overspending Risk"

    elif savings < 5000:

        risk = "Moderate Savings Risk"

    else:

        risk = "Financially Stable"

    # 🔥 PRODUCTIVITY
    completed_habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    completed_tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    productivity = (
        completed_habits +
        completed_tasks
    )

    if productivity >= 20:

        productivity_msg = (
            "Excellent productivity trend"
        )

    elif productivity >= 10:

        productivity_msg = (
            "Good consistency detected"
        )

    else:

        productivity_msg = (
            "Low productivity pattern"
        )

    # 🎯 GOAL ESTIMATION
    goals = Goal.objects.filter(
        user=user,
        completed=False
    )

    goal_msg = "No active goals"

    if goals.exists():

        g = goals.first()

        remaining = (
            g.target_amount -
            g.current_amount
        )

        if predicted_savings > 0:

            months = max(
                1,
                int(
                    remaining /
                    predicted_savings
                )
            )

            goal_msg = (
                f"You may complete "
                f"{g.title} in "
                f"{months} month(s)"
            )

    # 🤖 AI ADVICE
    if total_expense > total_income:

        advice = (
            "Reduce unnecessary expenses "
            "immediately to avoid "
            "financial stress."
        )

    elif savings > 20000:

        advice = (
            "Excellent savings trend. "
            "Consider investing for "
            "long-term growth."
        )

    else:

        advice = (
            "Improving habit consistency "
            "and reducing small daily "
            "expenses can improve savings."
        )

    return JsonResponse({

        "status": "success",

        "income":
            total_income,

        "expense":
            total_expense,

        "savings":
            savings,

        "predicted_savings":
            predicted_savings,

        "risk":
            risk,

        "productivity":
            productivity_msg,

        "goal_prediction":
            goal_msg,

        "advice":
            advice,
    })
# ============================================================
# NEW FEATURE 5 — COMPARE MONTH
# ============================================================
@csrf_exempt
def compare_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    # 💰 FINANCE
    income = sum(
        i.amount for i in
        Income.objects.filter(user=user)
    )

    expense = sum(
        e.amount for e in
        Expense.objects.filter(user=user)
    )

    savings = income - expense

    # 🔥 HABITS
    habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    # ✅ TASKS
    tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    # 😊 MOODS
    moods = Mood.objects.filter(
        user=user
    ).count()

    # 📈 COMPARISON ENGINE
    if savings >= 20000:

        savings_msg = (
            "Savings improved significantly."
        )

    elif savings >= 5000:

        savings_msg = (
            "Savings are stable."
        )

    else:

        savings_msg = (
            "Savings growth is low."
        )

    if expense > income:

        expense_msg = (
            "Expenses are higher than income."
        )

    else:

        expense_msg = (
            "Expense control looks healthy."
        )

    if habits >= 20:

        habit_msg = (
            "Habit consistency improved strongly."
        )

    elif habits >= 10:

        habit_msg = (
            "Habit routine is moderately stable."
        )

    else:

        habit_msg = (
            "Habit consistency needs improvement."
        )

    if tasks >= 20:

        task_msg = (
            "Excellent productivity trend."
        )

    elif tasks >= 10:

        task_msg = (
            "Task completion improving gradually."
        )

    else:

        task_msg = (
            "Low productivity consistency."
        )

    if moods >= 15:

        mood_msg = (
            "Strong emotional awareness detected."
        )

    elif moods >= 5:

        mood_msg = (
            "Mood tracking improving."
        )

    else:

        mood_msg = (
            "Very little mood tracking data."
        )

    # 🤖 AI INSIGHT
    if savings > 20000 and habits > 20:

        insight = (
            "Your financial discipline and "
            "productivity are improving together."
        )

    elif expense > income:

        insight = (
            "Overspending may affect long-term "
            "financial stability."
        )

    else:

        insight = (
            "Your lifestyle balance is improving gradually."
        )

    return JsonResponse({

        "status": "success",

        "savings":
            savings_msg,

        "expense":
            expense_msg,

        "habits":
            habit_msg,

        "tasks":
            task_msg,

        "mood":
            mood_msg,

        "insight":
            insight,
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

        return JsonResponse({
            "status": "error"
        })

    income = sum(
        i.amount for i in
        Income.objects.filter(user=user)
    )

    expense = sum(
        e.amount for e in
        Expense.objects.filter(user=user)
    )

    savings = income - expense

    completed_tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    pending_tasks = Task.objects.filter(
        user=user,
        completed=False
    ).count()

    completed_habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    moods = Mood.objects.filter(
        user=user
    ).count()

    # 🧠 PERSONALITY ENGINE
    if savings > 30000 and completed_habits > 20:

        personality = (
            "Strategic Achiever"
        )

    elif expense > income:

        personality = (
            "Risky Spender"
        )

    elif completed_tasks > 20:

        personality = (
            "Productivity Focused"
        )

    elif moods > 10:

        personality = (
            "Emotionally Aware"
        )

    else:

        personality = (
            "Balanced Explorer"
        )

    # 🔥 FINANCE ANALYSIS
    if savings > 20000:

        finance = (
            "Excellent savings discipline detected."
        )

    elif savings > 5000:

        finance = (
            "Moderate financial stability."
        )

    else:

        finance = (
            "Savings growth needs improvement."
        )

    # 🔥 PRODUCTIVITY ANALYSIS
    if completed_tasks > pending_tasks:

        productivity = (
            "Strong productivity consistency."
        )

    else:

        productivity = (
            "Task completion rate is low."
        )

    # 🔥 HABIT ANALYSIS
    if completed_habits >= 25:

        habits = (
            "Outstanding habit consistency."
        )

    elif completed_habits >= 10:

        habits = (
            "Good routine stability."
        )

    else:

        habits = (
            "Habits require stronger consistency."
        )

    # 😊 MOOD ANALYSIS
    if moods >= 15:

        mood = (
            "Excellent emotional tracking awareness."
        )

    elif moods >= 5:

        mood = (
            "Moderate emotional awareness."
        )

    else:

        mood = (
            "Mood tracking data insufficient."
        )

    # 🤖 AI RECOMMENDATION
    if expense > income:

        advice = (
            "Your spending trend is risky. "
            "Reduce unnecessary expenses "
            "to avoid financial instability."
        )

    elif pending_tasks > completed_tasks:

        advice = (
            "Improving task completion consistency "
            "can significantly improve productivity."
        )

    elif completed_habits >= 20:

        advice = (
            "Your discipline level is excellent. "
            "Maintain this consistency for long-term success."
        )

    else:

        advice = (
            "Small daily improvements across habits, "
            "finance, and productivity will create "
            "major long-term growth."
        )

    return JsonResponse({

        "status": "success",

        "personality":
            personality,

        "finance":
            finance,

        "productivity":
            productivity,

        "habits":
            habits,

        "mood":
            mood,

        "advice":
            advice,
    })
@csrf_exempt
def alerts_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    alerts = []

    # 💰 FINANCE
    income = sum(
        i.amount for i in
        Income.objects.filter(user=user)
    )

    expense = sum(
        e.amount for e in
        Expense.objects.filter(user=user)
    )

    savings = income - expense

    if expense > income:

        alerts.append({

            "title":
                "Overspending Alert",

            "message":
                "Your expenses are higher than your income.",

            "type":
                "danger",
        })

    elif savings > 20000:

        alerts.append({

            "title":
                "Savings Growth",

            "message":
                "Excellent savings consistency detected.",

            "type":
                "success",
        })

    else:

        alerts.append({

            "title":
                "Finance Update",

            "message":
                "Your financial balance is moderately stable.",

            "type":
                "info",
        })

    # 🔥 HABITS
    habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    if habits >= 20:

        alerts.append({

            "title":
                "Habit Consistency",

            "message":
                "Your habit streak is improving strongly.",

            "type":
                "success",
        })

    elif habits < 5:

        alerts.append({

            "title":
                "Habit Warning",

            "message":
                "Your routine consistency is dropping.",

            "type":
                "warning",
        })

    # ✅ TASKS
    completed_tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    pending_tasks = Task.objects.filter(
        user=user,
        completed=False
    ).count()

    if pending_tasks > completed_tasks:

        alerts.append({

            "title":
                "Productivity Alert",

            "message":
                "Pending tasks are increasing rapidly.",

            "type":
                "danger",
        })

    else:

        alerts.append({

            "title":
                "Productivity Growth",

            "message":
                "Task completion consistency is improving.",

            "type":
                "success",
        })

    # 😊 MOOD
    moods = Mood.objects.filter(
        user=user
    ).count()

    if moods >= 10:

        alerts.append({

            "title":
                "Mood Tracking",

            "message":
                "Your emotional awareness is improving.",

            "type":
                "info",
        })

    else:

        alerts.append({

            "title":
                "Mood Reminder",

            "message":
                "Track moods more consistently for better insights.",

            "type":
                "warning",
        })

    # 🎯 GOALS
    goals = Goal.objects.filter(
        user=user,
        completed=False
    )

    if goals.exists():

        alerts.append({

            "title":
                "Goal Progress",

            "message":
                "Your active goals are progressing steadily.",

            "type":
                "success",
        })

    else:

        alerts.append({

            "title":
                "Goal Suggestion",

            "message":
                "Create goals to improve motivation and tracking.",

            "type":
                "info",
        })

    return JsonResponse({

        "status": "success",

        "alerts":
            alerts,
    })
@csrf_exempt
def goal_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    # ➕ CREATE GOAL
    if request.method == "POST":

        data = json.loads(
            request.body
        )

        Goal.objects.create(

            user=user,

            title=data.get(
                "title"
            ),

            target_amount=data.get(
                "target_amount"
            ),

            current_amount=data.get(
                "current_amount",
                0
            ),

            completed=False,
        )

        return JsonResponse({

            "status":
                "success"
        })

    # 📥 FETCH GOALS
    goals = Goal.objects.filter(
        user=user
    )

    result = []

    # 💰 USER SAVINGS
    income = sum(
        i.amount for i in
        Income.objects.filter(
            user=user
        )
    )

    expense = sum(
        e.amount for e in
        Expense.objects.filter(
            user=user
        )
    )

    savings = income - expense

    for g in goals:

        progress = 0

        if g.target_amount > 0:

            progress = int(

                (g.current_amount /
                 g.target_amount) * 100
            )

        # 🔮 PREDICTION
        months = 0

        remaining = (
            g.target_amount -
            g.current_amount
        )

        if savings > 0:

            months = max(
                1,
                int(
                    remaining /
                    savings
                )
            )

        # 🤖 AI STATUS
        if progress >= 80:

            status = (
                "Goal almost completed."
            )

        elif progress >= 40:

            status = (
                "Good progress detected."
            )

        else:

            status = (
                "Progress needs improvement."
            )

        result.append({

            "title":
                g.title,

            "target":
                g.target_amount,

            "current":
                g.current_amount,

            "progress":
                progress,

            "prediction":
                f"{months} month(s) remaining",

            "status":
                status,
        })

    return JsonResponse({

        "status": "success",

        "goals": result,
    })
@csrf_exempt
def daily_summary_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({

            "status":
                "error",

            "summary":
                "User not found."
        })

    # 💰 FINANCE
    income = sum(

        i.amount for i in
        Income.objects.filter(
            user=user
        )
    )

    expense = sum(

        e.amount for e in
        Expense.objects.filter(
            user=user
        )
    )

    savings = income - expense

    # 🔥 HABITS
    habits = HabitLog.objects.filter(

        habit__user=user,

        completed=True
    ).count()

    # ✅ TASKS
    tasks = Task.objects.filter(

        user=user,

        completed=True
    ).count()

    # 😊 MOODS
    moods = Mood.objects.filter(
        user=user
    ).count()

    # 🎯 GOALS
    goals = Goal.objects.filter(
        user=user
    ).count()

    # 🤖 AI SUMMARY
    summary_parts = []

    # FINANCE
    if income == 0 and expense == 0:

        summary_parts.append(

            "💰 Start tracking income and expenses to unlock financial AI insights."
        )

    elif savings > 20000:

        summary_parts.append(

            "📈 Strong savings growth detected this period."
        )

    elif expense > income:

        summary_parts.append(

            "⚠ Expenses are currently higher than income."
        )

    else:

        summary_parts.append(

            "💰 Financial balance is moderately stable."
        )

    # HABITS
    if habits >= 20:

        summary_parts.append(

            "🔥 Excellent habit consistency detected."
        )

    elif habits > 0:

        summary_parts.append(

            "🔥 Your routines are gradually improving."
        )

    else:

        summary_parts.append(

            "🔥 Add habits to build consistency tracking."
        )

    # TASKS
    if tasks >= 15:

        summary_parts.append(

            "✅ Productivity performance is improving rapidly."
        )

    elif tasks > 0:

        summary_parts.append(

            "✅ Task completion is progressing steadily."
        )

    else:

        summary_parts.append(

            "✅ Start completing tasks to unlock productivity analysis."
        )

    # MOOD
    if moods >= 10:

        summary_parts.append(

            "😊 Emotional awareness tracking is improving."
        )

    elif moods > 0:

        summary_parts.append(

            "😊 Mood tracking activity detected."
        )

    else:

        summary_parts.append(

            "😊 Add mood entries for emotional AI insights."
        )

    # GOALS
    if goals > 0:

        summary_parts.append(

            "🎯 Active goals are helping growth progression."
        )

    else:

        summary_parts.append(

            "🎯 Create goals to improve long-term planning."
        )

    # FINAL AI INSIGHT
    summary_parts.append(

        "🤖 LifeLedger AI continuously adapts insights based on your financial, behavioral and productivity patterns."
    )

    final_summary = "\n\n".join(
        summary_parts
    )

    return JsonResponse({

        "status":
            "success",

        "summary":
            final_summary,

        "income":
            income,

        "expense":
            expense,

        "savings":
            savings,

        "habits":
            habits,

        "tasks":
            tasks,

        "moods":
            moods,

        "goals":
            goals,
    })
@csrf_exempt
def heatmap_view(request, user_id):

    try:

        user = User.objects.get(
            id=user_id
        )

        moods = Mood.objects.filter(
            user=user
        ).order_by("-date")[:30]

        tasks = Task.objects.filter(
            user=user,
            completed=True
        )

        habit_logs = HabitLog.objects.filter(
            habit__user=user,
            completed=True
        )

        heatmap = []

        for i in range(1, 31):

            score = 0

            # 😊 mood contribution
            if moods.count() >= i:
                score += 30

            # ✅ task contribution
            if tasks.count() >= i:
                score += 40

            # 🔥 habit contribution
            if habit_logs.count() >= i:
                score += 30

            score = max(
                0,
                min(100, score)
            )

            level = "low"

            if score >= 80:

                level = "excellent"

            elif score >= 40:

                level = "average"

            heatmap.append({

                "day": i,

                "score": score,

                "level": level,
            })

        # 🤖 AI insight
        insight = ""

        avg_score = sum(
            d["score"] for d in heatmap
        ) / len(heatmap)

        if avg_score >= 70:

            insight = (
                "🔥 Strong lifestyle consistency detected this month."
            )

        elif avg_score >= 40:

            insight = (
                "📈 Your routines are improving steadily."
            )

        else:

            insight = (
                "⚠ Activity levels are low. Start tracking daily habits and moods."
            )

        return JsonResponse({

            "status":
                "success",

            "days":
                heatmap,

            "insight":
                insight,
        })

    except Exception as e:

        print("HEATMAP ERROR:", e)

        return JsonResponse({

            "status":
                "error",

            "days": [],

            "insight":
                "Unable to generate heatmap currently."
        })
@csrf_exempt
def networth_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    total_income = sum(

        i.amount for i in Income.objects.filter(
            user=user
        )
    )

    total_expense = sum(

        e.amount for e in Expense.objects.filter(
            user=user
        )
    )

    networth = (
        total_income -
        total_expense
    )

    # 📈 SAVINGS RATE
    savings_rate = 0

    if total_income > 0:

        savings_rate = int(

            (networth / total_income)
            * 100
        )

    # 🧠 FINANCIAL HEALTH
    if savings_rate >= 50:

        health = "Excellent"

        color = "green"

    elif savings_rate >= 25:

        health = "Good"

        color = "blue"

    elif savings_rate >= 10:

        health = "Average"

        color = "orange"

    else:

        health = "Poor"

        color = "red"

    # 🤖 AI MESSAGE
    if savings_rate >= 50:

        ai = (
            "🔥 Amazing savings discipline!"
        )

    elif savings_rate >= 25:

        ai = (
            "👍 Good financial management."
        )

    else:

        ai = (
            "⚠ Try reducing expenses and saving more."
        )

    return JsonResponse({

        "status": "success",

        "total_income":
            total_income,

        "total_expense":
            total_expense,

        "networth":
            networth,

        "savings_rate":
            savings_rate,

        "health":
            health,

        "color":
            color,

        "ai":
            ai,
    })
@csrf_exempt
def streaks_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    # 🔥 HABITS
    habit_streak = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    # ✅ TASKS
    task_streak = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    # 😊 MOODS
    mood_streak = Mood.objects.filter(
        user=user
    ).count()

    # 💰 SAVINGS
    income = sum(
        i.amount for i in
        Income.objects.filter(user=user)
    )

    expense = sum(
        e.amount for e in
        Expense.objects.filter(user=user)
    )

    savings = income - expense

    saving_streak = 0

    if savings > 20000:

        saving_streak = 30

    elif savings > 10000:

        saving_streak = 20

    elif savings > 5000:

        saving_streak = 10

    else:

        saving_streak = 3

    # 🧠 AI INSIGHT
    if habit_streak >= 20:

        insight = (
            "Excellent consistency and discipline detected."
        )

    elif task_streak > habit_streak:

        insight = (
            "Productivity growth is improving rapidly."
        )

    elif savings < 5000:

        insight = (
            "Financial consistency requires improvement."
        )

    else:

        insight = (
            "Your lifestyle consistency is gradually improving."
        )

    return JsonResponse({

        "status": "success",

        "habit_streak":
            habit_streak,

        "task_streak":
            task_streak,

        "mood_streak":
            mood_streak,

        "saving_streak":
            saving_streak,

        "insight":
            insight,
    })
@csrf_exempt
def achievements_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    achievements = []

    income_count = Income.objects.filter(
        user=user
    ).count()

    habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    moods = Mood.objects.filter(
        user=user
    ).count()

    if income_count >= 1:

        achievements.append({

            "title":
                "First Earner",

            "icon":
                "💰",

            "description":
                "Added first income successfully.",
        })

    if habits >= 20:

        achievements.append({

            "title":
                "Discipline Master",

            "icon":
                "🔥",

            "description":
                "Excellent habit consistency achieved.",
        })

    if tasks >= 25:

        achievements.append({

            "title":
                "Productivity Pro",

            "icon":
                "⚡",

            "description":
                "Outstanding task completion performance.",
        })

    if moods >= 15:

        achievements.append({

            "title":
                "Self Awareness",

            "icon":
                "😊",

            "description":
                "Strong emotional tracking awareness.",
        })

    if len(achievements) == 0:

        achievements.append({

            "title":
                "Starting Journey",

            "icon":
                "🚀",

            "description":
                "Begin improving habits and productivity.",
        })

    return JsonResponse({

        "status": "success",

        "achievements":
            achievements,
    })
@csrf_exempt
def forgot_password_view(request):

    if request.method == "POST":

        data = json.loads(
            request.body
        )

        email = data.get("email")

        print("EMAIL:", email)

        try:

            user = User.objects.get(
                email=email
            )

            print("USER FOUND")

        except User.DoesNotExist:

            print("USER NOT FOUND")

            return JsonResponse({

                "status":
                    "error",

                "message":
                    "Email not found"
            })

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        print("OTP:", otp)

        PasswordResetOTP.objects.create(

            email=email,

            otp=otp
        )

        send_mail(

            'LifeLedger OTP',

            f'Your OTP is {otp}',

            EMAIL_HOST_USER,

            [email],

            fail_silently=False,
        )

        print("MAIL SENT")

        return JsonResponse({

            "status":
                "success"
        })
@csrf_exempt
def verify_otp_view(request):

    data = json.loads(
        request.body
    )

    email = data.get("email")

    otp = data.get("otp")

    exists = PasswordResetOTP.objects.filter(

        email=email,

        otp=otp
    ).exists()

    if exists:

        return JsonResponse({

            "status":
                "success"
        })

    return JsonResponse({

        "status":
            "error"
    })
@csrf_exempt
def reset_password_view(request):

    data = json.loads(
        request.body
    )

    email = data.get("email")

    password = data.get("password")

    try:

        user = User.objects.get(
            email=email
        )

        user.password = password

        user.save()

        return JsonResponse({

            "status":
                "success"
        })

    except:

        return JsonResponse({

            "status":
                "error"
        })