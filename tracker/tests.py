import json
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Record, OperationalMetric


class MultiUserTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pw-alice-123')
        self.bob = User.objects.create_user('bob', password='pw-bob-123')
        self.rec = Record.objects.create(user=self.alice, title='alice secret', category='Task', hours=3)

    def test_register_logs_in_and_starts_empty(self):
        r = self.client.post('/register/', {'username': 'carol', 'password1': 'Strong-pass-991', 'password2': 'Strong-pass-991'})
        self.assertRedirects(r, '/')
        data = self.client.get('/api/records/').json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(self.client.get('/api/stats/').json()['total_records'], 0)

    def test_register_rejects_weak_or_duplicate(self):
        r = self.client.post('/register/', {'username': 'alice', 'password1': '123', 'password2': '123'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.filter(username='alice').count(), 1)

    def test_users_cannot_see_or_touch_each_others_records(self):
        self.client.login(username='bob', password='pw-bob-123')
        self.assertEqual(self.client.get('/api/records/').json()['count'], 0)
        url = f'/api/records/{self.rec.id}/'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.put(url, json.dumps({'title': 'hacked'}), content_type='application/json').status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertNotIn(b'alice secret', self.client.get('/api/export/csv/').content)
        self.rec.refresh_from_db()
        self.assertEqual(self.rec.title, 'alice secret')

    def test_created_records_and_metrics_are_per_user(self):
        self.client.login(username='bob', password='pw-bob-123')
        self.client.post('/api/records/', json.dumps({'title': 'bob enquiry', 'cat': 'AdmissionSupport'}), content_type='application/json')
        self.assertEqual(Record.objects.get(title='bob enquiry').user, self.bob)
        self.assertEqual(OperationalMetric.get_for(self.bob).support_enquiries, 1)
        self.assertEqual(OperationalMetric.get_for(self.alice).support_enquiries, 0)

    def test_pages_require_login(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.assertEqual(self.client.get('/api/records/').status_code, 302)
        self.assertEqual(self.client.get('/register/').status_code, 200)

    def test_write_apis_require_csrf_token(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.login(username='alice', password='pw-alice-123')
        body = json.dumps({'title': 'x'})
        self.assertEqual(c.post('/api/records/', body, content_type='application/json').status_code, 403)
        self.assertEqual(c.delete(f'/api/records/{self.rec.id}/').status_code, 403)
        token = c.get('/').context['csrf_token']
        r = c.post('/api/records/', body, content_type='application/json', HTTP_X_CSRFTOKEN=str(token))
        self.assertEqual(r.status_code, 201)

    def test_counters_follow_delete_category_change_and_import(self):
        self.client.login(username='alice', password='pw-alice-123')
        m = lambda: OperationalMetric.get_for(self.alice)
        rid = self.client.post('/api/records/', json.dumps({'title': 'mock', 'cat': 'MockInterview'}), content_type='application/json').json()['record']['id']
        self.assertEqual(m().mock_interviews, 1)
        self.client.put(f'/api/records/{rid}/', json.dumps({'cat': 'Placement'}), content_type='application/json')
        self.assertEqual((m().mock_interviews, m().placements_supported), (0, 1))
        self.client.delete(f'/api/records/{rid}/')
        self.assertEqual(m().placements_supported, 0)
        self.client.post('/api/import/json/', json.dumps([{'title': 'e', 'date': '2026-01-01', 'cat': 'ProjectEval'}]), content_type='application/json')
        self.assertEqual(m().project_evaluations, 1)

    def test_duplicate_metric_rows_do_not_break_requests(self):
        first = OperationalMetric.objects.create(user=self.alice, mock_interviews=4)
        OperationalMetric.objects.create(user=self.alice)  # what parallel first page loads used to produce
        self.client.login(username='alice', password='pw-alice-123')
        self.assertEqual(self.client.get('/api/stats/').status_code, 200)
        self.assertEqual(OperationalMetric.get_for(self.alice).id, first.id)
