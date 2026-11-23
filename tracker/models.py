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

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

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

class AppSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.key}: {self.value}"
