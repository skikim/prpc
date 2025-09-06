from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime, date, timedelta
from .models import BookingLog
from .decorators import superuser_required, ajax_superuser_required
from bookingapp.models import Booking
import json


def _filter_duplicate_logs(logs_queryset):
    """
    중복 로그 필터링 로직 (예약요청 취소 후 승인 등의 패턴 간소화)
    """
    # 날짜+시간별로 그룹화하여 처리
    booking_groups = {}
    for log in logs_queryset:
        key = f"{log.booking_date}_{log.booking_time}"
        if key not in booking_groups:
            booking_groups[key] = []
        booking_groups[key].append(log)
    
    filtered_logs = []
    
    for group_logs in booking_groups.values():
        # 각 그룹을 시간순으로 정렬
        group_logs = sorted(group_logs, key=lambda x: x.created_at)
        
        i = 0
        while i < len(group_logs):
            current_log = group_logs[i]
            
            # 예약요청 취소 후 바로 예약승인이 오는 패턴 감지
            if (current_log.action_type == 'DELETE' and 
                current_log.previous_status == '예약요청' and
                i + 1 < len(group_logs) and
                group_logs[i + 1].action_type in ['CREATE', 'APPROVE'] and
                group_logs[i + 1].new_status == '예약승인'):
                
                # 예약요청 취소 로그는 건너뛰고 승인 로그만 추가
                next_log = group_logs[i + 1]
                # 승인 로그의 previous_status를 예약요청으로 수정하여 직접 전환처럼 보이게 함
                next_log.previous_status = '예약요청'
                # 액션을 예약승인으로 설정
                next_log.action_type = 'APPROVE'
                filtered_logs.append(next_log)
                i += 2  # 두 개 로그 모두 처리했으므로 2 증가
                continue
            
            # 예약승인 취소 후 바로 예약가능이 오는 패턴 감지  
            elif (current_log.action_type == 'DELETE' and 
                  current_log.previous_status == '예약승인' and
                  i + 1 < len(group_logs) and
                  group_logs[i + 1].action_type == 'CREATE' and
                  group_logs[i + 1].new_status == '예약가능'):
                
                # 승인 취소 로그는 건너뛰고 예약가능 생성을 취소 로그로 변환
                next_log = group_logs[i + 1]
                # 가짜 취소 로그 생성 (실제로는 예약가능 생성이지만 취소로 표시)
                cancel_log = type('LogProxy', (), {
                    'id': next_log.id,
                    'action_type': 'DELETE',
                    'get_simplified_action_display': lambda: '예약취소',
                    'get_action_display_korean': lambda: '예약취소',
                    'booking_date': next_log.booking_date,
                    'booking_time': next_log.booking_time,
                    'user': current_log.user,
                    'modified_by': next_log.modified_by,
                    'previous_status': '예약승인',
                    'new_status': '예약가능',
                    'created_at': next_log.created_at,
                    'notes': f'예약 취소: 예약승인 → 예약가능',
                    'ip_address': next_log.ip_address,
                    'get_user_display': current_log.get_user_display,
                    'get_modifier_display': next_log.get_modifier_display,
                })()
                filtered_logs.append(cancel_log)
                i += 2  # 두 개 로그 모두 처리했으므로 2 증가
                continue
            
            # 예약요청 취소 후 바로 예약가능이 오는 패턴 감지  
            elif (current_log.action_type == 'DELETE' and 
                  current_log.previous_status == '예약요청' and
                  i + 1 < len(group_logs) and
                  group_logs[i + 1].action_type == 'CREATE' and
                  group_logs[i + 1].new_status == '예약가능'):
                
                # 요청 취소 로그는 건너뛰고 예약가능 생성을 취소 로그로 변환
                next_log = group_logs[i + 1]
                # 가짜 취소 로그 생성 (실제로는 예약가능 생성이지만 취소로 표시)
                cancel_log = type('LogProxy', (), {
                    'id': next_log.id,
                    'action_type': 'DELETE',
                    'get_simplified_action_display': lambda: '예약취소',
                    'get_action_display_korean': lambda: '예약취소',
                    'booking_date': next_log.booking_date,
                    'booking_time': next_log.booking_time,
                    'user': current_log.user,
                    'modified_by': next_log.modified_by,
                    'previous_status': '예약요청',
                    'new_status': '예약가능',
                    'created_at': next_log.created_at,
                    'notes': f'예약 취소: 예약요청 → 예약가능',
                    'ip_address': next_log.ip_address,
                    'get_user_display': current_log.get_user_display,
                    'get_modifier_display': next_log.get_modifier_display,
                })()
                filtered_logs.append(cancel_log)
                i += 2  # 두 개 로그 모두 처리했으므로 2 증가
                continue
            
            # 일반적인 로그는 그대로 추가 (previous_status 보정)
            if current_log.action_type == 'CREATE' and not current_log.previous_status:
                # 예약요청의 경우 이전 상태를 예약가능으로 설정
                if current_log.new_status == '예약요청':
                    current_log.previous_status = '예약가능'
                # 다른 CREATE 로그들도 적절히 이전 상태 추정
                elif current_log.new_status == '예약승인' and i > 0:
                    # 이전 로그에서 상태 추정
                    prev_log = group_logs[i-1] if i > 0 else None
                    if prev_log and prev_log.new_status:
                        current_log.previous_status = prev_log.new_status
            
            filtered_logs.append(current_log)
            i += 1
    
    # 시간순으로 다시 정렬 (최신순)
    return sorted(filtered_logs, key=lambda x: x.created_at, reverse=True)


@superuser_required
def log_list(request):
    """
    로그 목록 조회 (메인 페이지)
    """
    # 기본 쿼리셋 (최근 2주일)
    end_date = date.today()
    start_date = end_date - timedelta(days=14)
    
    all_logs = BookingLog.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('user', 'modified_by', 'booking').order_by('created_at')
    
    # 중복 로그 필터링 적용
    filtered_logs = _filter_duplicate_logs(all_logs)
    
    # 페이지네이션
    paginator = Paginator(filtered_logs, 20)
    page_number = request.GET.get('page')
    page_logs = paginator.get_page(page_number)
    
    # 통계 정보 (원본 데이터 기준)
    stats = {
        'total_logs': BookingLog.objects.count(),
        'today_logs': BookingLog.objects.filter(created_at__date=date.today()).count(),
        'week_logs': all_logs.count(),
        'create_count': all_logs.filter(action_type='CREATE').count(),
        'update_count': all_logs.filter(action_type='UPDATE').count(),
        'delete_count': all_logs.filter(action_type='DELETE').count(),
        'approve_count': all_logs.filter(action_type='APPROVE').count(),
    }
    
    context = {
        'logs': page_logs,
        'stats': stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'logapp/log_list.html', context)


@superuser_required
def log_search(request):
    """
    검색 페이지
    """
    return render(request, 'logapp/log_search.html')


@ajax_superuser_required
def log_search_api(request):
    """
    AJAX 검색 API
    """
    if request.method != 'GET':
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
    
    # 검색 파라미터
    search_type = request.GET.get('type', 'all')
    keyword = request.GET.get('keyword', '').strip()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    booking_date = request.GET.get('booking_date')
    booking_time = request.GET.get('booking_time')
    action_type = request.GET.get('action_type')
    user_id = request.GET.get('user_id')
    
    # 기본 쿼리셋
    queryset = BookingLog.objects.select_related('user', 'modified_by', 'booking')
    
    # 날짜 필터링 (로그 생성 날짜 기준)
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 액션 타입 필터링
    if action_type:
        queryset = queryset.filter(action_type=action_type)
    
    # 사용자 필터링
    if user_id:
        try:
            user_id = int(user_id)
            queryset = queryset.filter(Q(user_id=user_id) | Q(modified_by_id=user_id))
        except ValueError:
            pass
    
    # 예약 날짜 필터링 (예약 슬롯 기준)
    if booking_date:
        try:
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            queryset = queryset.filter(booking_date=booking_date_obj)
        except ValueError:
            pass
    
    # 예약 시간 필터링 (예약 슬롯 기준)
    if booking_time:
        try:
            # 시간 형식 검증 후 문자열로 비교 (데이터베이스에 문자열로 저장되어 있음)
            datetime.strptime(booking_time, '%H:%M')  # 형식 검증용
            queryset = queryset.filter(booking_time=booking_time)
        except ValueError:
            pass
    
    # 키워드 검색
    if keyword:
        if search_type == 'date_time':
            # 날짜/시간 검색
            queryset = queryset.filter(
                Q(booking_date__icontains=keyword) |
                Q(booking_time__icontains=keyword)
            )
        elif search_type == 'user':
            # 사용자 검색 (실명 또는 사용자명)
            queryset = queryset.filter(
                Q(user__profile__real_name__icontains=keyword) |
                Q(user__username__icontains=keyword) |
                Q(modified_by__profile__real_name__icontains=keyword) |
                Q(modified_by__username__icontains=keyword)
            )
        elif search_type == 'notes':
            # 메모 검색
            queryset = queryset.filter(notes__icontains=keyword)
        else:
            # 전체 검색
            queryset = queryset.filter(
                Q(booking_date__icontains=keyword) |
                Q(booking_time__icontains=keyword) |
                Q(user__profile__real_name__icontains=keyword) |
                Q(user__username__icontains=keyword) |
                Q(modified_by__profile__real_name__icontains=keyword) |
                Q(modified_by__username__icontains=keyword) |
                Q(notes__icontains=keyword)
            )
    
    # 정렬 (필터링 전)
    queryset = queryset.order_by('created_at')
    
    # 중복 로그 필터링 적용
    filtered_logs = _filter_duplicate_logs(queryset)
    
    # 페이지네이션
    page = int(request.GET.get('page', 1))
    paginator = Paginator(filtered_logs, 15)
    page_logs = paginator.get_page(page)
    
    # JSON 응답 데이터 생성
    logs_data = []
    for log in page_logs:
        # 액션 타입 표시 로직
        if log.action_type == 'DELETE' and log.previous_status in ['예약승인', '예약요청'] and log.new_status == '예약가능':
            action_display = '예약취소'
        elif log.action_type == 'CREATE' and log.new_status == '예약요청':
            action_display = '예약요청'
        elif log.action_type == 'CREATE' and log.new_status == '예약승인':
            action_display = '예약승인'
        elif log.action_type == 'APPROVE':
            action_display = '예약승인'
        elif hasattr(log, 'get_action_display_korean'):
            action_display = log.get_action_display_korean()
        else:
            action_display = '예약취소' if log.action_type == 'DELETE' else '기타'
        
        logs_data.append({
            'id': log.id,
            'action_type': action_display,
            'action_type_code': log.action_type,
            'booking_date': log.booking_date.strftime('%Y-%m-%d'),
            'booking_time': log.booking_time,
            'user_display': log.get_user_display() if hasattr(log, 'get_user_display') else (log.user.username if log.user else '-'),
            'modifier_display': log.get_modifier_display() if hasattr(log, 'get_modifier_display') else (log.modified_by.username if log.modified_by else '시스템'),
            'previous_status': log.previous_status or '',
            'new_status': log.new_status,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'notes': log.notes,
            'ip_address': log.ip_address or '',
        })
    
    return JsonResponse({
        'logs': logs_data,
        'pagination': {
            'page': page_logs.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_previous': page_logs.has_previous(),
            'has_next': page_logs.has_next(),
        }
    })


@superuser_required
def booking_log_detail(request, date, time):
    """
    특정 날짜/시간 예약의 모든 로그 조회
    """
    try:
        booking_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return render(request, 'logapp/error.html', {
            'error': '잘못된 날짜 형식입니다.'
        })
    
    all_logs = BookingLog.objects.filter(
        booking_date=booking_date,
        booking_time=time
    ).select_related('user', 'modified_by', 'booking').order_by('created_at')
    
    # 불필요한 중간 로그 제거 (예약요청 -> 예약취소 -> 예약승인 패턴 간소화)
    filtered_logs = []
    logs_list = list(all_logs)
    
    i = 0
    while i < len(logs_list):
        current_log = logs_list[i]
        
        # 예약요청 취소 후 바로 예약승인이 오는 패턴 감지
        if (current_log.action_type == 'DELETE' and 
            current_log.previous_status == '예약요청' and
            i + 1 < len(logs_list) and
            logs_list[i + 1].action_type in ['CREATE', 'APPROVE'] and
            logs_list[i + 1].new_status == '예약승인'):
            
            # 예약요청 취소 로그는 건너뛰고 승인 로그만 추가
            next_log = logs_list[i + 1]
            # 승인 로그의 previous_status를 예약요청으로 수정하여 직접 전환처럼 보이게 함
            next_log.previous_status = '예약요청'
            # 액션을 예약승인으로 설정
            next_log.action_type = 'APPROVE'
            filtered_logs.append(next_log)
            i += 2  # 두 개 로그 모두 처리했으므로 2 증가
            continue
        
        # 예약승인 취소 후 바로 예약가능이 오는 패턴 감지  
        elif (current_log.action_type == 'DELETE' and 
              current_log.previous_status == '예약승인' and
              i + 1 < len(logs_list) and
              logs_list[i + 1].action_type == 'CREATE' and
              logs_list[i + 1].new_status == '예약가능'):
            
            # 승인 취소 로그는 건너뛰고 예약가능 생성을 취소 로그로 변환
            next_log = logs_list[i + 1]
            # 가짜 취소 로그 생성 (실제로는 예약가능 생성이지만 취소로 표시)
            cancel_log = type('LogProxy', (), {
                'id': next_log.id,
                'action_type': 'DELETE',
                'get_simplified_action_display': lambda: '예약취소',
                'booking_date': next_log.booking_date,
                'booking_time': next_log.booking_time,
                'user': current_log.user,
                'modified_by': next_log.modified_by,
                'previous_status': '예약승인',
                'new_status': '예약가능',
                'created_at': next_log.created_at,
                'notes': f'예약 취소: 예약승인 → 예약가능',
                'ip_address': next_log.ip_address,
                'get_user_display': next_log.get_user_display,
                'get_modifier_display': next_log.get_modifier_display,
            })()
            filtered_logs.append(cancel_log)
            i += 2  # 두 개 로그 모두 처리했으므로 2 증가
            continue
        
        # 예약요청 취소 후 바로 예약가능이 오는 패턴 감지  
        elif (current_log.action_type == 'DELETE' and 
              current_log.previous_status == '예약요청' and
              i + 1 < len(logs_list) and
              logs_list[i + 1].action_type == 'CREATE' and
              logs_list[i + 1].new_status == '예약가능'):
            
            # 요청 취소 로그는 건너뛰고 예약가능 생성을 취소 로그로 변환
            next_log = logs_list[i + 1]
            # 가짜 취소 로그 생성 (실제로는 예약가능 생성이지만 취소로 표시)
            cancel_log = type('LogProxy', (), {
                'id': next_log.id,
                'action_type': 'DELETE',
                'get_simplified_action_display': lambda: '예약취소',
                'booking_date': next_log.booking_date,
                'booking_time': next_log.booking_time,
                'user': current_log.user,
                'modified_by': next_log.modified_by,
                'previous_status': '예약요청',
                'new_status': '예약가능',
                'created_at': next_log.created_at,
                'notes': f'예약 취소: 예약요청 → 예약가능',
                'ip_address': next_log.ip_address,
                'get_user_display': next_log.get_user_display,
                'get_modifier_display': next_log.get_modifier_display,
            })()
            filtered_logs.append(cancel_log)
            i += 2  # 두 개 로그 모두 처리했으므로 2 증가
            continue
        
        # 일반적인 로그는 그대로 추가 (previous_status 보정)
        if current_log.action_type == 'CREATE' and not current_log.previous_status:
            # 예약요청의 경우 이전 상태를 예약가능으로 설정
            if current_log.new_status == '예약요청':
                current_log.previous_status = '예약가능'
            # 다른 CREATE 로그들도 적절히 이전 상태 추정
            elif current_log.new_status == '예약승인' and i > 0:
                # 이전 로그에서 상태 추정
                prev_log = logs_list[i-1] if i > 0 else None
                if prev_log and prev_log.new_status:
                    current_log.previous_status = prev_log.new_status
        
        filtered_logs.append(current_log)
        i += 1
    
    # 시간순으로 다시 정렬 (최신순)
    logs = sorted(filtered_logs, key=lambda x: x.created_at, reverse=True)
    
    # 현재 예약 상태 확인
    current_booking = None
    try:
        current_booking = Booking.objects.get(booking_date=booking_date, booking_time=time)
    except Booking.DoesNotExist:
        pass
    
    context = {
        'logs': logs,
        'booking_date': booking_date,
        'booking_time': time,
        'current_booking': current_booking,
    }
    
    return render(request, 'logapp/booking_log_detail.html', context)


@superuser_required
def user_log_detail(request, user_id):
    """
    특정 사용자의 모든 로그 조회
    """
    user = get_object_or_404(User, id=user_id)
    
    # 사용자가 예약자인 로그 + 변경자인 로그
    all_logs = BookingLog.objects.filter(
        Q(user=user) | Q(modified_by=user)
    ).select_related('user', 'modified_by', 'booking').order_by('created_at')
    
    # 중복 로그 필터링 적용
    filtered_logs = _filter_duplicate_logs(all_logs)
    
    # 페이지네이션
    paginator = Paginator(filtered_logs, 20)
    page_number = request.GET.get('page')
    page_logs = paginator.get_page(page_number)
    
    # 통계 정보 (원본 데이터 기준)
    stats = {
        'total_logs': all_logs.count(),
        'as_user_count': all_logs.filter(user=user).count(),
        'as_modifier_count': all_logs.filter(modified_by=user).count(),
        'create_count': all_logs.filter(user=user, action_type='CREATE').count(),
        'approve_count': all_logs.filter(modified_by=user, action_type='APPROVE').count(),
    }
    
    context = {
        'target_user': user,
        'logs': page_logs,
        'stats': stats,
    }
    
    return render(request, 'logapp/user_log_detail.html', context)
