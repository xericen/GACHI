#!/usr/bin/env node

const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

const repoRoot = childProcess.execFileSync(
    'git',
    ['rev-parse', '--show-toplevel'],
    { encoding: 'utf8' }
).trim();

const scanAll = process.argv.includes('--all');
const modeLabel = scanAll ? 'tracked working-tree files' : 'staged files';

function git(args, encoding = 'utf8') {
    return childProcess.execFileSync('git', args, {
        cwd: repoRoot,
        encoding,
        maxBuffer: 64 * 1024 * 1024,
    });
}

function nulList(buffer) {
    return buffer
        .toString('utf8')
        .split('\0')
        .filter(Boolean);
}

function isPlaceholder(value) {
    return /(?:replace(?:_with)?|example|placeholder|dummy|sample|redacted|changeme|your[_-]|<[^>]+>|\$\{|process\.env|os\.environ|getenv\(|config\()/i.test(value);
}

function loadLocalSecretValues() {
    const values = [];
    const envPath = path.join(repoRoot, '.env');

    if (fs.existsSync(envPath)) {
        for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
            const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
            if (!match) continue;

            const value = match[2].replace(/^['"]|['"]$/g, '');
            if (value.length >= 8 && !isPlaceholder(value)) {
                values.push({ name: match[1], value });
            }
        }
    }

    const configDir = path.join(repoRoot, 'config');
    if (fs.existsSync(configDir)) {
        for (const fileName of fs.readdirSync(configDir)) {
            if (!fileName.endsWith('.py')) continue;
            const content = fs.readFileSync(path.join(configDir, fileName), 'utf8');
            const assignment = /\b([A-Za-z0-9_]*(?:key|secret|token|password|passwd)[A-Za-z0-9_]*)\b\s*[:=]\s*['"]([^'"]{8,})['"]/gi;

            for (const match of content.matchAll(assignment)) {
                if (!isPlaceholder(match[2])) {
                    values.push({ name: `config:${match[1]}`, value: match[2] });
                }
            }
        }
    }

    return values;
}

const blockedPaths = [
    {
        pattern: /(^|\/)\.env(?:\..+)?$/i,
        allow: /(^|\/)\.env\.example$/i,
        label: 'environment file',
    },
    {
        pattern: /(^|\/)config\//i,
        allow: /(^|\/)config-sample\//i,
        label: 'private runtime config',
    },
    {
        pattern: /(?:^|\/)(?:id_rsa|id_ed25519|credentials[^/]*\.json|service-account[^/]*\.json)$/i,
        label: 'credential or private key file',
    },
    {
        pattern: /\.(?:pem|key|p12|pfx)$/i,
        label: 'private key or certificate bundle',
    },
];

const secretPatterns = [
    ['private key', /-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----/g],
    ['GitHub token', /(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})/g],
    ['Google API key', /AIza[0-9A-Za-z_-]{30,}/g],
    ['OpenAI-style API key', /sk-[A-Za-z0-9_-]{20,}/g],
    ['AWS access key', /AKIA[0-9A-Z]{16}/g],
    ['JWT', /eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g],
    ['URL with embedded credentials', /[a-z][a-z0-9+.-]*:\/\/[^\s/:]+:[^\s/@]+@[^\s/]+/gi],
];

const files = scanAll
    ? nulList(git(['ls-files', '-z'], null))
    : nulList(git(['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'], null));

const localSecrets = loadLocalSecretValues();
const findings = [];

function addFinding(file, label, content, index = 0) {
    const line = content.slice(0, index).split('\n').length;
    findings.push({ file, line, label });
}

for (const file of files) {
    for (const blocked of blockedPaths) {
        if (blocked.pattern.test(file) && !(blocked.allow && blocked.allow.test(file))) {
            findings.push({ file, line: 1, label: blocked.label });
        }
    }

    let buffer;
    try {
        buffer = scanAll
            ? fs.readFileSync(path.join(repoRoot, file))
            : git(['show', `:${file}`], null);
    } catch {
        continue;
    }

    if (buffer.length > 5 * 1024 * 1024 || buffer.includes(0)) continue;
    const content = buffer.toString('utf8');

    for (const [label, pattern] of secretPatterns) {
        pattern.lastIndex = 0;
        for (const match of content.matchAll(pattern)) {
            addFinding(file, label, content, match.index || 0);
        }
    }

    const literalAssignment = /(?<![.\w])(api[_-]?key|client[_-]?secret|secret|access[_-]?token|refresh[_-]?token|password|passwd|private[_-]?key)\b\s*[:=]\s*(['"`])([^'"`\r\n]{8,})\2/gi;
    for (const match of content.matchAll(literalAssignment)) {
        if (!isPlaceholder(match[3])) {
            addFinding(file, `literal ${match[1]} value`, content, match.index || 0);
        }
    }

    for (const secret of localSecrets) {
        let offset = content.indexOf(secret.value);
        while (offset !== -1) {
            addFinding(file, `local value matching ${secret.name}`, content, offset);
            offset = content.indexOf(secret.value, offset + secret.value.length);
        }
    }
}

const uniqueFindings = [...new Map(
    findings.map((finding) => [
        `${finding.file}:${finding.line}:${finding.label}`,
        finding,
    ])
).values()];

if (uniqueFindings.length > 0) {
    console.error(`\n[secret-guard] Blocked: ${uniqueFindings.length} possible secret(s) found in ${modeLabel}.`);
    for (const finding of uniqueFindings) {
        console.error(`- ${finding.file}:${finding.line} (${finding.label})`);
    }
    console.error('\nMove real values to .env or config/, keep placeholders in Git, and try again.');
    process.exit(1);
}

console.log(`[secret-guard] OK: ${files.length} ${modeLabel} checked; no sensitive values found.`);
