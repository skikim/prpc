from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from superapp.backup_excel import backup_bytes
from superapp.models import BackupSetting


def _superuser_or_redirect(request):
    if request.user.is_superuser:
        return None
    return redirect(reverse('articleapp:index'))


def clean_backup_form(post):
    try:
        interval = int(post.get('interval_minutes'))
        retention = int(post.get('retention_days'))
    except (TypeError, ValueError):
        return None, '간격과 보관기간을 확인해 주세요.'
    if interval not in BackupSetting.INTERVAL_CHOICES:
        return None, '백업 간격은 5분, 10분, 15분 중에서 선택해 주세요.'
    if retention < 1 or retention > 30:
        return None, '보관기간은 1일에서 30일 사이여야 합니다.'
    return {
        'enabled': post.get('enabled') == 'on',
        'interval_minutes': interval,
        'retention_days': retention,
    }, None


@login_required
def backup_settings(request):
    denied = _superuser_or_redirect(request)
    if denied:
        return denied
    setting = BackupSetting.load()
    error = None
    if request.method == 'POST':
        cleaned, error = clean_backup_form(request.POST)
        if cleaned:
            setting.enabled = cleaned['enabled']
            setting.interval_minutes = cleaned['interval_minutes']
            setting.retention_days = cleaned['retention_days']
            setting.save()
            return redirect(reverse('superapp:backup_settings') + '?saved=1')
    return render(request, 'superapp/backup_settings.html', {
        'setting': setting,
        'error': error,
        'saved': request.GET.get('saved') == '1',
        'interval_choices': BackupSetting.INTERVAL_CHOICES,
    })


@login_required
def backup_config(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'forbidden'}, status=403)
    setting = BackupSetting.load()
    response = JsonResponse({
        'enabled': setting.enabled,
        'interval_minutes': setting.interval_minutes,
        'retention_days': setting.retention_days,
    })
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def backup_export(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'forbidden'}, status=403)
    content, stamp, filename = backup_bytes()
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['X-Backup-Stamp'] = stamp
    response['Cache-Control'] = 'no-store'
    response['Content-Disposition'] = (
        f"attachment; filename=\"backup_{stamp}.xlsx\"; filename*=UTF-8''{quote(filename)}"
    )
    return response
