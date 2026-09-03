# GACHI Mobile

WIZ의 `bundle/www`를 로컬 웹 번들로 사용하고 Capacitor로 iOS 앱을 생성하는 모바일 셸입니다.

Mac에서 Xcode 실행부터 실기기·TestFlight·App Store 제출까지의 순서는 [`XCODE_GUIDE.md`](XCODE_GUIDE.md)를 따르세요.

## 준비

- Node.js 22 이상
- macOS와 최신 Xcode
- Apple Developer 계정
- WIZ 프로젝트 빌드 완료

## 명령

```bash
cd mobile
npm install
npm run cap:sync
npm run ios:open
```

최초 iOS 프로젝트 생성이 필요한 경우에만 `npm run ios:add`를 실행합니다.

서버 주소를 변경할 때는 `mobile.config.json`을 수정하거나 동기화 시 환경 변수로 덮어씁니다.

```bash
GACHI_SERVER_ORIGIN=https://staging.example.com npm run cap:sync
```

## 구현 범위

- WIZ `bundle/www`와 `bundle/src/assets` 동기화
- API/WIZ/Auth 절대경로의 모바일 서버 주소 변환
- 네이티브 위치 API를 표준 Geolocation API로 연결
- 카메라 촬영 입력, 푸시 권한·토큰 등록
- 외부 링크, 뒤로가기, 키보드, Safe Area
- 커스텀/유니버설 딥링크와 네트워크 오류 화면
- 저장 코스 응답의 로컬 오프라인 캐시

## Apple 등록과 서명

Apple Developer의 Identifiers에서 App ID `com.wizide.gachi`를 만들고 Push Notifications와 Associated Domains를 활성화합니다. Membership의 Team ID를 사용해 Xcode 프로젝트를 고정합니다.

```bash
APPLE_TEAM_ID=ABCDEFGHIJ \
APPLE_BUNDLE_ID=com.wizide.gachi \
npm run apple:configure

APPLE_TEAM_ID=ABCDEFGHIJ npm run apple:check
npm run ios:open
```

`apple:configure`는 Team ID 형식을 검사하고 Xcode의 Debug/Release Signing Team에 반영합니다. 실제 Team ID는 저장소에 커밋하지 않습니다.

GitHub Actions의 `iOS` 워크플로는 macOS에서 서명 없는 Simulator 빌드를 수행합니다. 수동 App Store archive에는 `app-store` 환경에 아래 Secrets가 필요합니다.

- `APPLE_TEAM_ID`
- `APP_STORE_CONNECT_KEY_ID`
- `APP_STORE_CONNECT_ISSUER_ID`
- `APP_STORE_CONNECT_PRIVATE_KEY_BASE64`

App Store Connect API 키는 CI 서명/프로비저닝용이며 APNs 발송 키와 용도가 다릅니다.

## 유니버설 링크

서버에 `config-sample/apple.py`와 동일한 Apple 설정을 반영한 뒤 WIZ를 배포하면 아래 주소가 AASA JSON을 반환합니다.

```text
https://travel.wizide.com/.well-known/apple-app-site-association
```

공개 배포 후 리다이렉트, Content-Type, appID를 검증합니다.

```bash
APPLE_TEAM_ID=ABCDEFGHIJ npm run aasa:verify
```

## APNs 발송 워커

Apple Developer에서 APNs 키를 만든 뒤 서버 전용 환경 파일에 아래 값을 설정합니다. `.p8` 키는 저장소나 앱 번들에 넣지 않습니다.

```bash
APPLE_TEAM_ID=ABCDEFGHIJ
APPLE_BUNDLE_ID=com.wizide.gachi
APNS_KEY_ID=KLMNOPQRST
APNS_PRIVATE_KEY_PATH=/etc/gachi/AuthKey_KLMNOPQRST.p8
APNS_ENVIRONMENT=production
```

```bash
npm run push:check
npm run push:worker
```

동행 신청, 동행 수락, 약속 채팅 이벤트는 `mobile_push_jobs` 큐에 활성 기기별로 저장됩니다. 워커는 APNs HTTP/2 발송, 지수 백오프 재시도, 만료 토큰 비활성화를 처리합니다. systemd 실행 예시는 `deploy/gachi-apns-worker.service.example`에 있습니다.
