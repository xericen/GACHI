import process from 'node:process';

const origin = String(process.env.GACHI_SERVER_ORIGIN || 'https://travel.wizide.com').replace(/\/$/, '');
const teamId = String(process.env.APPLE_TEAM_ID || '').trim();
const appIdPrefix = String(process.env.APPLE_APP_ID_PREFIX || teamId).trim();
const bundleId = String(process.env.APPLE_BUNDLE_ID || 'com.wizide.gachi').trim();
if (!/^[A-Z0-9]{10}$/.test(appIdPrefix)) throw new Error('AASA 검증에는 APPLE_APP_ID_PREFIX 또는 APPLE_TEAM_ID 10자리 값이 필요합니다.');

const url = `${origin}/.well-known/apple-app-site-association`;
const response = await fetch(url, { redirect: 'manual' });
if (response.status !== 200) throw new Error(`AASA 응답 상태가 200이 아닙니다: ${response.status}`);
if (response.status >= 300 && response.status < 400) throw new Error('AASA URL은 리다이렉트 없이 응답해야 합니다.');
if (!String(response.headers.get('content-type') || '').toLowerCase().includes('application/json')) {
  throw new Error('AASA Content-Type이 application/json이 아닙니다.');
}
const payload = await response.json();
const appIds = (payload.applinks?.details || []).flatMap((item) => item.appIDs || []);
const expected = `${appIdPrefix}.${bundleId}`;
if (!appIds.includes(expected)) throw new Error(`AASA appID 누락: ${expected}`);
console.log(`AASA 공개 검증 완료: ${url} (${expected})`);
