import csv
import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Record, OperationalMetric

def index_view(request):
    return render(request, 'index.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('index')
    return render(request, 'registration/register.html', {'form': form})

@require_http_methods(["GET", "POST"])
def api_records(request):
    if request.method == "GET":
        q = request.GET.get('q', '').strip()
        cat = request.GET.get('cat', '').strip()
        time_filter = request.GET.get('time_filter', 'all').strip()

        qs = Record.objects.filter(user=request.user)

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
            user=request.user,
            date=parsed_date,
            category=cat,
            title=title,
            notes=notes,
            hours=parsed_hours
        )

        OperationalMetric.bump(request.user, cat, +1)

        return JsonResponse({'record': record.to_dict(), 'message': 'Record created successfully'}, status=201)

@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_record_detail(request, record_id):
    record = get_object_or_404(Record, id=record_id, user=request.user)

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
        new_cat = body.get('cat') or body.get('category')
        if new_cat and new_cat != record.category:
            OperationalMetric.bump(request.user, record.category, -1)
            OperationalMetric.bump(request.user, new_cat, +1)
            record.category = new_cat
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
        OperationalMetric.bump(request.user, record.category, -1)
        record.delete()
        return JsonResponse({'message': 'Record deleted successfully'})

@require_http_methods(["GET", "POST"])
def api_operational_metrics(request):
    metric = OperationalMetric.get_for(request.user)

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
    mine = Record.objects.filter(user=request.user)
    total_hours_agg = mine.aggregate(total=Sum('hours'))['total'] or 0.0
    return JsonResponse({
        'achievements_count': mine.filter(category='Achievement').count(),
        'distinct_days_logged': mine.values('date').distinct().count(),
        'total_hours': float(round(total_hours_agg, 2)),
        'total_records': mine.count(),
        'operational_metrics': OperationalMetric.get_for(request.user).to_dict(),
    })

@require_http_methods(["GET"])
def api_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="progress-records-{datetime.date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Title', 'Details', 'Hours'])

    for r in Record.objects.filter(user=request.user).order_by('date', 'id'):
        writer.writerow([r.date.strftime('%Y-%m-%d'), r.category, r.title, r.notes, r.hours if r.hours is not None else ''])

    return response

@require_http_methods(["GET"])
def api_export_json(request):
    records = [r.to_dict() for r in Record.objects.filter(user=request.user).order_by('date', 'id')]
    metrics = OperationalMetric.get_for(request.user).to_dict()
    export_payload = {
        'records': records,
        'operational_metrics': metrics,
        'exported_at': datetime.datetime.now().isoformat()
    }
    response = JsonResponse(export_payload, safe=False, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="progress-backup-{datetime.date.today()}.json"'
    return response

@require_http_methods(["POST"])
def api_import_json(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        raw_records = body if isinstance(body, list) else body.get('records', [])
        # A full backup restores counters itself below; a plain record list must bump them per record.
        has_metrics = isinstance(body, dict) and 'operational_metrics' in body

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
                user=request.user,
                date=p_date,
                category=cat,
                title=title,
                notes=notes,
                hours=p_hours
            )
            if not has_metrics:
                OperationalMetric.bump(request.user, cat, +1)
            imported_count += 1

        if has_metrics:
            m_data = body['operational_metrics']
            metric = OperationalMetric.get_for(request.user)
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
