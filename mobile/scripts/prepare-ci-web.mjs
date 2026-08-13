import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const webRoot = path.join(root, 'www');

await mkdir(webRoot, { recursive: true });
await writeFile(path.join(webRoot, 'index.html'), `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <base href="./">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>GACHI CI Shell</title>
</head>
<body>
  <main id="gachi-ci-shell">GACHI iOS build verification</main>
  <script src="mobile-config.js"></script>
  <script src="mobile-runtime.js"></script>
</body>
</html>
`, 'utf8');
await writeFile(path.join(webRoot, 'mobile-config.js'), `window.__GACHI_MOBILE_CONFIG__ = {
  serverOrigin: 'https://travel.wizide.com',
  allowedHosts: ['travel.wizide.com'],
  deepLinkScheme: 'gachi'
};
`, 'utf8');
await writeFile(path.join(webRoot, 'mobile-runtime.js'), `window.__GACHI_CI_SHELL__ = true;\n`, 'utf8');

console.log('GACHI iOS CI용 최소 웹 셸 생성 완료');
