import datetime

from articleapp.models import Waiting, WaitingOverride, WaitingPatient

AM_START = 6 * 60 + 30
AM_END = 9 * 60
PM_START = 11 * 60 + 30
PM_END = 14 * 60
MAX_WAITING = 4


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
    if override and override.mode == 'open' and weekday == 6:
        weekday = 0
    elif weekday == 6:
        return result(None, False, '일요일은 선착순 접수가 없습니다.')
    if weekday == 2:
        if total < PM_START:
            return result(None, False, '수요일은 오후 진료입니다.\n11시 30분부터 접수할 수 있습니다.')
        if total < PM_END:
            return result('pm', True, '')
        return result(None, False, '오늘 선착순 접수가 마감되었습니다.')
    if weekday == 5:
        if total < AM_START:
            return result(None, False, '오전 접수는 6시 30분부터 시작됩니다.')
        if total < AM_END:
            return result('am', True, '')
        return result(None, False, '오늘 선착순 접수가 마감되었습니다.')
    if total < AM_START:
        return result(None, False, '오전 접수는 6시 30분부터 시작됩니다.')
    if total < AM_END:
        return result('am', True, '')
    if total < PM_START:
        return result(None, False, '오전 접수가 마감되었습니다.\n오후 접수는 11시 30분부터입니다.')
    if total < PM_END:
        return result('pm', True, '')
    return result(None, False, '오늘 선착순 접수가 마감되었습니다.')


def current_waiting_period(now=None):
    return waiting_gate(now)['period']


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


def waiting_board(visit_date, period):
    if not period:
        return []
    patients = WaitingPatient.objects.filter(visit_date=visit_date, period=period).order_by('created_at')
    return [
        {'n': index, 'name': mask_name(patient.real_name)}
        for index, patient in enumerate(patients, 1)
    ]
