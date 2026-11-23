from django.contrib import admin
from django.utils.html import format_html
from .models import Record, OperationalMetric

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'category_badge', 'title', 'hours', 'created_at')
    list_filter = ('user', 'category', 'date')
    search_fields = ('title', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date', '-id')

    def category_badge(self, obj):
        colors = {
            'Achievement': '#d97706',
            'Task': '#2563eb',
            'Batch': '#0284c7',
            'ProjectEval': '#0d9488',
            'MockInterview': '#7c3aed',
            'AdmissionSupport': '#c026d3',
            'Syllabus': '#e11d48',
            'Placement': '#059669',
            'Learning': '#16a34a',
            'Meeting': '#9333ea',
            'Issue': '#dc2626',
            'Other': '#64748b',
        }
        color = colors.get(obj.category, '#64748b')
        return format_html(
            '<span style="background-color:{}; color:#fff; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:11px;">{}</span>',
            color,
            obj.category
        )
    category_badge.short_description = 'Category'

@admin.register(OperationalMetric)
class OperationalMetricAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'total_batches', 'batches_completed', 'total_students', 'students_completed',
        'project_evaluations', 'mock_interviews', 'support_enquiries', 'syllabus_updates',
        'placements_supported', 'updated_at'
    )
