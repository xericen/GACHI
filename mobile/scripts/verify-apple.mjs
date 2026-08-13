import { access, readFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const project = await readFile(path.join(root, 'ios/App/App.xcodeproj/project.pbxproj'), 'utf8');
const entitlements = await readFile(path.join(root, 'ios/App/App/App.entitlements'), 'utf8');
const bundleId = String(process.env.APPLE_BUNDLE_ID || 'com.wizide.gachi').trim();
const teamId = String(process.env.APPLE_TEAM_ID || '').trim();
const requireTeam = process.argv.includes('--require-team');
const requireApns = process.argv.includes('--require-apns');

if (!project.includes(`PRODUCT_BUNDLE_IDENTIFIER = ${bundleId};`)) {
  throw new Error(`Xcode Bundle ID가 ${bundleId}와 일치하지 않습니다.`);
}
for (const marker of ['com.apple.developer.associated-domains', 'applinks:travel.wizide.com', 'aps-environment']) {
  if (!entitlements.includes(marker)) throw new Error(`iOS entitlement 누락: ${marker}`);
}

if (requireTeam || teamId) {
  if (!/^[A-Z0-9]{10}$/.test(teamId)) throw new Error('APPLE_TEAM_ID 10자리 값을 설정하세요.');
  if (!project.includes(`DEVELOPMENT_TEAM = ${teamId};`)) {
    throw new Error('Xcode Team ID가 주입되지 않았습니다. npm run apple:configure를 먼저 실행하세요.');
  }
}

if (requireApns) {
  const keyId = String(process.env.APNS_KEY_ID || '').trim();
  const keyPath = String(process.env.APNS_PRIVATE_KEY_PATH || '').trim();
  if (!/^[A-Z0-9]{10}$/.test(keyId)) throw new Error('APNS_KEY_ID 10자리 값을 설정하세요.');
  if (!keyPath) throw new Error('APNS_PRIVATE_KEY_PATH를 설정하세요.');
  await access(keyPath);
  const key = await readFile(keyPath, 'utf8');
  if (!key.includes('BEGIN PRIVATE KEY')) throw new Error('APNs .p8 개인 키 형식이 올바르지 않습니다.');
}

console.log(JSON.stringify({
  bundleId,
  teamConfigured: Boolean(teamId && project.includes(`DEVELOPMENT_TEAM = ${teamId};`)),
  apnsCredentialsChecked: requireApns,
}));
