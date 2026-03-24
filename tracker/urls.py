from django.urls import path
from .views import (
    login_view,
    signup_view,
    expense_view,
    income_view,
    habit_view,
    habit_log_view,
    task_view,
    mood_view,
    dashboard_view,
    history_view,
)

urlpatterns = [
    # Auth
    path('login/', login_view),
    path('signup/', signup_view),

    # Dashboard
    path('dashboard/<int:user_id>/', dashboard_view),

    # Expenses
    path('expenses/<int:user_id>/', expense_view),

    # Income
    path('income/<int:user_id>/', income_view),

    # Habits
    path('habits/<int:user_id>/', habit_view),
    path('habits/log/<int:habit_id>/', habit_log_view),

    # Tasks
    path('tasks/<int:user_id>/', task_view),

    # Mood
    path('mood/<int:user_id>/', mood_view),

    # History
    path('history/<int:user_id>/', history_view),
]