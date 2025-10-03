from django.contrib import admin
from .models import Subject, Event, Student, Teacher

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'semester')
    list_filter = ('semester',)
    search_fields = ('code', 'name')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('subject', 'event_type', 'start_time', 'end_time', 'location')
    list_filter = ('event_type', 'subject')
    search_fields = ('subject__code', 'subject__name', 'location')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'student_id')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'teacher_id')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'teacher_id')