from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.timezone import localtime
from django.db.models import Sum, Count
import json
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
            "status": "error"
        })

    # 💰 FINANCE SCORE
    income = sum(
        i.amount
        for i in Income.objects.filter(
            user=user
        )
    )

    expense = sum(
        e.amount
        for e in Expense.objects.filter(
            user=user
        )
    )

    savings = income - expense

    if savings > 20000:

        finance_score = 25

    elif savings > 10000:

        finance_score = 20

    elif savings > 5000:

        finance_score = 15

    else:

        finance_score = 10

    # 🔥 HABITS SCORE
    habits_completed = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    habits_score = min(25, habits_completed)

    # ✅ PRODUCTIVITY SCORE
    tasks_completed = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    productivity_score = min(
        25,
        tasks_completed
    )

    # 😊 MOOD SCORE
    mood_entries = Mood.objects.filter(
        user=user
    ).count()

    mood_score = min(25, mood_entries * 2)

    # 🏆 TOTAL
    total_score = (

        finance_score +

        habits_score +

        productivity_score +

        mood_score
    )

    # 🤖 AI MESSAGE
    if total_score >= 85:

        message = (
            "🔥 Excellent life balance detected."
        )

    elif total_score >= 65:

        message = (
            "👍 Good overall lifestyle consistency."
        )

    elif total_score >= 40:

        message = (
            "📈 Your lifestyle is improving gradually."
        )

    else:

        message = (
            "⚠ Focus on habits, mood, and savings improvement."
        )

    return JsonResponse({

        "status": "success",

        "total_score":
            total_score,

        "finance":
            finance_score,

        "habits":
            habits_score,

        "productivity":
            productivity_score,

        "mood":
            mood_score,

        "message":
            message,
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

    moods = Mood.objects.filter(
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

    completed_habits = HabitLog.objects.filter(
        habit__user=user,
        completed=True
    ).count()

    completed_tasks = Task.objects.filter(
        user=user,
        completed=True
    ).count()

    # 🧠 PERSONALITY
    if savings > 20000:

        personality = "Smart Saver"

    elif total_expense > total_income:

        personality = "Impulsive Spender"

    elif completed_habits > 15:

        personality = "Disciplined Achiever"

    else:

        personality = "Balanced User"

    # 🔥 DISCIPLINE SCORE
    discipline = (
        completed_habits +
        completed_tasks
    )

    if discipline >= 25:

        discipline_msg = (
            "Excellent consistency and discipline"
        )

    elif discipline >= 10:

        discipline_msg = (
            "Moderate productivity pattern"
        )

    else:

        discipline_msg = (
            "Low consistency detected"
        )

    # ⚠ SPENDING PATTERN
    if total_expense > (
        total_income * 0.8
    ):

        spending = (
            "High spending pattern detected"
        )

    elif total_expense > (
        total_income * 0.5
    ):

        spending = (
            "Balanced spending behavior"
        )

    else:

        spending = (
            "Strong saving behavior"
        )

    # 😊 MOOD ANALYSIS
    mood_msg = (
        "Mood data insufficient"
    )

    if moods.exists():

        mood_msg = (
            "Mood tracking indicates emotional awareness"
        )

    # 🤖 AI ADVICE
    if total_expense > total_income:

        advice = (
            "Focus on reducing unnecessary expenses "
            "and improving financial discipline."
        )

    elif completed_habits >= 20:

        advice = (
            "Your consistency habits are excellent. "
            "Maintain this routine for long-term success."
        )

    else:

        advice = (
            "Small daily improvements in habits and "
            "expense control can significantly improve "
            "your lifestyle balance."
        )

    return JsonResponse({

        "status": "success",

        "personality":
            personality,

        "discipline":
            discipline_msg,

        "spending":
            spending,

        "mood":
            mood_msg,

        "advice":
            advice,
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

    streaks = Streak.objects.filter(
        user=user
    )

    result = []

    for s in streaks:

        result.append({

            "type":
                s.streak_type,

            "current":
                s.current_streak,

            "longest":
                s.longest_streak,
        })

    return JsonResponse({

        "status": "success",

        "streaks":
            result
    })
@csrf_exempt
def achievements_view(request, user_id):

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:

        return JsonResponse({
            "status": "error"
        })

    achievements = Achievement.objects.filter(
        user=user
    )

    result = []

    for a in achievements:

        result.append({

            "title":
                a.title,

            "description":
                a.description,

            "icon":
                a.icon,

            "date":
                str(a.created_at),
        })

    return JsonResponse({

        "status": "success",

        "achievements":
            result
    })