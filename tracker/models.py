import os
from django.conf import settings
from django.db import models
from django.utils import timezone
import datetime

class Record(models.Model):
    CATEGORY_CHOICES = [
        ('Achievement', '⭐ Achievement'),
        ('Task', '📌 Task'),
        ('Batch', '🎓 Batch / Class'),
        ('ProjectEval', '📊 Project Evaluation'),
        ('MockInterview', '🎙️ Mock Interview'),
        ('AdmissionSupport', '💼 Sales / Admissions Support'),
        ('Syllabus', '📚 Syllabus Update'),
        ('Placement', '🎯 Placement Support'),
        ('Learning', '💡 Learning'),
        ('Meeting', '🤝 Meeting'),
        ('Issue', '⚠️ Issue'),
        ('Other', '📝 Other'),
    ]

    # shortcut: nullable at DB level to avoid a table rebuild on Turso; app code always sets it
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='records')
    date = models.DateField(default=datetime.date.today, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Task', db_index=True)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Progress Record'
        verbose_name_plural = 'Progress Records'

    def __str__(self):
        return f"[{self.date}] {self.category}: {self.title}"

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'cat': self.category,
            'title': self.title,
            'notes': self.notes,
            'hours': float(self.hours) if self.hours is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class OperationalMetric(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='metrics')  # one per user via get_for()
    # Batches & Students
    total_batches = models.IntegerField(default=0, verbose_name="Total Batches")
    batches_completed = models.IntegerField(default=0, verbose_name="Batches Completed")
    total_students = models.IntegerField(default=0, verbose_name="Total Students")
    students_completed = models.IntegerField(default=0, verbose_name="Students Batch Completed")

    # Project Handling
    project_evaluations = models.IntegerField(default=0, verbose_name="Project Evaluations")
    mock_interviews = models.IntegerField(default=0, verbose_name="Mock Interviews")

    # Sales Cooperation and Admissions Support
    support_enquiries = models.IntegerField(default=0, verbose_name="Support & Admission Enquiries")
    syllabus_updates = models.IntegerField(default=0, verbose_name="Syllabus Updates")
    placements_supported = models.IntegerField(default=0, verbose_name="Placement Support / Assisted")

    notes = models.TextField(blank=True, default='', verbose_name="Operational Highlights / Notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Operational Metric'
        verbose_name_plural = 'Operational Metrics'

    CATEGORY_FIELD = {
        'MockInterview': 'mock_interviews',
        'ProjectEval': 'project_evaluations',
        'AdmissionSupport': 'support_enquiries',
        'Syllabus': 'syllabus_updates',
        'Placement': 'placements_supported',
    }

    @classmethod
    def get_for(cls, user):
        # shortcut: no DB unique constraint (avoids a Turso table rebuild), so parallel first requests can
        # create a duplicate row; always use the oldest one. Add unique=True if this ever matters.
        return cls.objects.filter(user=user).order_by('id').first() or cls.objects.create(user=user)

    @classmethod
    def bump(cls, user, category, delta):
        """Adjust the counter linked to a record category (never below 0). Returns True if one changed."""
        field = cls.CATEGORY_FIELD.get(category)
        if not field:
            return False
        metric = cls.get_for(user)
        setattr(metric, field, max(0, getattr(metric, field) + delta))
        metric.save()
        return True

    def to_dict(self):
        return {
            'total_batches': self.total_batches,
            'batches_completed': self.batches_completed,
            'total_students': self.total_students,
            'students_completed': self.students_completed,
            'project_evaluations': self.project_evaluations,
            'mock_interviews': self.mock_interviews,
            'support_enquiries': self.support_enquiries,
            'syllabus_updates': self.syllabus_updates,
            'placements_supported': self.placements_supported,
            'notes': self.notes,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


def local_owner():
    """User that desktop tools (popup, management commands) record for."""
    from django.contrib.auth import get_user_model
    return get_user_model().objects.get(username=os.environ.get('TRACKER_USER', 'harikriz'))
