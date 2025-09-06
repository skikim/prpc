#!/usr/bin/env python
"""
중복 로그와 불필요한 로그들을 정리하는 스크립트
"""
import os
import django
from datetime import datetime

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_test.settings.base')
django.setup()

from logapp.models import BookingLog

def clean_duplicate_logs():
    """
    중복 로그와 불필요한 로그들을 정리
    """
    print("=== 로그 정리 시작 ===")
    
    # 1. 같은 날짜/시간의 로그들을 그룹화
    booking_groups = {}
    all_logs = BookingLog.objects.all().order_by('booking_date', 'booking_time', 'created_at')
    
    for log in all_logs:
        key = f"{log.booking_date}_{log.booking_time}"
        if key not in booking_groups:
            booking_groups[key] = []
        booking_groups[key].append(log)
    
    deleted_count = 0
    
    for key, logs in booking_groups.items():
        if len(logs) <= 1:
            continue
            
        print(f"\n--- {key} 로그 그룹 정리 ---")
        for i, log in enumerate(logs):
            print(f"{i}: {log.created_at.strftime('%m/%d %H:%M:%S')} | {log.action_type} | {log.previous_status} -> {log.new_status} | {log.notes}")
        
        # 중복 패턴 감지 및 제거
        logs_to_keep = []
        logs_to_delete = []
        
        i = 0
        while i < len(logs):
            current = logs[i]
            
            # 예약승인 → 예약가능 (취소) 중복 제거
            if (current.action_type == 'DELETE' and 
                current.previous_status == '예약승인' and 
                current.new_status == '예약가능'):
                
                # 다음 로그가 동일한 패턴인지 확인
                if (i + 1 < len(logs) and 
                    logs[i + 1].action_type == 'DELETE' and
                    logs[i + 1].previous_status == '예약승인' and 
                    logs[i + 1].new_status == '예약가능'):
                    
                    # 첫 번째는 유지, 두 번째는 삭제
                    logs_to_keep.append(current)
                    logs_to_delete.append(logs[i + 1])
                    print(f"중복 삭제 로그 발견: {logs[i + 1].id} 삭제 예정")
                    i += 2
                    continue
            
            # 예약요청 → 예약승인 시 불필요한 예약요청 취소 로그 제거
            if (current.action_type == 'DELETE' and 
                current.previous_status == '예약요청' and 
                i + 1 < len(logs) and
                logs[i + 1].action_type == 'APPROVE' and
                logs[i + 1].previous_status == '예약요청'):
                
                logs_to_delete.append(current)
                print(f"불필요한 예약요청 취소 로그 발견: {current.id} 삭제 예정")
                i += 1
                continue
            
            logs_to_keep.append(current)
            i += 1
        
        # 실제 삭제 실행
        for log in logs_to_delete:
            print(f"삭제: {log.id} | {log.action_type} | {log.notes}")
            log.delete()
            deleted_count += 1
    
    print(f"\n=== 총 {deleted_count}개의 중복/불필요 로그 삭제 완료 ===")

if __name__ == "__main__":
    clean_duplicate_logs()