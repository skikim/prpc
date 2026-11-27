import datetime
from io import BytesIO

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from openpyxl import load_workbook

from articleapp.models import Holiday
from articleapp.views import sanitize_holiday_html
from bookingapp.models import Booking
from logapp.middleware import LoggingMiddleware
from noteapp.models import Note
from profileapp.forms import ProfileCreationForm
from profileapp.models import Profile
from superapp.backup_excel import backup_bytes, sanitize_excel_value


class HolidaySecurityTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('sec-admin', 'admin@example.com', 'pass1234')
        self.patient = User.objects.create_user('sec-patient', password='pass1234')
        self.holiday = Holiday.objects.create(holiday_message='<p>정상 공지</p>')

    def test_holiday_update_requires_superuser(self):
        url = f'/articles/holiday_update/{self.holiday.id}/'
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(url, {'holiday_message': '변조'}).status_code, 302)
        self.holiday.refresh_from_db()
        self.assertEqual(self.holiday.holiday_message, '<p>정상 공지</p>')

        self.client.login(username='sec-patient', password='pass1234')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'holiday_message': '변조'}).status_code, 403)
        self.holiday.refresh_from_db()
        self.assertEqual(self.holiday.holiday_message, '<p>정상 공지</p>')

        self.client.login(username='sec-admin', password='pass1234')
        resp = self.client.post(url, {'holiday_message': '<p><strong>수정된 공지</strong></p>'})
        self.assertEqual(resp.status_code, 302)
        self.holiday.refresh_from_db()
        self.assertEqual(self.holiday.holiday_message, '<p><strong>수정된 공지</strong></p>')

    def test_holiday_delete_requires_superuser_and_post(self):
        url = f'/articles/holiday_message_delete/{self.holiday.id}/'
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertTrue(Holiday.objects.filter(id=self.holiday.id).exists())

        self.client.login(username='sec-patient', password='pass1234')
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Holiday.objects.filter(id=self.holiday.id).exists())

        self.client.login(username='sec-admin', password='pass1234')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(Holiday.objects.filter(id=self.holiday.id).exists())

        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Holiday.objects.filter(id=self.holiday.id).exists())

    def test_sanitize_holiday_html_strips_unsafe_markup_and_keeps_formatting(self):
        raw = (
            '<p style="color: #dc2626; font-size: 18px; background-image: url(https://evil.test/x)" '
            'onclick="bad()"><strong>휴진 안내</strong></p>'
            '<svg onload="bad()"></svg>'
            '<img src="x" onerror="bad()">'
            '<script>bad()</script>'
            '<a href="javascript:bad()">링크텍스트</a>'
        )
        cleaned = sanitize_holiday_html(raw)
        self.assertIn('<strong>휴진 안내</strong>', cleaned)
        self.assertIn('color: #dc2626; font-size: 18px', cleaned)
        self.assertIn('링크텍스트', cleaned)
        for forbidden in ('<script', '<svg', '<img', 'onclick', 'onerror', 'onload', 'javascript:', 'url('):
            self.assertNotIn(forbidden, cleaned.lower())


class CsrfAndAccessHardeningTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('hard-admin', 'admin@example.com', 'pass1234')
        self.u1 = User.objects.create_user('hard-u1', password='pass1234')
        self.u2 = User.objects.create_user('hard-u2', password='pass1234')
        self.p1 = Profile.objects.create(user=self.u1, real_name='김일번', birth_date='900101', phone_num='010-1111-1111')
        self.p2 = Profile.objects.create(user=self.u2, real_name='김이번', birth_date='920202', phone_num='010-2222-2222')
        self.note = Note.objects.create(sender=self.admin, recipient=self.u1, message='테스트 메시지')

    def test_search_enforces_csrf_and_blocks_empty_dump(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        self.assertEqual(csrf_client.post('/searches/search/', {'search_term': '김'}).status_code, 403)
        self.assertEqual(csrf_client.post('/searches/searchpage/', {'search_term': '김'}).status_code, 403)

        self.client.login(username='hard-admin', password='pass1234')
        empty = self.client.post('/searches/search/', {'search_term': '   '})
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()['data'], [])

    def test_note_deletion_requires_post_and_ownership(self):
        self.client.login(username='hard-u1', password='pass1234')
        self.assertEqual(self.client.get(f'/notes/delete_notes/{self.note.id}/').status_code, 405)
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())

        self.client.login(username='hard-u2', password='pass1234')
        self.assertEqual(self.client.post(f'/notes/delete_notes/{self.note.id}/').status_code, 404)
        ajax_other = self.client.post(f'/notes/delete_note_ajax/{self.note.id}/')
        self.assertEqual(ajax_other.status_code, 404)
        self.assertFalse(ajax_other.json()['success'])
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())

        self.client.logout()
        self.assertEqual(self.client.post(f'/notes/delete_note_ajax/{self.note.id}/').status_code, 302)

        self.client.login(username='hard-u1', password='pass1234')
        ajax_ok = self.client.post(f'/notes/delete_note_ajax/{self.note.id}/')
        self.assertEqual(ajax_ok.status_code, 200)
        self.assertTrue(ajax_ok.json()['success'])
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_profile_and_account_auth_and_404_instead_of_500(self):
        self.assertEqual(self.client.get('/profiles/create/').status_code, 302)
        self.assertEqual(self.client.get(f'/accounts/detail/{self.u1.pk}').status_code, 302)
        self.assertEqual(self.client.get(f'/profiles/update/{self.p1.pk}').status_code, 302)

        self.client.login(username='hard-u1', password='pass1234')
        self.assertEqual(self.client.get('/accounts/detail/999999').status_code, 404)
        self.assertEqual(self.client.get('/profiles/update/999999').status_code, 404)
        self.assertEqual(self.client.get('/bookings/delete999999/').status_code, 404)

    def test_profile_form_validation_blocks_html_and_formulas(self):
        bad_html = ProfileCreationForm(data={
            'real_name': '<b>홍길동</b>',
            'birth_date': '900101',
            'phone_num': '010-1234-5678',
        })
        self.assertFalse(bad_html.is_valid())
        bad_formula = ProfileCreationForm(data={
            'real_name': '=CMD',
            'birth_date': '900101',
            'phone_num': '010-1234-5678',
        })
        self.assertFalse(bad_formula.is_valid())
        good = ProfileCreationForm(data={
            'real_name': '홍길동',
            'birth_date': '900101',
            'phone_num': '010-1234-5678',
        })
        self.assertTrue(good.is_valid())


class BookingExcelAndIpHardeningTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user('win-patient', password='pass1234')
        Profile.objects.create(
            user=self.patient,
            real_name='박정상',
            birth_date='900101',
            phone_num='010-1234-5678',
        )
        self.client.login(username='win-patient', password='pass1234')

    def test_booking_window_blocks_past_and_far_future(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        far_future = datetime.date.today() + datetime.timedelta(days=20)
        Booking.objects.create(booking_date=yesterday, booking_time='09:20', booking_status='예약가능')
        Booking.objects.create(booking_date=far_future, booking_time='09:20', booking_status='예약가능')

        resp_past = self.client.post('/bookings/create2/', {'date': yesterday.isoformat(), 'time': '09:20'})
        self.assertContains(resp_past, '지난 날짜는 예약할 수 없습니다.')

        resp_future = self.client.post('/bookings/create2/', {'date': far_future.isoformat(), 'time': '09:20'})
        self.assertContains(resp_future, '2주 이내')
        self.assertFalse(Booking.objects.filter(user=self.patient).exists())

    def test_excel_formula_injection_is_neutralized(self):
        self.assertEqual(sanitize_excel_value('=1+1'), "'=1+1")
        self.assertEqual(sanitize_excel_value('+SUM(A1)'), "'+SUM(A1)")
        self.assertEqual(sanitize_excel_value('홍길동'), '홍길동')

        today = datetime.date.today()
        Booking.objects.create(
            booking_date=today,
            booking_time='09:20',
            booking_status='예약승인',
            booking_rn='=1+1',
        )
        content, _, _ = backup_bytes(today=today)
        wb = load_workbook(BytesIO(content))
        values = [cell.value for row in wb['1주차'].iter_rows() for cell in row if cell.value]
        self.assertIn("'=1+1", values)
        self.assertNotIn('=1+1', values)

    def test_logging_middleware_prefers_x_real_ip_over_spoofed_xff(self):
        rf = RequestFactory()
        request = rf.get(
            '/',
            HTTP_X_FORWARDED_FOR='1.2.3.4, 203.0.113.9',
            HTTP_X_REAL_IP='203.0.113.9',
            REMOTE_ADDR='172.18.0.2',
        )
        mw = LoggingMiddleware(lambda req: None)
        self.assertEqual(mw.get_client_ip(request), '203.0.113.9')

        request_no_real = rf.get(
            '/',
            HTTP_X_FORWARDED_FOR='1.2.3.4, 203.0.113.9',
            REMOTE_ADDR='172.18.0.2',
        )
        self.assertEqual(mw.get_client_ip(request_no_real), '203.0.113.9')
