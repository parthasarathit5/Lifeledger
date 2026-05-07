from django.contrib import admin
from .models import User, Expense, Income, Habit, HabitLog, Task, Mood, History,Budget,  Achievement, Streak,Goal,PasswordResetOTP
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'created_at']
    search_fields = ['name', 'email']
    ordering = ['-created_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'amount', 'category', 'date']
    search_fields = ['title', 'user__email']
    list_filter = ['category', 'date']
    ordering = ['-date']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'amount', 'category', 'date']
    search_fields = ['title', 'user__email']
    list_filter = ['category', 'date']
    ordering = ['-date']


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'icon', 'created_at']
    search_fields = ['name', 'user__email']
    ordering = ['-created_at']


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'habit', 'date', 'completed']
    list_filter = ['completed', 'date']
    ordering = ['-date']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'priority', 'completed', 'completed_at', 'created_at']
    search_fields = ['title', 'user__email']
    list_filter = ['priority', 'completed', 'created_at']
    ordering = ['-created_at']


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'mood', 'date']
    search_fields = ['user__email']
    list_filter = ['mood', 'date']
    ordering = ['-date']


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'title', 'amount', 'category', 'date', 'month', 'year']
    search_fields = ['title', 'user__email']
    list_filter = ['type', 'month', 'year', 'date']
    ordering = ['-date', '-id']
@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'category', 'amount', 'month', 'year']
    search_fields = ['user__email', 'category']
    list_filter = ['month', 'year', 'category']
    ordering = ['-year', '-month']
admin.site.register(Achievement)
admin.site.register(Streak)
admin.site.register(Goal)
admin.site.register(
    PasswordResetOTP
)
admin.site.site_header = "LifeTracer Admin"
admin.site.site_title = "LifeTracer"
admin.site.index_title = "Welcome to LifeTracer Admin Panel"


# Good — this is the right question to ask before jumping ahead 👍
# Let’s make it **super clear and practical** (no confusion).

# ---

# # 🧠 Why are we using Flutter?

# 👉 Because you want:

# ✔ Mobile app 📱
# ✔ Runs on Android (and iOS later)
# ✔ One code → multiple platforms

# ---

# ## 🔥 Without Flutter

# You would need:

# * Java/Kotlin → Android ❌
# * Swift → iOS ❌

# 👉 Too complex

# ---

# ## ✅ With Flutter

# 👉 One code (Dart) → Android + iOS

# ---

# # 🧠 Why VS Code?

# 👉 VS Code is just a **code editor**

# Think:

# * VS Code = place where you **write code**
# * Flutter = framework that **runs the app**

# ---

# # 🧠 Why terminal (IMPORTANT)

# You asked:

# > “why should i run terminal?”

# 👉 Because terminal is how we **talk to Flutter**

# ---

# ## 💡 Simple understanding

# When you type:

# ```bash
# flutter create lifeledger_app
# ```

# 👉 You are telling Flutter:

# > “Create a new app for me”

# ---

# When you type:

# ```bash
# flutter run
# ```

# 👉 You are telling:

# > “Run my app on phone/emulator”

# ---

# # 🔥 Real analogy

# Think like this:

# | Thing    | Example           |
# | -------- | ----------------- |
# | VS Code  | Notebook          |
# | Flutter  | Machine           |
# | Terminal | Remote control 🎮 |

# ---

# # 🎯 What each command does

# ## 🛠️ Create app

# ```bash
# flutter create lifeledger_app
# ```

# 👉 Creates full project structure

# ---

# ## ▶️ Run app

# ```bash
# flutter run
# ```

# 👉 Launches app on emulator/phone

# ---

# ## 🧪 Check setup

# ```bash
# flutter doctor
# ```

# 👉 Checks if everything installed

# ---

# # 🧠 Why not just click buttons?

# 👉 Because:

# * Flutter works via CLI (command line)
# * Faster and powerful
# * Industry standard

# ---

# # 🚀 Your workflow (VERY IMPORTANT)

# ```text
# Write code → Save → Run command → See app
# ```

# ---

# # 💥 Full system you are building

# ```text
# Flutter (UI)
#     ↓
# Django (API)
#     ↓
# PostgreSQL (DB)
# ```

# ---

# # 💪 Final clarity

# 👉 VS Code = write code
# 👉 Flutter = build app
# 👉 Terminal = run commands

# ---

# # 🚀 Now no more confusion

# Just do this:

# ```bash
# flutter doctor
# ```

# ---

# Then:

# 👉 say **“done flutter doctor”**

# We will **build your app UI next** 🔥📱
