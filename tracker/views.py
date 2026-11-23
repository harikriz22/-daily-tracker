import csv
import json
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Record, OperationalMetric, AppSetting

def index_view(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_records(request):
    if request.method == "GET":
        q = request.GET.get('q', '').strip()
        cat = request.GET.get('cat', '').strip()
        time_filter = request.GET.get('time_filter', 'all').strip()

        qs = Record.objects.all()

        if cat:
            qs = qs.filter(category=cat)

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(notes__icontains=q) | Q(category__icontains=q))

        today = datetime.date.today()
        if time_filter == 'this-month':
            qs = qs.filter(date__year=today.year, date__month=today.month)
        elif time_filter == 'last-month':
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - datetime.timedelta(days=1)
            qs = qs.filter(date__year=last_month_end.year, date__month=last_month_end.month)
        elif time_filter == 'this-week':
            start_week = today - datetime.timedelta(days=today.weekday())
            end_week = start_week + datetime.timedelta(days=6)
            qs = qs.filter(date__gte=start_week, date__lte=end_week)

        data = [r.to_dict() for r in qs]
        return JsonResponse({'records': data, 'count': len(data)})

    elif request.method == "POST":
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        date_str = body.get('date') or datetime.date.today().strftime('%Y-%m-%d')
        cat = body.get('cat') or body.get('category') or 'Task'
        title = (body.get('title') or '').strip()
        notes = (body.get('notes') or '').strip()
        hours = body.get('hours')

        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)

        try:
            parsed_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            parsed_date = datetime.date.today()

        parsed_hours = None
        if hours not in (None, '', 0, '0'):
            try:
                parsed_hours = round(float(hours), 2)
            except ValueError:
                parsed_hours = None

        record = Record.objects.create(
            date=parsed_date,
            category=cat,
            title=title,
            notes=notes,
            hours=parsed_hours
        )

        # Automatically increment corresponding OperationalMetric if relevant
        metric = OperationalMetric.get_solo()
        if cat == 'MockInterview':
            metric.mock_interviews += 1
            metric.save()
        elif cat == 'ProjectEval':
            metric.project_evaluations += 1
            metric.save()
        elif cat == 'AdmissionSupport':
            metric.support_enquiries += 1
            metric.save()
        elif cat == 'Syllabus':
            metric.syllabus_updates += 1
            metric.save()
        elif cat == 'Placement':
            metric.placements_supported += 1
            metric.save()

        return JsonResponse({'record': record.to_dict(), 'message': 'Record created successfully'}, status=201)

@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_record_detail(request, record_id):
    record = get_object_or_404(Record, id=record_id)

    if request.method == "GET":
        return JsonResponse({'record': record.to_dict()})

    elif request.method in ("PUT", "PATCH"):
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if 'date' in body:
            try:
                record.date = datetime.date.fromisoformat(body['date'])
            except ValueError:
                pass
        if 'cat' in body or 'category' in body:
            record.category = body.get('cat') or body.get('category')
        if 'title' in body:
            record.title = body['title'].strip()
        if 'notes' in body:
            record.notes = body['notes'].strip()
        if 'hours' in body:
            h = body['hours']
            record.hours = round(float(h), 2) if h not in (None, '') else None

        record.save()
        return JsonResponse({'record': record.to_dict(), 'message': 'Record updated successfully'})

    elif request.method == "DELETE":
        record.delete()
        return JsonResponse({'message': 'Record deleted successfully'})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_operational_metrics(request):
    metric = OperationalMetric.get_solo()

    if request.method == "GET":
        return JsonResponse({'metrics': metric.to_dict()})

    elif request.method == "POST":
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        action = body.get('action')
        field = body.get('field')

        int_fields = [
            'total_batches', 'batches_completed', 'total_students', 'students_completed',
            'project_evaluations', 'mock_interviews', 'support_enquiries', 'syllabus_updates',
            'placements_supported'
        ]

        if action == 'increment' and field in int_fields:
            setattr(metric, field, getattr(metric, field) + 1)
            metric.save()
            return JsonResponse({'metrics': metric.to_dict(), 'message': f'Incremented {field}'})

        elif action == 'decrement' and field in int_fields:
            val = max(0, getattr(metric, field) - 1)
            setattr(metric, field, val)
            metric.save()
            return JsonResponse({'metrics': metric.to_dict(), 'message': f'Decremented {field}'})

        else:
            for f in int_fields:
                if f in body:
                    try:
                        setattr(metric, f, max(0, int(body[f])))
                    except (ValueError, TypeError):
                        pass
            if 'notes' in body:
                metric.notes = body['notes'].strip()

            metric.save()
            return JsonResponse({'metrics': metric.to_dict(), 'message': 'Operational metrics updated successfully'})

@require_http_methods(["GET"])
def api_stats(request):
    pe_setting = AppSetting.objects.filter(key='pe_target_date').first()
    pe_target_str = pe_setting.value if pe_setting else '2027-05-01'

    today = datetime.date.today()
    days_to_pe = None
    try:
        pe_date = datetime.date.fromisoformat(pe_target_str)
        days_to_pe = max(0, (pe_date - today).days)
    except Exception:
        days_to_pe = 0

    total_records = Record.objects.count()
    achievements_count = Record.objects.filter(category='Achievement').count()
    distinct_days_logged = Record.objects.values('date').distinct().count()
    total_hours_agg = Record.objects.aggregate(total=Sum('hours'))['total'] or 0.0

    metric = OperationalMetric.get_solo()

    return JsonResponse({
        'pe_target_date': pe_target_str,
        'days_to_pe': days_to_pe,
        'achievements_count': achievements_count,
        'distinct_days_logged': distinct_days_logged,
        'total_hours': float(round(total_hours_agg, 2)),
        'total_records': total_records,
        'operational_metrics': metric.to_dict(),
    })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_pe_date(request):
    if request.method == "GET":
        setting = AppSetting.objects.filter(key='pe_target_date').first()
        return JsonResponse({'pe_target_date': setting.value if setting else '2027-05-01'})
    elif request.method == "POST":
        try:
            body = json.loads(request.body.decode('utf-8'))
            pe_date = body.get('pe_target_date')
            if pe_date:
                AppSetting.objects.update_or_create(
                    key='pe_target_date',
                    defaults={'value': pe_date}
                )
                return JsonResponse({'pe_target_date': pe_date, 'message': 'Updated'})
        except Exception:
            pass
        return JsonResponse({'error': 'Invalid request'}, status=400)

@require_http_methods(["GET"])
def api_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="progress-records-{datetime.date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Title', 'Details', 'Hours'])

    for r in Record.objects.all().order_by('date', 'id'):
        writer.writerow([r.date.strftime('%Y-%m-%d'), r.category, r.title, r.notes, r.hours if r.hours is not None else ''])

    return response

@require_http_methods(["GET"])
def api_export_json(request):
    records = [r.to_dict() for r in Record.objects.all().order_by('date', 'id')]
    metrics = OperationalMetric.get_solo().to_dict()
    export_payload = {
        'records': records,
        'operational_metrics': metrics,
        'exported_at': datetime.datetime.now().isoformat()
    }
    response = JsonResponse(export_payload, safe=False, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="progress-backup-{datetime.date.today()}.json"'
    return response

@csrf_exempt
@require_http_methods(["POST"])
def api_import_json(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        raw_records = body if isinstance(body, list) else body.get('records', [])

        imported_count = 0
        for item in raw_records:
            title = (item.get('title') or '').strip()
            date_str = item.get('date')
            cat = item.get('cat') or item.get('category') or 'Task'
            notes = (item.get('notes') or '').strip()
            hours = item.get('hours')

            if not title or not date_str:
                continue

            try:
                p_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                continue

            p_hours = None
            if hours not in (None, ''):
                try:
                    p_hours = round(float(hours), 2)
                except ValueError:
                    p_hours = None

            Record.objects.create(
                date=p_date,
                category=cat,
                title=title,
                notes=notes,
                hours=p_hours
            )
            imported_count += 1

        if isinstance(body, dict) and 'operational_metrics' in body:
            m_data = body['operational_metrics']
            metric = OperationalMetric.get_solo()
            for f in ['total_batches', 'batches_completed', 'total_students', 'students_completed',
                      'project_evaluations', 'mock_interviews', 'support_enquiries', 'syllabus_updates',
                      'placements_supported']:
                if f in m_data:
                    setattr(metric, f, m_data[f])
            if 'notes' in m_data:
                metric.notes = m_data['notes']
            metric.save()

        return JsonResponse({'imported_count': imported_count, 'message': f'Successfully imported {imported_count} records'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
