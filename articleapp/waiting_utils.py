import datetime

import holidays

from articleapp.models import Waiting, WaitingBreak, WaitingOverride, WaitingPatient

AM_START = 6 * 60 + 30
AM_END = 9 * 60
PM_START = 11 * 60 + 30
PM_END = 14 * 60
MAX_WAITING = 4
_kr_holidays = {}


def legal_holiday_name(day):
    calendar = _kr_holidays.get(day.year)
    if calendar is None:
        calendar = holidays.KR(years=day.year)
        _kr_holidays[day.year] = calendar
    return calendar.get(day) or ''


def is_legal_holiday(day):
    return bool(legal_holiday_name(day))


def break_label(start, end):
    def text(day):
        return f'{day.month}월 {day.day}일'
    if start == end:
        return f'{text(start)} 쉽니다'
    return f'{text(start)}부터 {text(end)}까지 쉽니다'


def clear_waiting_break():
    current = WaitingBreak.objects.order_by('-id').first()
    if not current:
        return
    WaitingOverride.objects.filter(
        visit_date__range=(current.start_date, current.end_date),
        mode='closed',
    ).delete()
    current.delete()


def apply_waiting_break(start, end):
    clear_waiting_break()
    WaitingBreak.objects.create(start_date=start, end_date=end)
    day = start
    while day <= end:
        WaitingOverride.objects.update_or_create(visit_date=day, defaults={'mode': 'closed'})
        day += datetime.timedelta(days=1)


def _reception_closed_day(day):
    override = WaitingOverride.objects.filter(visit_date=day).first()
    if override:
        return override.mode == 'closed'
    return day.weekday() == 6 or is_legal_holiday(day)


def tablet_closed_day(now=None):
    now = now or datetime.datetime.now()
    return _reception_closed_day(now.date())


def tablet_screen_off(now=None):
    now = now or datetime.datetime.now()
    if tablet_closed_day(now):
        return True
    minutes = now.hour * 60 + now.minute
    if now.weekday() == 2:
        return minutes < 10 * 60 or minutes >= 20 * 60 + 30
    return minutes < 5 * 60 or minutes >= 18 * 60


def waiting_gate(now=None):
    now = now or datetime.datetime.now()
    weekday = now.weekday()
    total = now.hour * 60 + now.minute

    def result(period, can_input, message):
        return {
            'period': period,
            'can_input': can_input,
            'message': message,
            'period_label': period_label(period),
        }

    override = WaitingOverride.objects.filter(visit_date=now.date()).first()
    if override and override.mode == 'closed':
        return result(None, False, '오늘은 선착순 접수가 없습니다.')
    opened = bool(override and override.mode == 'open')
    if not opened and is_legal_holiday(now.date()):
        return result(None, False, '오늘은 공휴일이라 선착순 접수가 없습니다.')
    if opened and weekday == 6:
        weekday = 0
    elif weekday == 6:
        return result(None, False, '일요일은 선착순 접수가 없습니다.')
    if weekday == 2:
        if total < PM_START:
            return result(None, False, '수요일은 오후 진료입니다.\n11시 30분이 되면 자동으로 접수 화면으로 바뀝니다.\n조금만 기다려 주세요!!!')
        if total < PM_END:
            return result('pm', True, '')
        return result(None, False, '오늘 선착순 접수가 마감되었습니다.')
    if weekday == 5:
        if total < AM_START:
            return result(None, False, '오전 접수는 6시 30분부터입니다.\n6시 30분이 되면 자동으로 접수 화면으로 바뀝니다.\n조금만 기다려 주세요!!!')
        if total < AM_END:
            return result('am', True, '')
        return result(None, False, '오늘 선착순 접수가 마감되었습니다.')
    if total < AM_START:
        return result(None, False, '오전 접수는 6시 30분부터입니다.\n6시 30분이 되면 자동으로 접수 화면으로 바뀝니다.\n조금만 기다려 주세요!!!')
    if total < AM_END:
        return result('am', True, '')
    if total < PM_START:
        return result(None, False, '오전 접수가 마감되었습니다.\n오후 접수는 11시 30분부터입니다.\n11시 30분이 되면 자동으로 접수 화면으로 바뀝니다.\n조금만 기다려 주세요!!!')
    if total < PM_END:
        return result('pm', True, '')
    return result(None, False, '오늘 선착순 접수가 마감되었습니다.')


def current_waiting_period(now=None):
    return waiting_gate(now)['period']


def local_now():
    return datetime.datetime.now()


def notice_sessions(now=None):
    now = now or datetime.datetime.now()
    weekday = now.weekday()
    override = WaitingOverride.objects.filter(visit_date=now.date()).first()
    if override and override.mode == 'closed':
        return set()
    opened = bool(override and override.mode == 'open')
    if not opened and is_legal_holiday(now.date()):
        return set()
    if opened and weekday == 6:
        weekday = 0
    elif weekday == 6:
        return set()
    if weekday == 2:
        return {'pm'}
    if weekday == 5:
        return {'am'}
    return {'am', 'pm'}


def waiting_notice_visible(now, recorded_at):
    if not recorded_at or recorded_at.date() != now.date():
        return False
    sessions = notice_sessions(now)
    total = now.hour * 60 + now.minute
    recorded = recorded_at.hour * 60 + recorded_at.minute
    morning = (
        'am' in sessions
        and AM_START <= total < AM_END + 10
        and AM_START <= recorded < PM_START
    )
    afternoon = (
        'pm' in sessions
        and PM_START <= total < PM_END + 10
        and recorded >= PM_START
    )
    return morning or afternoon


def active_notice_period(now):
    sessions = notice_sessions(now)
    total = now.hour * 60 + now.minute
    if 'am' in sessions and AM_START <= total < AM_END + 10:
        return 'am'
    if 'pm' in sessions and PM_START <= total < PM_END + 10:
        return 'pm'
    return None


def waiting_clock_text(clock):
    if not clock:
        return ''
    period = '오전' if clock.hour < 12 else '오후'
    hour12 = clock.hour % 12 or 12
    return f'{period} {hour12}시 {clock.minute}분 기준'


def homepage_waiting_payload(now=None):
    now = now or local_now()
    waiting, _ = Waiting.objects.get_or_create(id=1)
    display = homepage_waiting(now, waiting.added_on_datetime, waiting.waiting_num)
    return {
        'visible': bool(display['visible']),
        'number': display['number'],
        'clock': waiting_clock_text(display['clock']) if display['visible'] else '',
    }


def homepage_waiting(now, recorded_at, stored_num):
    period = active_notice_period(now)
    hidden = {'visible': False, 'number': 0, 'period': '', 'clock': None}
    if not period:
        return hidden
    live = waiting_count(now.date(), period)
    if live:
        latest = WaitingPatient.objects.filter(
            visit_date=now.date(),
            period=period,
        ).order_by('-created_at').first()
        return {
            'visible': True,
            'number': min(live, MAX_WAITING),
            'period': period,
            'clock': latest.created_at if latest else recorded_at,
        }
    if waiting_notice_visible(now, recorded_at):
        return {
            'visible': True,
            'number': 0 if stored_num is None else stored_num,
            'period': period,
            'clock': recorded_at,
        }
    return hidden


def period_label(period):
    if period == 'am':
        return '오전'
    if period == 'pm':
        return '오후'
    return ''


def waiting_count(visit_date, period):
    return WaitingPatient.objects.filter(visit_date=visit_date, period=period).count()


def sync_waiting_count(visit_date, period):
    count = waiting_count(visit_date, period)
    waiting, _ = Waiting.objects.get_or_create(id=1)
    waiting.waiting_num = min(count, MAX_WAITING)
    waiting.save()
    return count


def mask_name(name):
    name = (name or '').strip()
    if len(name) <= 1:
        return '*'
    if len(name) == 2:
        return name[0] + '*'
    return name[0] + ('*' * (len(name) - 2)) + name[-1]


def normalize_birth_date(raw, today=None):
    raw = (raw or '').strip()
    if not raw.isdigit() or len(raw) not in (6, 8):
        return None
    today = today or datetime.date.today()
    if len(raw) == 6:
        yy = int(raw[:2])
        year = 1900 + yy if yy > today.year % 100 else 2000 + yy
        raw = f'{year:04d}{raw[2:]}'
    try:
        parsed = datetime.date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:
        return None
    if parsed.year < 1910 or parsed > today:
        return None
    return parsed.strftime('%Y%m%d')


def waiting_board(visit_date, period):
    if not period:
        return []
    patients = WaitingPatient.objects.filter(visit_date=visit_date, period=period).order_by('created_at')
    return [
        {'n': index, 'name': mask_name(patient.real_name)}
        for index, patient in enumerate(patients, 1)
    ]
