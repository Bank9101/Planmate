from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    credits = models.IntegerField()
    semester = models.CharField(max_length=20)  # e.g., "1/2567", "2/2567"
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_subjects', null=True, blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Event(models.Model):
    EVENT_TYPES = [
        ('class', 'Class'),
        ('exam', 'Exam'),
        ('lab', 'Lab'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    repeat_weekly = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.subject.code} - {self.get_event_type_display()}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    enrolled_subjects = models.ManyToManyField(Subject, blank=True, related_name='enrolled_students')
    scheduled_subjects = models.ManyToManyField(Subject, blank=True, related_name='scheduled_by_students')
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    managed_subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"