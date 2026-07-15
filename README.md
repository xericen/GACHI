# GACHI

> 여행지를 찾는 순간부터 코스를 만들고, 동행을 만나고, 여행 중 위치를 공유하고, 기록을 남기는 순간까지 하나로 연결한 여행 웹 애플리케이션입니다.

[![Quality](https://github.com/xericen/GACHI/actions/workflows/quality.yml/badge.svg)](https://github.com/xericen/GACHI/actions/workflows/quality.yml)
[![Security Policy](https://img.shields.io/badge/security-policy-red.svg)](SECURITY.md)

- 서비스: [https://travel.wizide.com/](https://travel.wizide.com/)
- 저장소: [xericen/GACHI](https://github.com/xericen/GACHI)
- 기반 기술: WIZ Framework, Angular, Python, MySQL

## GACHI가 해결하려는 문제

여행 준비에는 장소 검색, 일정 구성, 이동 경로 확인, 동행 모집, 실시간 소통처럼 서로 다른 작업이 필요합니다. GACHI는 이 과정을 여러 서비스로 나누지 않고 하나의 흐름으로 제공합니다.

1. 지역·날짜·취향을 선택합니다.
2. AI 추천 또는 직접 편집으로 여행 코스를 만듭니다.
3. 저장한 코스를 지도에서 실행하고 장소별로 체크인합니다.
4. 사전 동행을 모집하거나 여행지에서 즉석 만남을 시작합니다.
5. 커뮤니티와 채팅으로 경험을 공유하고 여행 기록을 보관합니다.

## 핵심 기능

### 장소 탐색과 홈

- 지역과 테마별 관광지·음식점·카페 탐색
- TourAPI 장소 데이터와 Google Places 평점·상세 정보 결합
- 날짜, 지역, 여행 성향을 반영한 필터
- 인기 코스, 추천 장소, 커뮤니티, 동행 콘텐츠 탐색

### AI 여행 코스

- 대화형 AI를 이용한 여행 요구사항 정리
- 실제 저장 장소를 바탕으로 일차별 코스 생성
- 장소 순서, 체류 시간, 이동 방식과 일정 직접 편집
- 생성 중인 코스 미리보기와 임시 보관
- 저장 코스의 지도 경로 및 장소 상세 확인

### 지도와 여행 실행

- Google Maps 기반 장소 검색과 주변 장소 표시
- 코스 구간별 경로, 예상 거리와 이동 시간 제공
- 여행 시작, 현재 목적지 안내, 장소별 체크인
- 여행 중 위치 공유와 장소 혼잡도 표현
- 일정이 끝난 뒤 실행 상태와 여행 기록 보관

### 동행과 같이 지도

- 확정된 코스를 기준으로 사전 동행 모집
- 여행 이력서와 성향 정보를 활용한 동행 신청
- 여행지 주변 사용자에게 즉석 만남 신호 전송
- 수락된 만남의 전용 채팅과 자동 만료
- 여행 기간에만 활성화되는 위치 공유형 같이 지도

### 본인 인증과 여행 이력서

- 이름과 여행 성향을 나누어 관리하는 여행 프로필
- PortOne V2 기반 PASS 본인 인증 연동
- 인증 결과를 활용한 여행 이력서 간편 입력
- 동행 신청 시 공개할 이력서 선택 및 미리보기

### 커뮤니티와 채팅

- 여행 후기, 질문, 사진, 태그와 투표 게시물
- 댓글, 좋아요, 저장과 공유
- AI 여행 채팅, 커뮤니티, 1:1 메시지 화면
- 동행 준비방과 즉석 만남 채팅

### 마이페이지와 관리자

- 저장 장소·코스, 최근 본 항목, 작성 게시물 관리
- 여행 코스를 목록·지도·기록 형태로 조회
- 사용자, 장소, 추천 코스, 공지와 약관 관리
- 가입·필터 사용·인기 코스 등 운영 통계 확인
- 운영 중인 AI 모델과 런타임 설정 관리

## 기술 구성

| 영역 | 사용 기술 및 역할 |
|---|---|
| UI | Angular, TypeScript, Pug, SCSS |
| 애플리케이션 | WIZ Framework의 page/route/portal 구조 |
| 서버 | Python API 및 컨트롤러 |
| 데이터 | MySQL, Python ORM 모델, Node.js 운영 스크립트 |
| 지도·장소 | Google Maps JavaScript API, Google Places API, 한국관광공사 TourAPI |
| AI | Gemini 기반 대화 및 코스 생성 도구 |
| 인증 | WIZ 세션/JWT, PortOne V2 PASS 본인 인증 |
| 실시간 여행 | 위치 공유, 체크인, 주변 신호, 만남 채팅과 만료 작업 |

## 프로젝트 구조

```text
GACHI/
├── config-sample/          # 공개 가능한 Python 설정 예시
├── scripts/                # 데이터 이관·수집·만료 배치
├── services/               # TourAPI 및 Google Places 클라이언트
├── src/
│   ├── angular/            # Angular 빌드 및 공통 부트스트랩
│   ├── app/                # 화면(page), 레이아웃, 화면 전용 API
│   ├── assets/             # 브랜드, 폰트, 샘플 이미지
│   ├── controller/         # 공통 서버 컨트롤러
│   ├── model/              # DB 모델과 도메인 로직
│   ├── portal/             # 인증 및 공통 WIZ 포털 모듈
│   └── route/              # 독립 API 및 관리자 라우트
├── .env.example            # 환경변수 이름과 예시값
├── .githooks/pre-commit    # 커밋 직전 민감정보 자동 검사
└── package.json            # 운영 스크립트와 Node.js 의존성
```

주요 화면은 `src/app/page.access/`에 모여 있습니다. 장소·코스·커뮤니티·동행·지도처럼 여러 기능이 같은 앱 셸과 하단 탐색 구조를 공유합니다. 독립적으로 호출되는 API는 `src/route/`, 재사용되는 데이터 로직은 `src/model/`에서 관리합니다.

## 시작하기

### 1. 저장소와 의존성 준비

```bash
git clone git@github.com:xericen/GACHI.git
cd GACHI
npm ci
cd src/angular && npm ci && cd ../..
```

WIZ 프로젝트 실행과 빌드에는 WIZ Framework가 구성된 개발 환경이 필요합니다.

### 2. 로컬 설정 생성

실제 자격증명은 저장소에 포함하지 않습니다. 예시 파일을 복사한 뒤 복사본에만 값을 입력합니다.

```bash
cp config-sample/database.py config/database.py
cp config-sample/ai.py config/ai.py
cp config-sample/auth.py config/auth.py
cp .env.example .env
```

`config/`와 `.env`는 Git에서 제외됩니다. 예시 파일에는 실제 키, 비밀번호, 운영 서버 주소를 넣지 마세요.

### 3. 환경변수

| 변수 | 용도 | 노출 범위 |
|---|---|---|
| `TOUR_API_KEY` | TourAPI 장소 수집·상세 조회 | 서버 전용 |
| `GOOGLE_PLACES_API_KEY` | 장소 매칭·평점 수집 | 서버 전용 |
| `PORTONE_STORE_ID` | PortOne 상점 식별자 | 브라우저 전달 가능 |
| `PORTONE_IDENTITY_CHANNEL_KEY` | PASS 본인 인증 채널 | 브라우저 전달 가능 |
| `PORTONE_API_SECRET` | 본인 인증 결과 서버 검증 | 서버 전용 |
| `GOOGLE_PLACES_DELAY_MS` | 외부 API 호출 간격 | 선택 사항 |
| `GOOGLE_RATING_CACHE_DAYS` | 평점 캐시 유지 기간 | 선택 사항 |

브라우저용 Google Maps 키는 배포 환경에서 `google-maps-api-key` 메타 태그 또는 `window.TOUR_ON_GOOGLE_MAPS_API_KEY`로 주입합니다. 반드시 HTTP referrer와 API 사용 범위를 제한하세요.

### 4. 인증 설정 주의사항

- `config/auth.py`의 JWT 비밀값은 충분히 긴 무작위 값으로 교체합니다.
- 최초 관리자 생성 기능은 계정 생성 직후 다시 비활성화합니다.
- 데이터베이스 계정은 필요한 스키마 권한만 부여합니다.
- 운영 키와 개발 키를 분리하고 정기적으로 교체합니다.

### 5. 빌드

일반 변경은 WIZ 기본 빌드로 확인합니다. API 함수의 추가·삭제·이름 변경처럼 메타데이터 갱신이 필요한 경우 clean build를 사용합니다.

## 데이터 운영 명령

아래 명령은 외부 API 호출 또는 DB 변경을 수행할 수 있으므로 `.env`와 DB 연결을 확인한 뒤 실행하세요.

| 명령 | 역할 |
|---|---|
| `npm run db:migrate-courses` | 코스 관련 테이블·데이터 이관 |
| `npm run tourapi:seed-places` | TourAPI 장소 기본 데이터 수집 |
| `npm run tourapi:hydrate-place-details` | 기존 장소 상세 정보 보강 |
| `npm run google:match-places` | 내부 장소와 Google Place 매칭 |
| `npm run google:fetch-ratings` | Google 평점·리뷰 수 집계 |
| `npm run signals:expire` | 만료된 신호·즉석 만남 정리 |

## 안전한 커밋 설정

저장소에는 버전 관리되는 pre-commit 훅이 포함되어 있습니다. 한 번 설치하면 매 커밋 직전에 스테이징된 파일을 자동 검사하고, 키·토큰·비밀번호·개인키 또는 로컬 환경값이 발견되면 커밋을 중단합니다.

```bash
npm run hooks:install
npm run secrets:check
```

설치 여부는 다음 명령으로 확인합니다.

```bash
git config --get core.hooksPath
# .githooks
```

권장 작업 흐름은 다음과 같습니다.

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/short-description

git add <변경 파일>
npm run secrets:check:staged
git commit -m "feat: 변경 내용"
git push -u origin feat/short-description
```

푸시 후 Pull Request를 만들고 자동 검사와 리뷰를 통과한 다음 병합합니다. 검사에 걸리면 실제 값을 `.env` 또는 `config/`로 옮기고, 저장소에는 환경변수 참조나 `replace_with_...` 형태의 예시값만 남긴 뒤 다시 커밋하세요. 훅을 우회하는 `--no-verify`는 사용하지 않는 것을 권장합니다.

## GitHub 협업 방식

GACHI는 기업에서 널리 사용하는 GitHub Flow를 기준으로 운영합니다.

- `main`은 항상 배포 가능한 상태로 유지합니다.
- 기능과 수정은 `feat/*`, `fix/*`, `docs/*`, `chore/*` 작업 브랜치에서 진행합니다.
- 모든 변경은 PR로 제출하고 CODEOWNERS 검토와 `quality` 자동 검사를 통과합니다.
- 커밋과 PR 제목은 Conventional Commits 형식을 사용합니다.
- Squash merge를 기본으로 하여 `main`의 이력을 선형으로 유지합니다.
- Dependabot이 npm 및 GitHub Actions 의존성을 정기 점검합니다.

세부 절차는 [CONTRIBUTING.md](CONTRIBUTING.md), 보안 신고 절차는 [SECURITY.md](SECURITY.md)를 확인하세요.

저장소 관리자에게 권장하는 `main` 보호 규칙:

1. Require a pull request before merging
2. Require at least one approval 및 Code Owner review
3. Dismiss stale approvals when new commits are pushed
4. Require status check `quality`
5. Require conversation resolution and linear history
6. Block force pushes and branch deletion

## 저장소 보안 원칙

- 커밋 금지: `.env`, `config/`, DB 덤프, 운영 로그, 업로드 파일, 개인키, 서비스 계정 JSON
- 공개 가능: `.env.example`, `config-sample/`, 구조 설명과 비밀값이 제거된 예제
- 노출이 의심되면 파일만 지우지 말고 키를 즉시 폐기·재발급합니다.
- 이미 원격에 올라간 비밀값은 Git 이력에서도 제거해야 합니다.
- 사용자 위치, 본인 인증 결과와 채팅 데이터는 로그에 원문으로 남기지 않습니다.

## 알려진 운영 과제

- Google Maps의 기존 `Marker`와 `DirectionsService` 사용부는 최신 Advanced Marker 및 Routes API로 단계적 이전이 필요합니다.
- 외부 관광 이미지 제공처의 CORS·가용성에 따라 일부 이미지 요청이 실패할 수 있습니다.
- 위치 공유와 즉석 만남 기능은 만료 배치가 주기적으로 실행되어야 합니다.
- PASS 인증은 PortOne 상점·채널 설정과 허용 도메인이 정확해야 동작합니다.

## 기여하기

기여 절차, 브랜치 규칙, 커밋 형식과 리뷰 기준은 [CONTRIBUTING.md](CONTRIBUTING.md)에 정의되어 있습니다. 버그와 기능 제안은 GitHub Issue 양식을 사용하고, 취약점은 공개 이슈가 아닌 비공개 Security Advisory로 신고해 주세요.

현재 별도의 라이선스 파일은 제공되지 않습니다. 재사용 또는 배포 범위는 저장소 소유자에게 확인하세요.
