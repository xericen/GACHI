const fs = require('node:fs');
const path = require('node:path');

const packageFile = require.resolve('ngc-esbuild/package.json', { paths: [process.cwd()] });
const packageInfo = JSON.parse(fs.readFileSync(packageFile, 'utf8'));

if (packageInfo.version !== '0.0.83') {
    throw new Error(`Unsupported ngc-esbuild shell version: ${packageInfo.version}`);
}

const adapterEntry = path.join(path.dirname(packageFile), packageInfo.main);
const adapter = `const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

class WizAngularCliBuild {
    constructor() {
        const sourceRoot = path.join(process.cwd(), 'src');
        let declarationCount = 0;
        const visit = (directory) => {
            for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
                const target = path.join(directory, entry.name);
                if (entry.isDirectory()) {
                    visit(target);
                    continue;
                }
                if (!entry.isFile() || !target.endsWith('.ts')) continue;
                let source = fs.readFileSync(target, 'utf8');
                source = source.replace(
                    /@(Component|Directive|Pipe)\\(\\{([\\s\\S]*?)\\}\\)/g,
                    (match, kind, body) => {
                        declarationCount++;
                        if (/\\bstandalone\\s*:/.test(body)) return match;
                        return '@' + kind + '({' + '\\n    standalone: false,' + body + '})';
                    }
                );
                source = source.replace(/styleUrls\\s*:\\s*\\[([^\\]]*)\\]/g, (match, body) => {
                    const existing = [...body.matchAll(/["']([^"']+)["']/g)]
                        .map((item) => item[1])
                        .filter((relative) => fs.existsSync(path.resolve(path.dirname(target), relative)));
                    return 'styleUrls: [' + existing.map((relative) => "'" + relative + "'").join(', ') + ']';
                });
                fs.writeFileSync(target, source, 'utf8');
            }
        };
        visit(sourceRoot);
        if (declarationCount === 0) {
            throw new Error('No WIZ Angular declarations found for compatibility preparation');
        }

        const compatibilityConfig = path.join(process.cwd(), 'tsconfig.wiz.json');
        fs.writeFileSync(compatibilityConfig, JSON.stringify({
            extends: './tsconfig.app.json',
            compilerOptions: {
                strict: false,
                noImplicitAny: false,
                noImplicitThis: false,
                noImplicitReturns: false,
                noPropertyAccessFromIndexSignature: false
            },
            angularCompilerOptions: {
                strictTemplates: false,
                strictInjectionParameters: false,
                strictInputAccessModifiers: false
            }
        }, null, 2));

        const generatedIndex = path.join(process.cwd(), 'src', 'index.html');
        if (fs.existsSync(generatedIndex)) {
            const source = fs.readFileSync(generatedIndex, 'utf8');
            const withoutLegacyBundles = source.replace(
                /<script\\b[^>]*\\bsrc=["'](?:vendor|main)\\.js["'][^>]*><\\/script>\\s*/gi,
                ''
            );
            fs.writeFileSync(generatedIndex, withoutLegacyBundles, 'utf8');
        }

        const generatedStyles = path.join(process.cwd(), 'src', 'styles.scss');
        if (fs.existsSync(generatedStyles)) {
            const source = fs.readFileSync(generatedStyles, 'utf8');
            const modernSassEntry = source.replace(
                /^\\s*@import\\s+["']styles\\/styles["']\\s*;?\\s*$/m,
                '@use "styles/styles";'
            );
            fs.writeFileSync(generatedStyles, modernSassEntry, 'utf8');
        }

        const cli = require.resolve('@angular/cli/bin/ng.js', { paths: [process.cwd()] });
        const result = spawnSync(process.execPath, [
            cli,
            'build',
            '--configuration',
            'production',
            '--ts-config',
            'tsconfig.wiz.json',
            '--output-hashing',
            'none'
        ], { stdio: 'inherit' });

        if (result.error) throw result.error;
        if (result.status !== 0) {
            throw new Error('Angular CLI build failed with exit code ' + result.status);
        }

        this.resolve = new Promise(() => {});
    }
}

module.exports = WizAngularCliBuild;
`;

fs.writeFileSync(adapterEntry, adapter, 'utf8');

if (!fs.readFileSync(adapterEntry, 'utf8').includes('class WizAngularCliBuild')) {
    throw new Error('WIZ Angular CLI adapter verification failed');
}

process.stdout.write('[postinstall] WIZ Angular CLI adapter configured\n');
