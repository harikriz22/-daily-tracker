from django.urls import path
from django.contrib.auth.decorators import login_required as L
from . import views

urlpatterns = [
    path('', L(views.index_view), name='index'),
    path('api/records/', L(views.api_records), name='api_records'),
    path('api/records/<int:record_id>/', L(views.api_record_detail), name='api_record_detail'),
    path('api/stats/', L(views.api_stats), name='api_stats'),
    path('api/operational-metrics/', L(views.api_operational_metrics), name='api_operational_metrics'),
    path('api/export/csv/', L(views.api_export_csv), name='api_export_csv'),
    path('api/export/json/', L(views.api_export_json), name='api_export_json'),
    path('api/import/json/', L(views.api_import_json), name='api_import_json'),
]
