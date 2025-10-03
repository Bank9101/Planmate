from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Subject, Event, Student, Teacher
from datetime import datetime, timedelta

class PlanmateModelsTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a subject
        self.subject = Subject.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            description='Basic concepts of computer science',
            credits=3,
            semester='1/2567',
            created_by=self.user
        )
        
        # Create a student
        self.student = Student.objects.create(
            user=self.user,
            student_id='ST12345'
        )
        
        # Create a teacher
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='teachpass123'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            teacher_id='TC98765'
        )
        
        # Add subject to student
        self.student.enrolled_subjects.add(self.subject)
        
        # Add subject to teacher
        self.teacher.managed_subjects.add(self.subject)
        
        # Create an event
        self.event = Event.objects.create(
            subject=self.subject,
            event_type='class',
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            location='Room 101',
            notes='Introduction to CS'
        )

    def test_subject_creation(self):
        """Test that a subject can be created correctly"""
        self.assertEqual(self.subject.code, 'CS101')
        self.assertEqual(self.subject.name, 'Introduction to Computer Science')
        self.assertEqual(self.subject.credits, 3)
        self.assertEqual(self.subject.semester, '1/2567')
        self.assertEqual(self.subject.created_by, self.user)

    def test_student_creation(self):
        """Test that a student can be created correctly"""
        self.assertEqual(self.student.user.username, 'testuser')
        self.assertEqual(self.student.student_id, 'ST12345')
        self.assertIn(self.subject, self.student.enrolled_subjects.all())

    def test_teacher_creation(self):
        """Test that a teacher can be created correctly"""
        self.assertEqual(self.teacher.user.username, 'teacher')
        self.assertEqual(self.teacher.teacher_id, 'TC98765')
        self.assertIn(self.subject, self.teacher.managed_subjects.all())

    def test_event_creation(self):
        """Test that an event can be created correctly"""
        self.assertEqual(self.event.subject, self.subject)
        self.assertEqual(self.event.event_type, 'class')
        self.assertEqual(self.event.location, 'Room 101')
        self.assertEqual(self.event.notes, 'Introduction to CS')

    def test_subject_deletion(self):
        """Test that a subject can be deleted correctly"""
        subject_id = self.subject.id
        self.subject.delete()
        
        # Check that the subject is deleted
        with self.assertRaises(Subject.DoesNotExist):
            Subject.objects.get(id=subject_id)
        
        # Check that related events are also deleted (CASCADE)
        self.assertFalse(Event.objects.filter(subject_id=subject_id).exists())

class PlanmateViewsTest(TestCase):
    def setUp(self):
        # Create users
        self.student_user = User.objects.create_user(
            username='student',
            password='studentpass123'
        )
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='teacherpass123'
        )
        
        # Create profiles
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='ST12345'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            teacher_id='TC98765'
        )
        
        # Create a subject owned by the student
        self.subject = Subject.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            description='Basic concepts of computer science',
            credits=3,
            semester='1/2567',
            created_by=self.student_user
        )

    def test_subject_list_view(self):
        """Test that the subject list view works"""
        # Test as student
        self.client.login(username='student', password='studentpass123')
        response = self.client.get(reverse('subject_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test as teacher
        self.client.login(username='teacher', password='teacherpass123')
        response = self.client.get(reverse('subject_list'))
        self.assertEqual(response.status_code, 200)

    def test_subject_detail_view(self):
        """Test that the subject detail view works"""
        # Test as owner (student)
        self.client.login(username='student', password='studentpass123')
        response = self.client.get(reverse('subject_detail', args=[self.subject.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test as non-owner (teacher) - should be redirected
        self.client.login(username='teacher', password='teacherpass123')
        response = self.client.get(reverse('subject_detail', args=[self.subject.id]))
        self.assertEqual(response.status_code, 302)  # Redirected due to permission

    def test_subject_deletion_view(self):
        """Test that a subject can be deleted via the view"""
        # Login as the owner
        self.client.login(username='student', password='studentpass123')
        
        # Delete the subject
        response = self.client.post(reverse('subject_detail', args=[self.subject.id]), {
            'delete_subject': 'true'
        })
        
        # Should redirect to subject list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('subject_list'))
        
        # Check that the subject is deleted
        with self.assertRaises(Subject.DoesNotExist):
            Subject.objects.get(id=self.subject.id)