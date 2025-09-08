# 예약 로그 자동 정리 가이드

## 개요
60일 이상 된 예약 로그를 자동으로 삭제하여 데이터베이스 용량을 관리하는 시스템입니다.

## 커맨드 사용법

### 기본 사용법
```bash
# 60일 이상 된 로그 삭제 (기본값)
python manage.py cleanup_old_logs

# 시뮬레이션 (실제 삭제 안함)
python manage.py cleanup_old_logs --dry-run

# 다른 보관 기간 설정 (예: 30일)
python manage.py cleanup_old_logs --days 30

# 자동화용 (확인 프롬프트 없이)
python manage.py cleanup_old_logs --force
```

### 옵션 설명
- `--days`: 보관할 일수 (기본: 60일)
- `--batch-size`: 한 번에 삭제할 로그 수 (기본: 1000개)
- `--dry-run`: 실제 삭제 없이 시뮬레이션만 실행
- `--force`: 확인 프롬프트 없이 강제 실행

## 자동화 설정

### 1. Linux/macOS에서 cron 설정

#### crontab 편집
```bash
crontab -e
```

#### 매일 새벽 2시에 실행
```bash
# 매일 새벽 2시에 60일 이상 된 로그 삭제
0 2 * * * cd /path/to/your/project && python manage.py cleanup_old_logs --force >> /var/log/django_log_cleanup.log 2>&1
```

#### 주간 실행 (매주 일요일 새벽 3시)
```bash
# 매주 일요일 새벽 3시에 실행
0 3 * * 0 cd /path/to/your/project && python manage.py cleanup_old_logs --force >> /var/log/django_log_cleanup.log 2>&1
```

### 2. AWS 서버에서 설정

#### Docker 환경에서
```bash
# Docker 컨테이너 내부에서 실행
docker exec -it your_container_name python manage.py cleanup_old_logs --force

# cron에서 Docker 컨테이너 실행
0 2 * * * docker exec your_container_name python manage.py cleanup_old_logs --force >> /var/log/django_log_cleanup.log 2>&1
```

#### 가상환경 사용 시
```bash
# 가상환경 활성화 후 실행
0 2 * * * cd /home/ubuntu/prpc && source venv/bin/activate && python manage.py cleanup_old_logs --force >> /var/log/django_log_cleanup.log 2>&1
```

### 3. 로그 모니터링

#### 로그 파일 확인
```bash
# 실행 로그 확인
tail -f /var/log/django_log_cleanup.log

# 최근 실행 결과 확인
tail -20 /var/log/django_log_cleanup.log
```

#### Django 로그 설정
`settings.py`에 로깅 설정 추가:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django_cleanup.log',
        },
    },
    'loggers': {
        'logapp.management.commands.cleanup_old_logs': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 실행 예시

### 테스트 실행 결과
```bash
$ python manage.py cleanup_old_logs --days 1 --dry-run
[DRY RUN] 예약 로그 정리 시작
보관 기간: 1일
삭제 기준 날짜: 2025-09-07
배치 크기: 1000
삭제 대상 로그: 142개
전체 로그: 148개
[DRY RUN] 142개의 로그가 삭제될 예정입니다.
```

### 실제 실행 결과
```bash
$ python manage.py cleanup_old_logs --force
예약 로그 정리 시작
보관 기간: 60일
삭제 기준 날짜: 2025-07-10
배치 크기: 1000
삭제 대상 로그: 1,250개
전체 로그: 2,103개

배치 1: 1,000개 삭제됨 (총 1,000/1,250)
배치 2: 250개 삭제됨 (총 1,250/1,250)

✅ 로그 정리 완료!
삭제된 로그: 1,250개
남은 로그: 853개
처리된 배치: 2개
데이터베이스 용량이 절약되었습니다!
```

## 안전 기능

1. **배치 삭제**: 메모리 효율성을 위해 1000개씩 나누어 삭제
2. **트랜잭션**: 각 배치는 트랜잭션으로 보호
3. **Dry Run**: 실제 삭제 전에 시뮬레이션 가능
4. **확인 프롬프트**: 수동 실행 시 삭제 확인
5. **상세 로깅**: 삭제 과정과 결과를 상세히 기록

## 권장 설정

- **보관 기간**: 60일 (감사 추적에 충분한 기간)
- **실행 주기**: 매일 또는 주 1회
- **실행 시간**: 새벽 시간대 (서버 부하 최소)
- **모니터링**: 로그 파일로 실행 결과 추적

## 주의사항

1. **백업**: 중요한 로그는 별도 백업 고려
2. **테스트**: 운영 환경 적용 전 `--dry-run`으로 테스트
3. **권한**: cron 실행 사용자에게 충분한 권한 필요
4. **경로**: cron에서는 절대 경로 사용 권장