# 병원 예약 웹 서비스(PRPC) 설명 문서

## 1. 웹에 대한 설명
이 웹 서비스는 Django 기반의 병원 예약 시스템으로, 환자가 온라인으로 예약할 수 있으며 병원 직원(슈퍼유저)은 관리자 페이지에서 전화 예약을 관리합니다. 주요 목적은 온라인 예약과 전화 상담의 충돌을 방지하기 위해 특정 시간대를 임시 차단하는 기능입니다. 

- **주요 목표**: 온라인 예약자가 차단된 시간대에 예약 시도 시 알림을 표시하고, 차단은 3분 후 자동 해제. 데이터베이스 대신 캐시를 사용해 구현.
- **대상 사용자**: 일반 환자(온라인 예약), 병원 직원(슈퍼유저, 예약 관리).
- **전체 흐름**: 회원가입/로그인 후 예약 페이지에서 시간 선택 → 예약 신청. 슈퍼유저는 별도 페이지에서 예약 관리 및 차단 기능 사용.
- **기타**: 휴일 메시지 표시, 대기 환자 수 업데이트, 쪽지(노트) 기능, 환자 검색 등 보조 기능 포함. 프로덕션 환경에서는 Redis 같은 캐시 백엔드 권장.

이 서비스는 2010년부터 운영 중인 푸른마취통증의학과의원 관련 웹으로, 통증의학 정보 제공과 예약 관리를 중심으로 합니다.

## 2. 구현된 기능
기능은 각 앱의 URL과 뷰를 기반으로 분류했습니다. 주요 기능은 계정 관리, 예약, 콘텐츠 표시, 검색, 쪽지 등입니다.

### 계정 관리 (accountapp)
- 회원가입: 동의 페이지 후 가입 폼 (/accounts/create/).
- 로그인/로그아웃: 커스텀 로그인 (/accounts/login/, /accounts/logout/).
- 계정 상세/수정/삭제: 사용자 페이지 (/accounts/detail/<pk>, /accounts/update/<pk>, /accounts/delete/<pk>).
- 동의 페이지: 회원가입 전 동의 (/accounts/agreement/).

### 프로필 관리 (profileapp)
- 프로필 생성/수정: 사용자 정보 입력 (/profiles/create/, /profiles/update/<pk>).
- 필드: 실명, 생년월일, 전화번호, 차트 번호.

### 콘텐츠/기사 표시 (articleapp)
- 홈페이지: 인덱스 페이지 (/ 또는 /articles/index/, 대기 환자 수, 휴일 메시지 표시).
- 정적 페이지: 통증의학 소개 (/articles/pm/), 장점 (/articles/pm_advantage/), 치료 질환 (/articles/pm_disease/), 개인정보 동의 (/articles/privacy_concent/), CCTV 정책 (/articles/cctv/), 예약 동영상 (/articles/movie/), 비급여 가격 (/articles/price/).
- 지도 (/articles/map/), 진료시간 (/articles/time_op/).
- 대기 환자 수 업데이트: 슈퍼유저 전용 (/articles/waiting_update/<pk>).
- 휴일 메시지: 생성/업데이트/삭제 (/articles/holiday_create/, /articles/holiday_update/<pk>, /articles/holiday_message_delete/<id>).

### 예약 관리 (bookingapp)
- 온라인 예약: 시간 선택 및 신청 (/bookings/create/, /bookings/create2/).
- 예약 상세/삭제: 사용자 예약 정보 (/bookings/detail/<pk>, /bookings/delete/<pk>).
- 상태: 예약가능, 예약요청, 예약승인, 예약불가.
- 차단 확인: 예약 시 캐시 확인 후 알림 표시.

### 슈퍼유저 예약 관리 (superapp)
- 슈퍼 예약 페이지: 다단계 예약 (/supers/supercreate/, /supers/supercreate2/, /supers/supercreate2_1/, /supers/supercreate3/, /supers/supercreate4/).
- 온라인 예약 차단/해제: 버튼 클릭으로 임시 차단 (/supers/block-bookings/, /supers/unblock-bookings/).

### 쪽지(노트) 기능 (noteapp)
- 쪽지 보내기: 슈퍼유저가 사용자에게 전송 (/notes/send_notes/).
- 쪽지 표시/삭제/이력: 받은 쪽지 목록 (/notes/display_notes/, /notes/delete_notes/<id>, /notes/notes_history/).

### 비밀번호 재설정 (passwordapp)
- 비밀번호 재설정 흐름: 폼 입력 → 확인 → 완료 (/passwords/password_reset/, /passwords/password_reset/done/, /passwords/reset/<uidb64>/<token>/, /passwords/password_reset_complete/).

### 검색 기능 (searchapp)
- 환자 검색: 이름, 생년월일, 전화번호로 검색 (/searches/searchpage/, /searches/search/).

### 기타 기능
- 관리자 페이지: Django admin (/admin/).
- 미들웨어: 프로필 확인 (CheckProfileMiddleware).
- 알림: Discord/SMS/Line 알림 (예약 시 트리거).
- 로깅: 차단 이벤트 기록.

## 3. 디자인
디자인은 Bootstrap 기반으로, 템플릿과 정적 파일로 구현. 간단한 반응형 레이아웃(헤더, 푸터, 본문).

### 템플릿 구조
- **기본 템플릿**: base.html (전체 레이아웃), head.html (헤더 스크립트), header.html (네비게이션 바: 메뉴, 드롭다운, 로그인/예약 링크), footer.html (주소, 연락처, 저작권, 슈퍼유저 링크).
- **앱별 템플릿**: 각 앱에 create.html, detail.html, update.html 등 (예: articleapp/index.html - 대기 환자 표시, bookingapp/create.html - 예약 폼).
- **전체 파일 목록**:
  - base.html, footer.html, head.html, header.html, home.html.
  - 앱별: accountapp/agreement.html, articleapp/home.html 등 (총 50+ 템플릿).

### 정적 파일 (static/)
- **CSS/JS**: styles.css (주 스타일, 11,303줄), scripts.js (자바스크립트 로직, 35줄).
- **이미지/아이콘**: manage_your_pain.png (로고), favicon.ico.
- **폰트**: NanumSquare 시리즈 (B, EB, L, R - 한국어 폰트).
- **특징**: 어두운 배경 푸터, 네비게이션 드롭다운, 모달(예약 확인 시 사용). Bootstrap5 사용으로 반응형.

## 4. 데이터베이스 구조
Django 모델 기반. 주요 모델은 다음과 같습니다. (models.py 파일에서 추출)

### articleapp/models.py
- **Waiting**: 대기 환자 수 (waiting_num: 0-4 선택, added_on_datetime: 자동 타임스탬프).
- **Holiday**: 휴일 메시지 (holiday_message: 문자열).

### bookingapp/models.py
- **Booking**: 예약 (user: User FK, booking_date: 날짜, booking_time: 시간 선택(09:20~20:05), booking_status: 상태 선택, booked_on_datetime: 자동 타임스탬프, booking_rn: 문자열).

### noteapp/models.py
- **Note**: 쪽지 (sender/recipient: User FK, message: 텍스트, timestamp: 자동 타임스탬프, is_read: 불린).

### profileapp/models.py
- **Profile**: 프로필 (user: User OneToOne, real_name: 문자열, birth_date: 문자열, phone_num: 문자열, chart_num: 고유 문자열).

### accountapp/models.py
- 빈 모델 (추가 모델 없음, Django User 모델 사용).

### 기타
- Django 기본 모델: User (auth), Admin 등.
- 마이그레이션: 각 앱에 초기 마이그레이션 파일 존재 (예: bookingapp에 0013까지).
- 관계: User → Profile (1:1), User → Booking/Note (FK). 