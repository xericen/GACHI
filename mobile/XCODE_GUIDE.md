# GACHI Xcode 작업 가이드

이 프로젝트는 새 iOS 앱을 Xcode에서 처음부터 만드는 방식이 아닙니다. WIZ 웹 빌드를 Capacitor가 iOS 프로젝트에 복사하고, Xcode는 서명·실행·배포를 담당합니다.

## 1. Mac 준비

- macOS에 최신 Xcode를 설치하고 한 번 실행해 추가 구성요소 설치를 완료합니다.
- Xcode `Settings > Accounts`에서 Apple Developer Program에 가입된 Apple 계정을 추가합니다.
- Node.js 22 이상과 Git을 설치합니다.
- 프로젝트를 Mac에 clone하거나 복사합니다.

Apple Developer의 `Certificates, Identifiers & Profiles > Identifiers`에서 Explicit App ID를 확인하거나 생성합니다.

- Description: `GACHI`
- Bundle ID: `com.wizide.gachi`
- Capabilities: `Push Notifications`, `Associated Domains`

## 2. 실제 웹 번들 준비

`bundle/`과 `mobile/www/`는 생성 산출물이라 Git에 포함되지 않습니다. Xcode에서 실제 앱을 실행하기 전에 WIZ 빌드가 만든 다음 경로가 Mac 프로젝트에 있어야 합니다.

```text
bundle/www/index.html
bundle/src/assets/
```

ReviewOps/WIZ 환경에서 프로젝트를 빌드한 뒤 `bundle/www`와 `bundle/src/assets`를 Mac의 같은 프로젝트 경로로 복사합니다. GitHub Actions의 `ci:prepare`는 iOS 컴파일만 확인하는 최소 화면이므로 실제 실행·TestFlight·App Store 빌드에 사용하면 안 됩니다.

## 3. Capacitor 동기화와 Xcode 열기

Mac 터미널에서 프로젝트 루트로 이동한 뒤 실행합니다.

```bash
npm ci --prefix mobile
npm run mobile:sync
```

Apple Developer Membership에 표시되는 10자리 Team ID를 적용합니다.

```bash
APPLE_TEAM_ID=실제_10자리_TEAM_ID \
APPLE_BUNDLE_ID=com.wizide.gachi \
npm --prefix mobile run apple:configure

APPLE_TEAM_ID=실제_10자리_TEAM_ID \
npm --prefix mobile run apple:check
```

Xcode를 엽니다.

```bash
npm run mobile:ios
```

명령이 열지 못하면 Finder에서 아래 프로젝트를 직접 엽니다.

```text
mobile/ios/App/App.xcodeproj
```

`npm run ios:add`는 실행하지 않습니다. iOS 프로젝트가 이미 생성되어 있기 때문입니다.

## 4. Xcode 서명 확인

Xcode 왼쪽에서 파란색 `App` 프로젝트를 선택하고 `TARGETS > App > Signing & Capabilities`를 엽니다.

1. `Automatically manage signing`을 켭니다.
2. `Team`에서 가입한 Apple Developer Team을 선택합니다.
3. Bundle Identifier가 `com.wizide.gachi`인지 확인합니다.
4. `Push Notifications` capability가 보이는지 확인합니다.
5. `Associated Domains`에 `applinks:travel.wizide.com`이 있는지 확인합니다.
6. 빨간 Signing 오류가 없어질 때까지 Xcode의 계정·인증서 안내를 처리합니다.

무료 Personal Team은 로컬 테스트에는 사용할 수 있지만 App Store 제출에는 유료 Apple Developer Program 가입이 필요합니다.

## 5. Simulator와 실기기 실행

### Simulator

Xcode 상단 Scheme은 `App`, 기기는 설치된 iPhone Simulator를 선택하고 `Run(▶)`을 누릅니다.

Simulator에서는 화면·로그인·API·딥링크·오프라인 화면을 우선 확인합니다. 카메라, 실제 GPS 이동, APNs 푸시는 실기기 결과로 판단합니다.

### 실기기

1. iPhone을 Mac에 연결하고 이 컴퓨터를 신뢰합니다.
2. iPhone에서 Developer Mode를 활성화합니다.
3. Xcode 상단 실행 기기로 연결된 iPhone을 선택합니다.
4. `Run(▶)`을 누르고 위치·카메라·알림 권한을 직접 허용합니다.

실기기 필수 점검:

- 로그인 후 앱 재실행 시 세션 유지
- 현재 위치와 주변 장소 표시
- 체크인 및 위치 기반 코스
- 카메라 촬영과 사진 업로드
- 알림 허용 후 APNs 토큰 등록
- 동행 신청·수락·약속 채팅 푸시 수신 및 탭 이동
- `gachi://` 딥링크와 `https://travel.wizide.com/access...` 유니버설 링크
- 비행기 모드에서 저장 코스와 네트워크 오류 화면
- 노치 기기의 Safe Area, 키보드, 뒤로가기 동작

## 6. 웹 수정 후 반복 작업

웹 코드를 수정할 때마다 WIZ 빌드 산출물을 Mac의 `bundle/`에 갱신한 뒤 다음 명령을 다시 실행합니다.

```bash
npm run mobile:sync
npm run mobile:verify
```

그 다음 Xcode에서 다시 `Run`합니다. Swift, entitlement, Info.plist 같은 네이티브 파일만 수정했다면 웹 동기화 없이 Xcode에서 다시 빌드할 수 있습니다.

## 7. TestFlight 업로드

먼저 App Store Connect `Apps`에서 앱 레코드를 만듭니다. Bundle ID는 반드시 `com.wizide.gachi`를 선택합니다.

Xcode에서:

1. `TARGETS > App > General`에서 Version과 Build를 확인합니다.
2. 업로드할 때마다 Build 번호를 증가시킵니다.
3. 실행 기기를 `Any iOS Device (arm64)` 또는 Generic iOS Device로 선택합니다.
4. `Product > Archive`를 실행합니다.
5. Organizer에서 archive를 선택하고 `Distribute App`을 누릅니다.
6. `TestFlight & App Store`와 자동 서명을 선택해 업로드합니다.
7. App Store Connect의 `TestFlight`에서 처리 완료 후 내부 테스터에게 배포합니다.

실기기 TestFlight 검증이 끝나기 전에는 App Review에 제출하지 않습니다.

## 8. App Store 제출 전 체크리스트

- 앱 이름, 설명, 카테고리, 연령 등급
- iPhone 규격별 App Store 스크린샷
- 개인정보처리방침 URL과 고객지원 URL
- 위치·사진·카메라·알림 데이터 사용 목적과 App Privacy 답변
- 로그인 계정이 필요한 경우 심사용 테스트 계정과 사용 방법
- 수출 규정(암호화) 질문
- 공개 AASA 검증

```bash
APPLE_TEAM_ID=실제_10자리_TEAM_ID \
npm --prefix mobile run aasa:verify
```

마지막으로 App Store Connect에서 출시 버전의 Build를 선택하고 심사 정보를 작성한 뒤 `Add for Review` 및 `Submit for Review`를 진행합니다.

## 자주 막히는 오류

- `No profiles for com.wizide.gachi`: App ID, Team, 자동 서명을 다시 확인합니다.
- `Bundle identifier is not available`: 해당 Bundle ID가 다른 Team에 등록됐는지 확인합니다.
- 흰 화면 또는 `bundle/www/index.html` 없음: 실제 WIZ 빌드 산출물을 복사하고 `npm run mobile:sync`를 다시 실행합니다.
- 푸시 토큰은 생기지만 알림이 안 옴: APNs Key ID·Team ID·환경(sandbox/production), 서버 워커 상태를 확인합니다.
- 유니버설 링크가 Safari로 열림: AASA의 App ID Prefix·Bundle ID, Content-Type, HTTPS 무리다이렉트 응답과 앱 재설치를 확인합니다.

## 공식 참고 문서

- [Capacitor 공식 문서](https://capacitorjs.com/docs)
- [Apple App ID 등록](https://developer.apple.com/help/account/identifiers/register-an-app-id/)
- [Xcode에서 TestFlight·App Store 배포](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)
- [App Store Connect 빌드 업로드](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds)
- [TestFlight 개요](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview)
