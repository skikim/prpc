# 예약 로그 시스템 구현 TODO List

## 개요
예약 요청, 승인, 취소 시 로그를 남기고 관리자가 확인할 수 있는 시스템 구현

## 목표
- 예약 상태 변경 시 상세 로그 생성
- 관리자가 `/log` 페이지에서 로그 확인 가능
- 60일간 로그 보관 후 자동 삭제
- 페이지네이션 지원

## TODO List

### 1. 데이터베이스 모델 생성
- [ ] `BookingLog` 모델 생성 (예약 로그 테이블)
  - 필드: id, user, chart_num, real_name, action_type, booking_date, booking_time, created_at, ip_address
  - action_type: '예약요청', '예약승인', '예약취소', '예약수정' 등
  - `superapp/models.py`에 모델 추가

### 2. 로그 생성 기능 구현
- [ ] `superapp/utils.py`에 로그 생성 함수 추가
  - `create_booking_log()` 함수 구현
  - IP 주소 추출 기능
  - 로그 메시지 포맷팅: "1234번(chart_num) 홍길동님이 2025/8/2 15:30 의 예약을 취소하였습니다.(2025/07/24 19:31)"

### 3. 기존 예약 관련 뷰 수정
- [ ] `superapp/views.py`의 예약 관련 뷰들에 로그 생성 추가
  - `superbooking()` - 1주차 예약 처리
  - `superbooking2()` - 2주차 예약 처리  
  - `superbooking2_1()` - 3주차 예약 처리
  - `superbooking2_2()` - 4주차 예약 처리
  - 각 예약 상태 변경 시 로그 생성

### 4. 로그 조회 페이지 생성
- [ ] `superapp/views.py`에 `booking_logs` 뷰 함수 추가
- [ ] `superapp/urls.py`에 로그 페이지 URL 패턴 추가 (`/log`)
- [ ] `superapp/templates/superapp/booking_logs.html` 템플릿 생성
  - 로그 목록 표시
  - 페이지네이션 구현
  - 검색/필터링 기능 (선택사항)

### 5. 자동 정리 기능 구현
- [ ] Django 관리 명령어 생성 (`management/commands/cleanup_old_logs.py`)
- [ ] 60일 이상 된 로그 자동 삭제 기능
- [ ] cron job 또는 Django signal로 자동 실행 설정

### 6. 마이그레이션 및 테스트
- [ ] Django 마이그레이션 파일 생성
- [ ] 기존 예약 데이터에 대한 로그 생성 테스트
- [ ] 로그 페이지 접근 권한 테스트 (슈퍼유저만 접근)

### 7. UI/UX 개선
- [ ] 로그 페이지 디자인 (Bootstrap 스타일링)
- [ ] 로그 레벨별 색상 구분 (요청/승인/취소)
- [ ] 날짜별 필터링 기능
- [ ] 사용자별 필터링 기능

## 구현 순서 (추천)
1. BookingLog 모델 생성
2. 로그 생성 유틸리티 함수 구현
3. 기존 뷰에 로그 생성 추가
4. 로그 조회 페이지 생성
5. 자동 정리 기능 구현

## 로그 메시지 형식 예시
- 예약요청: "1234번 홍길동님이 2025/8/2 15:30 의 예약을 요청하였습니다.(2025/07/24 19:31)"
- 예약승인: "1234번 홍길동님의 2025/8/2 15:30 의 예약이 승인되었습니다.(2025/07/24 19:31)"
- 예약취소: "1234번 홍길동님이 2025/8/2 15:30 의 예약을 취소하였습니다.(2025/07/24 19:31)"

## 접근 URL
- 로그 확인 페이지: `127.0.0.1:8000/log`
- 슈퍼유저만 접근 가능

## 파일 위치
- 모델: `superapp/models.py`
- 뷰: `superapp/views.py`
- URL: `superapp/urls.py`
- 템플릿: `superapp/templates/superapp/booking_logs.html`
- 유틸리티: `superapp/utils.py`
- 관리 명령어: `superapp/management/commands/cleanup_old_logs.py` 