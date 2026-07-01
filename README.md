# GACHI

GACHI는 여행지 탐색, 코스 설계, 실시간 위치 공유, 커뮤니티와 AI 여행 도우미를 한 화면에서 제공하는 WIZ Framework 기반 웹 애플리케이션입니다.

## 주요 기능

- 지역·테마 기반 장소 탐색과 여행 코스 생성
- Google Maps 기반 경로·주변 장소 검색
- 일정 저장, 체크인, 위치 공유와 실시간 시그널
- 커뮤니티 게시물·댓글·반응
- 관리자용 장소·코스·공지·통계 관리
- Gemini 기반 여행 대화와 코스 제안

## 로컬 설정

민감 설정은 저장소에 포함하지 않습니다. 샘플 파일을 복사한 뒤 실제 값을 로컬 파일에만 입력하세요.

```bash
cp config-sample/database.py config/database.py
cp config-sample/ai.py config/ai.py
cp config-sample/auth.py config/auth.py
cp .env.example .env
```

- `config/auth.py`의 `jwt_secret`은 최소 32자의 고유한 값으로 교체합니다.
- 최초 관리자 생성이 필요할 때만 `bootstrap_admin.enabled`를 잠시 켜고, 생성 직후 다시 끕니다.
- 서버용 TourAPI·Google Places 키는 `.env`에 둡니다.
- 브라우저용 Google Maps 키는 배포 시 `google-maps-api-key` 메타 태그 또는 `window.TOUR_ON_GOOGLE_MAPS_API_KEY`로 주입하고 HTTP referrer 제한을 적용합니다.
- `config/`, `.env*`, 내부 devlog와 운영 산출물은 Git에서 제외됩니다.

## 의존성

```bash
npm ci
cd src/angular
npm ci
```

프로젝트 빌드는 WIZ IDE 또는 WIZ 프로젝트 빌드 기능을 사용합니다. 일반 변경은 기본 빌드로 확인하며, API 함수 추가·삭제·이름 변경이 있을 때만 clean build를 사용합니다.

## 저장소 보안

실제 API 키, 데이터베이스 접속정보, 관리자 자격증명과 운영 로그를 커밋하지 마세요. 노출이 의심되면 해당 값을 즉시 폐기·재발급하고 Git 이력까지 점검해야 합니다.
