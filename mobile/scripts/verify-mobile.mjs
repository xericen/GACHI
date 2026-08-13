import { access, readFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const required = [
  'capacitor.config.ts',
  'www/index.html',
  'www/mobile-config.js',
  'www/mobile-runtime.js',
  'ios/App/App/Info.plist',
  'ios/App/App/PrivacyInfo.xcprivacy',
  'ios/App/App/App.entitlements',
  'ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png'
];

const missing = [];
for (const file of required) {
  try {
    await access(path.join(root, file));
  } catch {
    missing.push(file);
  }
}
if (missing.length) {
  throw new Error(`모바일 필수 파일 누락: ${missing.join(', ')}`);
}

const index = await readFile(path.join(root, 'www/index.html'), 'utf8');
for (const marker of ['mobile-config.js', 'mobile-runtime.js', '<base href="./">']) {
  if (!index.includes(marker)) throw new Error(`index.html 모바일 마커 누락: ${marker}`);
}

const plist = await readFile(path.join(root, 'ios/App/App/Info.plist'), 'utf8');
for (const key of ['NSLocationWhenInUseUsageDescription', 'NSCameraUsageDescription', 'CFBundleURLSchemes']) {
  if (!plist.includes(key)) throw new Error(`Info.plist 권한/딥링크 설정 누락: ${key}`);
}

const project = await readFile(path.join(root, 'ios/App/App.xcodeproj/project.pbxproj'), 'utf8');
for (const marker of ['PrivacyInfo.xcprivacy in Resources', 'CODE_SIGN_ENTITLEMENTS', 'com.wizide.gachi', 'com.apple.Push', 'APS_ENVIRONMENT = production']) {
  if (!project.includes(marker)) throw new Error(`Xcode 프로젝트 설정 누락: ${marker}`);
}

console.log('GACHI 모바일 셸 정적 검증 완료');
