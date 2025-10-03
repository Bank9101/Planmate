from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.core.serializers import serialize
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from .models import Subject, Event, Student, Teacher
from .forms import SubjectForm, EventForm
from django.contrib.auth.models import User
import json

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create student profile by default
            Student.objects.create(user=user, student_id=f"ST{user.id}")
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Get subjects created by this user
    subjects = Subject.objects.filter(created_by=request.user)
    
    # Get upcoming events for the user's subjects
    events = Event.objects.filter(subject__in=subjects).filter(end_time__gte=timezone.now()).order_by('start_time')[:5]
    
    # Get scheduled subjects for students
    scheduled_subjects = []
    if hasattr(request.user, 'student'):
        scheduled_subjects = request.user.student.scheduled_subjects.all()
    
    context = {
        'upcoming_events': events,
        'subjects': subjects,
        'scheduled_subjects': scheduled_subjects,
    }
    return render(request, 'dashboard.html', context)

@login_required
def subject_list(request):
    if request.method == 'POST':
        # Handle subject creation for any logged-in user
        if 'delete_subject' in request.POST:
            # Handle subject deletion
            subject_id = request.POST.get('subject_id')
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Check if user owns this subject
            if subject.created_by != request.user:
                messages.error(request, 'You do not have permission to delete this subject.')
                return redirect('subject_list')
            
            subject_name = subject.name
            subject.delete()
            messages.success(request, f'Subject "{subject_name}" deleted successfully!')
            return redirect('subject_list')
        else:
            # Handle subject creation
            form = SubjectForm(request.POST)
            if form.is_valid():
                subject = form.save(commit=False)
                subject.created_by = request.user
                subject.save()
                messages.success(request, f'Subject "{subject.name}" created successfully!')
                return redirect('subject_list')
            else:
                messages.error(request, 'Error creating subject. Please check the form.')
    
    # Show subjects created by this user
    subjects = Subject.objects.filter(created_by=request.user)
    
    # Get all subjects for enrollment (except those already scheduled)
    all_subjects = Subject.objects.exclude(created_by=request.user)
    scheduled_subject_ids = []
    if hasattr(request.user, 'student'):
        scheduled_subject_ids = request.user.student.scheduled_subjects.values_list('id', flat=True)
    
    # Prepare form for creating new subjects
    form = SubjectForm()
    
    context = {
        'subjects': subjects,
        'all_subjects': all_subjects,
        'scheduled_subject_ids': scheduled_subject_ids,
        'form': form,
    }
    return render(request, 'subjects/list.html', context)

@login_required
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if the user owns this subject or has scheduled it
    is_owner = subject.created_by == request.user
    is_scheduled = False
    if hasattr(request.user, 'student'):
        is_scheduled = request.user.student.scheduled_subjects.filter(id=subject_id).exists()
    
    if not is_owner and not is_scheduled:
        messages.error(request, 'You do not have permission to view this subject.')
        return redirect('subject_list')
    
    # Handle event creation
    if request.method == 'POST' and is_owner:
        if 'delete_subject' in request.POST:
            # Handle subject deletion
            subject_name = subject.name
            subject.delete()
            messages.success(request, f'Subject "{subject_name}" deleted successfully!')
            return redirect('subject_list')
        elif 'delete_event' in request.POST:
            # Handle event deletion
            event_id = request.POST.get('event_id')
            event = get_object_or_404(Event, id=event_id, subject=subject)
            event_type = event.get_event_type_display()
            event.delete()
            messages.success(request, f'Event "{event_type}" deleted successfully!')
            return redirect('subject_detail', subject_id=subject.id)
        else:
            # Handle event creation
            form = EventForm(request.POST)
            if form.is_valid():
                event = form.save()
                messages.success(request, f'Event "{event.get_event_type_display()}" created successfully!')
                return redirect('subject_detail', subject_id=subject.id)
            else:
                messages.error(request, 'Error creating event. Please check the form.')
                events = Event.objects.filter(subject=subject)
                form = EventForm(request.POST)  # Return form with errors
    else:
        events = Event.objects.filter(subject=subject)
        # Prepare form for creating new events (only for owners)
        form = EventForm(initial={'subject': subject}) if is_owner else None
    
    context = {
        'subject': subject,
        'events': events,
        'form': form,
        'is_owner': is_owner,
        'is_scheduled': is_scheduled,
    }
    return render(request, 'subjects/detail.html', context)

@login_required
def enroll_subject(request, subject_id):
    """Allow students to enroll in subjects"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Make sure user has a student profile
    if not hasattr(request.user, 'student'):
        messages.error(request, 'Only students can enroll in subjects.')
        return redirect('subject_list')
    
    # Make sure user doesn't already have this subject scheduled
    if request.user.student.scheduled_subjects.filter(id=subject_id).exists():
        messages.info(request, f'You have already scheduled "{subject.name}".')
    else:
        request.user.student.scheduled_subjects.add(subject)
        messages.success(request, f'Successfully scheduled "{subject.name}".')
    
    return redirect('subject_list')

@login_required
def unenroll_subject(request, subject_id):
    """Allow students to remove subjects from their schedule"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Make sure user has a student profile
    if not hasattr(request.user, 'student'):
        messages.error(request, 'Only students can unenroll from subjects.')
        return redirect('subject_list')
    
    # Make sure user has this subject scheduled
    if not request.user.student.scheduled_subjects.filter(id=subject_id).exists():
        messages.info(request, f'You do not have "{subject.name}" scheduled.')
    else:
        request.user.student.scheduled_subjects.remove(subject)
        messages.success(request, f'Successfully removed "{subject.name}" from your schedule.')
    
    return redirect('subject_list')

@login_required
def edit_subject(request, subject_id):
    """Allow owners to edit subjects"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if user owns this subject
    if subject.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this subject.')
        return redirect('subject_list')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{subject.name}" updated successfully!')
            return redirect('subject_detail', subject_id=subject.id)
        else:
            messages.error(request, 'Error updating subject. Please check the form.')
    else:
        form = SubjectForm(instance=subject)
    
    context = {
        'subject': subject,
        'form': form,
    }
    return render(request, 'subjects/edit.html', context)

@login_required
def edit_event(request, subject_id, event_id):
    """Allow owners to edit events"""
    subject = get_object_or_404(Subject, id=subject_id)
    event = get_object_or_404(Event, id=event_id, subject=subject)
    
    # Check if user owns this subject
    if subject.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('subject_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.get_event_type_display()}" updated successfully!')
            return redirect('subject_detail', subject_id=subject.id)
        else:
            messages.error(request, 'Error updating event. Please check the form.')
    else:
        form = EventForm(instance=event)
    
    context = {
        'subject': subject,
        'event': event,
        'form': form,
    }
    return render(request, 'events/edit.html', context)

@login_required
def delete_event(request, event_id):
    """Allow owners to delete events"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user owns the subject this event belongs to
    if event.subject.created_by != request.user:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('calendar_view')
    
    event_type = event.get_event_type_display()
    subject_id = event.subject.id
    event.delete()
    messages.success(request, f'Event "{event_type}" deleted successfully!')
    return redirect('subject_detail', subject_id=subject_id)

@login_required
def calendar_view(request):
    # Show only events for subjects created by this user or scheduled by this student
    user_subjects = Subject.objects.filter(created_by=request.user)
    
    # Include scheduled subjects for students
    scheduled_subjects = []
    if hasattr(request.user, 'student'):
        scheduled_subjects = request.user.student.scheduled_subjects.all()
    
    all_subjects = user_subjects | scheduled_subjects
    all_subjects = all_subjects.distinct()
    
    return render(request, 'calendar/calendar.html', {'subjects': all_subjects})

@login_required
def get_events(request):
    """API endpoint to get events for calendar"""
    # Show only events for subjects created by this user or scheduled by this student
    user_subjects = Subject.objects.filter(created_by=request.user)
    
    # Include scheduled subjects for students
    scheduled_subjects = []
    if hasattr(request.user, 'student'):
        scheduled_subjects = request.user.student.scheduled_subjects.all()
    
    all_subjects = user_subjects | scheduled_subjects
    all_subjects = all_subjects.distinct()
    
    events = Event.objects.filter(subject__in=all_subjects)
    
    # Convert events to JSON serializable format
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': f"{event.subject.code} - {event.get_event_type_display()}",
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'backgroundColor': get_event_color(event.event_type),
            'borderColor': get_event_color(event.event_type),
            'extendedProps': {
                'location': event.location,
                'notes': event.notes,
                'subject': event.subject.name,
                'subject_id': event.subject.id,  # Add subject_id for deletion
            }
        })
    
    return JsonResponse(events_data, safe=False)

def get_event_color(event_type):
    """Return color based on event type"""
    colors = {
        'class': '#007bff',  # Blue
        'exam': '#dc3545',   # Red
        'lab': '#28a745',    # Green
    }
    return colors.get(event_type, '#6c757d')  # Default gray