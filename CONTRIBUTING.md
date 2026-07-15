# GACHI 기여 가이드

GACHI는 `main`을 항상 배포 가능한 상태로 유지하는 GitHub Flow를 사용합니다. 모든 변경은 짧게 유지되는 작업 브랜치에서 시작하고 Pull Request(PR)를 통해 검토·병합합니다.

## 기본 원칙

- `main`에 직접 커밋하거나 강제 푸시하지 않습니다.
- 한 브랜치와 PR에는 하나의 목적만 담습니다.
- 기능 변경과 무관한 대규모 포맷 변경을 섞지 않습니다.
- 비밀값, 개인정보, 운영 로그와 DB 덤프를 커밋하지 않습니다.
- PR 병합 전 자동 검사 통과와 코드 소유자 검토를 확인합니다.

## 브랜치 이름

| 유형 | 형식 | 예시 |
|---|---|---|
| 기능 | `feat/<topic>` | `feat/instant-meeting-chat` |
| 버그 수정 | `fix/<topic>` | `fix/map-route-fallback` |
| 문서 | `docs/<topic>` | `docs/setup-guide` |
| 리팩터링 | `refactor/<topic>` | `refactor/course-service` |
| 운영·설정 | `chore/<topic>` | `chore/dependabot-policy` |
| 긴급 수정 | `hotfix/<topic>` | `hotfix/auth-session` |

영문 소문자와 하이픈을 사용하고, 이슈가 있다면 `fix/123-map-route`처럼 번호를 포함할 수 있습니다.

## 개발 흐름

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/short-description

# 작업과 검증
npm run secrets:check

git add <변경 파일>
git commit -m "feat: 변경 내용"
git push -u origin feat/short-description
```

푸시 후 PR을 만들고 템플릿의 항목을 작성합니다. 리뷰 반영은 같은 브랜치에 추가 커밋으로 올리며, 승인 후 GitHub의 Squash and merge를 기본으로 사용합니다.

## 커밋 메시지

Conventional Commits 형식을 사용합니다.

```text
<type>(optional-scope): 짧고 명확한 설명
```

허용하는 주요 `type`은 다음과 같습니다.

- `feat`: 사용자 기능 추가
- `fix`: 버그 수정
- `docs`: 문서만 변경
- `refactor`: 동작을 바꾸지 않는 구조 개선
- `test`: 테스트 추가·수정
- `perf`: 성능 개선
- `build`: 빌드·의존성 변경
- `ci`: CI/CD 변경
- `chore`: 기타 유지보수
- `revert`: 기존 변경 되돌리기

예시:

```text
feat(companion): add instant meeting expiration
fix(map): handle empty directions response
docs: clarify local credential setup
```

## Pull Request 기준

- 제목도 Conventional Commits 형식을 따릅니다.
- 변경 이유와 사용자 영향을 설명합니다.
- 실행한 검증을 체크하고 미실행 항목은 이유를 적습니다.
- UI 변경은 가능한 경우 전·후 캡처를 첨부합니다.
- DB, 환경변수, 배치 작업과 배포 순서에 미치는 영향을 기록합니다.
- 보안 관련 상세 내용은 공개 이슈나 PR에 작성하지 않습니다.

## 필수 검증

```bash
npm ci
npm run secrets:check
python -m compileall -q config-sample src
find scripts services -name '*.js' -print0 | xargs -0 -n1 node --check
```

WIZ 화면이나 API를 변경했다면 WIZ 일반 빌드를 실행합니다. API 함수의 추가·삭제·이름 변경이 있다면 clean build를 사용합니다.

## 리뷰와 병합

- 작성자 본인이 아닌 최소 1명의 승인을 권장합니다.
- CODEOWNERS 대상 파일은 코드 소유자의 승인을 받습니다.
- 새 커밋이 올라오면 기존 승인을 다시 확인합니다.
- 모든 대화와 자동 검사를 해결한 뒤 병합합니다.
- merge commit보다 squash merge를 사용해 `main`의 선형 이력을 유지합니다.
- 병합 후 작업 브랜치를 삭제합니다.

## 긴급 수정

장애 대응도 원칙적으로 `hotfix/*` 브랜치와 PR을 사용합니다. 불가피하게 관리자 우회가 필요했다면 복구 후 변경 이유, 검증, 후속 조치를 이슈나 회고에 남깁니다.

## 민감정보 처리

pre-commit 훅 설치:

```bash
npm run hooks:install
```

훅이 민감정보를 발견하면 커밋을 중단합니다. 실제 값은 `.env` 또는 `config/`로 옮기고 공개 파일에는 환경변수 참조나 예시값만 남겨야 합니다. `--no-verify`로 검사를 우회하지 마세요.
