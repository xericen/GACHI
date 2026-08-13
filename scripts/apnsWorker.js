#!/usr/bin/env node

const crypto = require('node:crypto');
const fs = require('node:fs');
const http2 = require('node:http2');
const { connect } = require('./db');

const REQUIRED_ENV = ['APPLE_TEAM_ID', 'APNS_KEY_ID', 'APNS_PRIVATE_KEY_PATH'];
const BUNDLE_ID = process.env.APPLE_BUNDLE_ID || 'com.wizide.gachi';
const IS_SANDBOX = (process.env.APNS_ENVIRONMENT || 'production').toLowerCase() === 'sandbox';
const APNS_ORIGIN = IS_SANDBOX
    ? 'https://api.sandbox.push.apple.com'
    : 'https://api.push.apple.com';
const MAX_ATTEMPTS = Math.max(1, Number(process.env.APNS_MAX_ATTEMPTS || 5));
const POLL_INTERVAL_MS = Math.max(500, Number(process.env.APNS_POLL_INTERVAL_MS || 2000));
const BATCH_SIZE = Math.min(100, Math.max(1, Number(process.env.APNS_BATCH_SIZE || 25)));
const RUN_ONCE = process.argv.includes('--once');
const CHECK_ONLY = process.argv.includes('--check');

let stopped = false;
let cachedProviderToken = null;
let cachedProviderTokenAt = 0;

function assertConfiguration() {
    const missing = REQUIRED_ENV.filter((key) => !String(process.env[key] || '').trim());
    if (missing.length) throw new Error(`APNs 환경 변수 누락: ${missing.join(', ')}`);
    if (!/^[A-Z0-9]{10}$/.test(process.env.APPLE_TEAM_ID)) {
        throw new Error('APPLE_TEAM_ID는 Apple Developer의 10자리 Team ID여야 합니다.');
    }
    if (!/^[A-Z0-9]{10}$/.test(process.env.APNS_KEY_ID)) {
        throw new Error('APNS_KEY_ID는 Apple Developer의 10자리 Key ID여야 합니다.');
    }
    if (!/^[A-Za-z0-9.-]+$/.test(BUNDLE_ID)) throw new Error('APPLE_BUNDLE_ID 형식이 올바르지 않습니다.');
    if (!fs.existsSync(process.env.APNS_PRIVATE_KEY_PATH)) {
        throw new Error('APNS_PRIVATE_KEY_PATH 파일을 찾을 수 없습니다.');
    }
}

function base64url(value) {
    return Buffer.from(value).toString('base64url');
}

function providerToken() {
    const now = Math.floor(Date.now() / 1000);
    if (cachedProviderToken && now - cachedProviderTokenAt < 50 * 60) return cachedProviderToken;
    const header = base64url(JSON.stringify({ alg: 'ES256', kid: process.env.APNS_KEY_ID }));
    const claims = base64url(JSON.stringify({ iss: process.env.APPLE_TEAM_ID, iat: now }));
    const signingInput = `${header}.${claims}`;
    const privateKey = fs.readFileSync(process.env.APNS_PRIVATE_KEY_PATH, 'utf8');
    const signature = crypto.sign('sha256', Buffer.from(signingInput), {
        key: privateKey,
        dsaEncoding: 'ieee-p1363',
    });
    cachedProviderToken = `${signingInput}.${signature.toString('base64url')}`;
    cachedProviderTokenAt = now;
    return cachedProviderToken;
}

function payloadFor(job) {
    let custom = {};
    try {
        custom = JSON.parse(job.payload || '{}');
    } catch {
        custom = {};
    }
    const payload = {
        ...custom,
        aps: {
            alert: { title: job.title || 'GACHI', body: job.body || '' },
            sound: 'default',
        },
        event_type: job.event_type || 'general',
        deep_link: job.deep_link || '',
    };
    const encoded = JSON.stringify(payload);
    if (Buffer.byteLength(encoded, 'utf8') > 4096) {
        payload.aps.alert.body = String(payload.aps.alert.body || '').slice(0, 180);
        delete payload.metadata;
    }
    return JSON.stringify(payload);
}

function sendNotification(client, job) {
    return new Promise((resolve, reject) => {
        const request = client.request({
            ':method': 'POST',
            ':path': `/3/device/${encodeURIComponent(job.device_token)}`,
            authorization: `bearer ${providerToken()}`,
            'apns-topic': BUNDLE_ID,
            'apns-push-type': 'alert',
            'apns-priority': '10',
            'apns-collapse-id': `${job.event_type || 'general'}:${job.user_id || ''}`.slice(0, 64),
        });
        const chunks = [];
        let status = 0;
        request.setEncoding('utf8');
        request.on('response', (headers) => { status = Number(headers[':status'] || 0); });
        request.on('data', (chunk) => chunks.push(chunk));
        request.on('end', () => {
            let response = {};
            try { response = JSON.parse(chunks.join('') || '{}'); } catch { response = {}; }
            resolve({ status, reason: response.reason || '' });
        });
        request.on('error', reject);
        request.setTimeout(15000, () => request.destroy(new Error('APNs request timed out')));
        request.end(payloadFor(job));
    });
}

async function claimJobs(db) {
    await db.execute(
        "UPDATE mobile_push_jobs SET status = 'retry', available_at = NOW(), updated_at = NOW(), last_error = 'stale worker claim recovered' WHERE status = 'sending' AND updated_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE)"
    );
    const [rows] = await db.execute(
        "SELECT * FROM mobile_push_jobs WHERE status IN ('queued', 'retry') AND available_at <= NOW() ORDER BY created_at ASC LIMIT ?",
        [BATCH_SIZE]
    );
    const claimed = [];
    for (const row of rows) {
        const [result] = await db.execute(
            "UPDATE mobile_push_jobs SET status = 'sending', attempts = attempts + 1, updated_at = NOW() WHERE id = ? AND status IN ('queued', 'retry')",
            [row.id]
        );
        if (result.affectedRows) claimed.push({ ...row, attempts: Number(row.attempts || 0) + 1 });
    }
    return claimed;
}

async function recordResult(db, job, result) {
    if (result.status === 200) {
        await db.execute(
            "UPDATE mobile_push_jobs SET status = 'sent', sent_at = NOW(), updated_at = NOW(), last_error = '' WHERE id = ?",
            [job.id]
        );
        return 'sent';
    }
    const invalidToken = result.status === 410 || ['BadDeviceToken', 'DeviceTokenNotForTopic', 'Unregistered'].includes(result.reason);
    if (invalidToken) {
        await db.execute(
            "UPDATE mobile_device SET enabled = 0, updated = NOW() WHERE device_token = ?",
            [job.device_token]
        );
    }
    const retryable = [429, 500, 503].includes(result.status) && job.attempts < MAX_ATTEMPTS;
    const nextStatus = retryable ? 'retry' : 'failed';
    const delaySeconds = Math.min(3600, 30 * (2 ** Math.max(0, job.attempts - 1)));
    await db.execute(
        "UPDATE mobile_push_jobs SET status = ?, available_at = DATE_ADD(NOW(), INTERVAL ? SECOND), updated_at = NOW(), last_error = ? WHERE id = ?",
        [nextStatus, delaySeconds, `${result.status || 'network'} ${result.reason || 'APNs request failed'}`.slice(0, 1000), job.id]
    );
    return nextStatus;
}

async function recordNetworkFailure(db, job, error) {
    const retryable = job.attempts < MAX_ATTEMPTS;
    const delaySeconds = Math.min(3600, 30 * (2 ** Math.max(0, job.attempts - 1)));
    await db.execute(
        "UPDATE mobile_push_jobs SET status = ?, available_at = DATE_ADD(NOW(), INTERVAL ? SECOND), updated_at = NOW(), last_error = ? WHERE id = ?",
        [retryable ? 'retry' : 'failed', delaySeconds, String(error && error.message || error).slice(0, 1000), job.id]
    );
}

async function processBatch(db) {
    const jobs = await claimJobs(db);
    if (!jobs.length) return { claimed: 0, sent: 0, retry: 0, failed: 0 };
    const client = http2.connect(APNS_ORIGIN);
    client.on('error', () => undefined);
    const summary = { claimed: jobs.length, sent: 0, retry: 0, failed: 0 };
    try {
        for (const job of jobs) {
            try {
                const state = await recordResult(db, job, await sendNotification(client, job));
                summary[state] += 1;
            } catch (error) {
                await recordNetworkFailure(db, job, error);
                summary[job.attempts < MAX_ATTEMPTS ? 'retry' : 'failed'] += 1;
            }
        }
    } finally {
        client.close();
    }
    return summary;
}

async function main() {
    assertConfiguration();
    if (CHECK_ONLY) {
        providerToken();
        console.log(JSON.stringify({ configured: true, bundleId: BUNDLE_ID, environment: IS_SANDBOX ? 'sandbox' : 'production' }));
        return;
    }
    const db = await connect();
    try {
        do {
            const summary = await processBatch(db);
            if (summary.claimed || RUN_ONCE) {
                console.log(JSON.stringify({ ...summary, environment: IS_SANDBOX ? 'sandbox' : 'production', checkedAt: new Date().toISOString() }));
            }
            if (RUN_ONCE || stopped) break;
            await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        } while (!stopped);
    } finally {
        await db.end();
    }
}

for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => { stopped = true; });
}

main().catch((error) => {
    console.error(`[apns-worker] ${error.message}`);
    process.exit(1);
});
