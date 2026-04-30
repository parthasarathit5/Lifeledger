from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100, default="")
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.email


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food & Dining'),
        ('rent', 'Rent'),
        ('transport', 'Transport'),
        ('shopping', 'Shopping'),
        ('health', 'Health'),
        ('entertainment', 'Entertainment'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses', null=True)
    title = models.CharField(max_length=100, default="Untitled")
    amount = models.FloatField(default=0.0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


class Income(models.Model):
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('freelance', 'Freelance'),
        ('business', 'Business'),
        ('investment', 'Investment'),
        ('gift', 'Gift'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes', null=True)
    title = models.CharField(max_length=100, default="Untitled")
    amount = models.FloatField(default=0.0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits', null=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="⭐")
    created_at = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(auto_now_add=True)
    completed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', null=True)
    title = models.CharField(max_length=200, default="")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title


class Mood(models.Model):
    MOOD_CHOICES = [
        ('great', '😄 Great'),
        ('good', '🙂 Good'),
        ('okay', '😐 Okay'),
        ('bad', '😔 Bad'),
        ('terrible', '😢 Terrible'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moods', null=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    note = models.TextField(blank=True, default="")
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.mood} - {self.date}"


class History(models.Model):
    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
        ('task', 'Task Completed'),
        ('habit', 'Habit Completed'),
        ('mood', 'Mood Logged'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history', null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200, default="")
    amount = models.FloatField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, default="")
    note = models.TextField(blank=True, default="")
    date = models.DateField(auto_now_add=True)
    month = models.IntegerField(default=1)
    year = models.IntegerField(default=2026)

    def __str__(self):
        return f"{self.user} - {self.type} - {self.date}"
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets', null=True)
    category = models.CharField(max_length=50)
    amount = models.FloatField(default=0.0)
    month = models.IntegerField(default=1)
    year = models.IntegerField(default=2026)

    def __str__(self):
        return f"{self.user} - {self.category} - {self.amount}"