import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const projectPath = path.join(root, 'ios/App/App.xcodeproj/project.pbxproj');
const teamId = String(process.env.APPLE_TEAM_ID || '').trim();
const bundleId = String(process.env.APPLE_BUNDLE_ID || 'com.wizide.gachi').trim();

if (!/^[A-Z0-9]{10}$/.test(teamId)) {
  throw new Error('APPLE_TEAM_ID는 Apple Developer Membership의 10자리 Team ID여야 합니다.');
}
if (!/^[A-Za-z0-9.-]+$/.test(bundleId)) throw new Error('APPLE_BUNDLE_ID 형식이 올바르지 않습니다.');

let project = await readFile(projectPath, 'utf8');
project = project.replace(/PRODUCT_BUNDLE_IDENTIFIER = [^;]+;/g, `PRODUCT_BUNDLE_IDENTIFIER = ${bundleId};`);
if (/DEVELOPMENT_TEAM = [^;]*;/g.test(project)) {
  project = project.replace(/DEVELOPMENT_TEAM = [^;]*;/g, `DEVELOPMENT_TEAM = ${teamId};`);
} else {
  project = project.replace(
    /CODE_SIGN_STYLE = Automatic;/g,
    `CODE_SIGN_STYLE = Automatic;\n\t\t\t\tDEVELOPMENT_TEAM = ${teamId};`
  );
}
await writeFile(projectPath, project, 'utf8');
console.log(`Apple 서명 설정 반영: ${teamId}.${bundleId}`);
