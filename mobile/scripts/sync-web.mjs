import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { build } from 'esbuild';

const mobileRoot = path.resolve(import.meta.dirname, '..');
const projectRoot = path.resolve(mobileRoot, '..');
const wizWebRoot = path.join(projectRoot, 'bundle', 'www');
const wizAssetsRoot = path.join(projectRoot, 'bundle', 'src', 'assets');
const outputRoot = path.join(mobileRoot, 'www');
const configPath = path.join(mobileRoot, 'mobile.config.json');

if (!existsSync(path.join(wizWebRoot, 'index.html'))) {
  throw new Error('bundle/www/index.html이 없습니다. 프로젝트 루트에서 WIZ 빌드를 먼저 실행하세요.');
}

const rawConfig = JSON.parse(await readFile(configPath, 'utf8'));
const serverOrigin = String(process.env.GACHI_SERVER_ORIGIN || rawConfig.serverOrigin || '')
  .trim()
  .replace(/\/$/, '');
if (!/^https:\/\//.test(serverOrigin)) {
  throw new Error('모바일 서버 주소는 HTTPS여야 합니다.');
}

await rm(outputRoot, { recursive: true, force: true });
await mkdir(outputRoot, { recursive: true });
await cp(wizWebRoot, outputRoot, { recursive: true });
if (existsSync(wizAssetsRoot)) {
  await cp(wizAssetsRoot, path.join(outputRoot, 'assets'), { recursive: true });
}

const runtimeConfig = {
  ...rawConfig,
  serverOrigin,
  buildTime: new Date().toISOString()
};
await writeFile(
  path.join(outputRoot, 'mobile-config.js'),
  `window.GACHI_MOBILE_CONFIG = ${JSON.stringify(runtimeConfig)};\n`,
  'utf8'
);

await build({
  entryPoints: [path.join(mobileRoot, 'src', 'runtime.ts')],
  outfile: path.join(outputRoot, 'mobile-runtime.js'),
  bundle: true,
  minify: true,
  sourcemap: true,
  platform: 'browser',
  format: 'iife',
  target: ['safari15']
});

const indexPath = path.join(outputRoot, 'index.html');
let index = await readFile(indexPath, 'utf8');
index = index
  .replace(/<base\s+href="\/">/i, '<base href="./">')
  .replace(/(href|src)="\/assets\//g, '$1="./assets/')
  .replace(/<link\s+rel="manifest"[^>]*>/i, '')
  .replace(
    /<\/head>/i,
    '<script src="mobile-config.js"></script><script src="mobile-runtime.js"></script></head>'
  );
await writeFile(indexPath, index, 'utf8');

console.log(`GACHI 모바일 웹 동기화 완료: ${serverOrigin}`);
