from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.timezone import localtime  # ✅ Added this
import json
from .models import User, Expense, Income, Habit, HabitLog, Task, Mood, History

def save_history(user, type, title, amount=None, category="", note=""):
    today = timezone.localdate()  # ✅ Fixed: uses IST date now
    History.objects.create(
        user=user,
        type=type,
        title=title,
        amount=amount,
        category=category,
        note=note,
        date=today,
        month=today.month,
        year=today.year,
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
                # ✅ Added IST login time
                "login_time": localtime(timezone.now()).strftime('%d-%m-%Y %I:%M %p'),
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid email or password"
            })
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    })

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
            return JsonResponse({
                "status": "error",
                "message": "All fields are required"
            })
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                "status": "error",
                "message": "Email already registered"
            })
        user = User.objects.create(
            name=name,
            email=email,
            password=make_password(password)
        )
        return JsonResponse({
            "status": "success",
            "user_id": user.id,
            "name": user.name,
            # ✅ Added IST signup time
            "created_at": localtime(timezone.now()).strftime('%d-%m-%Y %I:%M %p'),
        })
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    })

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
            "type": "expense",
            "title": e.title,
            "category": e.category,
            "amount": e.amount,
            "date": str(e.date),
        })
    for i in recent_incomes:
        transactions.append({
            "type": "income",
            "title": i.title,
            "category": i.category,
            "amount": i.amount,
            "date": str(i.date),
        })
    transactions.sort(key=lambda x: x["date"], reverse=True)
    total_habits = Habit.objects.filter(user=user).count()
    today = timezone.localdate()  # ✅ Fixed: IST date
    completed_habits = HabitLog.objects.filter(
        habit__user=user, date=today, completed=True
    ).count()
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
            "expenses": [
                {
                    "id": e.id,
                    "title": e.title,
                    "amount": e.amount,
                    "category": e.category,
                    "date": str(e.date),
                    "note": e.note,
                }
                for e in expenses
            ]
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
            user=user,
            title=title,
            amount=float(amount),
            category=category,
            note=note,
        )
        save_history(user=user, type='expense', title=title,
                     amount=float(amount), category=category, note=note)
        return JsonResponse({"status": "success", "id": expense.id})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        expense_id = data.get("id")
        Expense.objects.filter(id=expense_id, user=user).delete()
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
            "incomes": [
                {
                    "id": i.id,
                    "title": i.title,
                    "amount": i.amount,
                    "category": i.category,
                    "date": str(i.date),
                    "note": i.note,
                }
                for i in incomes
            ]
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
            user=user,
            title=title,
            amount=float(amount),
            category=category,
            note=note,
        )
        save_history(user=user, type='income', title=title,
                     amount=float(amount), category=category, note=note)
        return JsonResponse({"status": "success", "id": income.id})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        income_id = data.get("id")
        Income.objects.filter(id=income_id, user=user).delete()
        return JsonResponse({"status": "success"})

@csrf_exempt
def habit_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    if request.method == "GET":
        today = timezone.localdate()  # ✅ Fixed: IST date
        habits = Habit.objects.filter(user=user)
        return JsonResponse({
            "status": "success",
            "habits": [
                {
                    "id": h.id,
                    "name": h.name,
                    "icon": h.icon,
                    "completed_today": HabitLog.objects.filter(
                        habit=h, date=today, completed=True
                    ).exists(),
                }
                for h in habits
            ]
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
        habit_id = data.get("id")
        Habit.objects.filter(id=habit_id, user=user).delete()
        return JsonResponse({"status": "success"})

@csrf_exempt
def habit_log_view(request, habit_id):
    try:
        habit = Habit.objects.get(id=habit_id)
    except Habit.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Habit not found"})
    if request.method == "POST":
        today = timezone.localdate()  # ✅ Fixed: IST date
        log, created = HabitLog.objects.get_or_create(habit=habit, date=today)
        log.completed = not log.completed
        log.save()
        if log.completed:
            save_history(
                user=habit.user,
                type='habit',
                title=f"Completed habit: {habit.name}",
                category=habit.icon,
            )
        return JsonResponse({
            "status": "success",
            "completed": log.completed,
        })

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
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority,
                    "completed": t.completed,
                    "completed_at": str(t.completed_at) if t.completed_at else None,
                    "due_date": str(t.due_date) if t.due_date else None,
                    "created_at": str(t.created_at),
                }
                for t in tasks
            ]
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
        task = Task.objects.create(
            user=user,
            title=title,
            priority=priority,
            due_date=due_date,
        )
        return JsonResponse({"status": "success", "id": task.id})
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        task_id = data.get("id")
        task = Task.objects.filter(id=task_id, user=user).first()
        if task:
            task.completed = not task.completed
            if task.completed:
                task.completed_at = timezone.localdate()  # ✅ Fixed: IST date
                save_history(
                    user=user,
                    type='task',
                    title=f"Completed task: {task.title}",
                    category=task.priority,
                )
            else:
                task.completed_at = None
            task.save()
        return JsonResponse({"status": "success"})
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"status": "error", "message": "Invalid request"})
        task_id = data.get("id")
        Task.objects.filter(id=task_id, user=user).delete()
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
            "moods": [
                {
                    "id": m.id,
                    "mood": m.mood,
                    "note": m.note,
                    "date": str(m.date),
                }
                for m in moods
            ]
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
        save_history(
            user=user,
            type='mood',
            title=f"Mood logged: {mood}",
            note=note,
        )
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
            "history": [
                {
                    "id": h.id,
                    "type": h.type,
                    "title": h.title,
                    "amount": h.amount,
                    "category": h.category,
                    "note": h.note,
                    "date": str(h.date),
                    "month": h.month,
                    "year": h.year,
                }
                for h in history
            ]
        })