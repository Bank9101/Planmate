from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:subject_id>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:subject_id>/events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('subjects/<int:subject_id>/enroll/', views.enroll_subject, name='enroll_subject'),
    path('subjects/<int:subject_id>/unenroll/', views.unenroll_subject, name='unenroll_subject'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('api/events/', views.get_events, name='get_events'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
]