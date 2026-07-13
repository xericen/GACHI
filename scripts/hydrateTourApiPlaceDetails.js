const fs = require('node:fs');
const path = require('node:path');
const { connect } = require('./db');
const { TourApiClient } = require('../services/tourApiClient');

const PRIORITY_CONTENT_TYPE_IDS = ['12', '14', '28', '39'];
const OPTIONAL_CONTENT_TYPE_IDS = ['15', '32', '38'];
const ALL_AREAS = [
    '서울',
    '부산',
    '제주',
    '강원 강릉',
    '강원 속초',
    '전북 전주',
    '전남 여수',
    '경북 경주',
    '대전',
    '인천',
    '경기 가평'
];

const STAGES = {
    '1': {
        label: '서울/부산/제주 우선 카테고리',
        areas: ['서울', '부산', '제주'],
        contentTypeIds: PRIORITY_CONTENT_TYPE_IDS
    },
    '2': {
        label: '나머지 지역 우선 카테고리',
        areas: ['강원 강릉', '강원 속초', '전북 전주', '전남 여수', '경북 경주', '대전', '인천', '경기 가평'],
        contentTypeIds: PRIORITY_CONTENT_TYPE_IDS
    },
    '3': {
        label: '쇼핑/숙박/축제 추가 카테고리',
        areas: ALL_AREAS,
        contentTypeIds: OPTIONAL_CONTENT_TYPE_IDS
    }
};

const REGION_FILTERS = {
    busan: {
        label: '부산',
        aliases: ['busan', '부산', '부산광역시'],
        areas: ['부산'],
        ldongRegnCodes: ['26']
    }
};

const DEFAULT_BATCH_SIZE = 250;
const MIN_REQUEST_DELAY_MS = 100;
const MAX_REQUEST_DELAY_MS = 200;
const BATCH_DELAY_MS = 3000;
const PROGRESS_FILE = path.join(__dirname, '.hydrateTourApiPlaceDetails.progress.json');
const FAILURE_LOG_FILE = path.join(__dirname, 'hydrateTourApiPlaceDetails.failures.jsonl');
const MAX_CONSECUTIVE_FAILURES = 10;
const DEFAULT_LOG_EVERY = 25;
const DEFAULT_CONCURRENCY = 3;

const USAGE_TIME_FIELDS = [
    'usetime',
    'usetimeculture',
    'usetimefestival',
    'usetimeleports',
    'opentime',
    'opentimefood',
    'opentimeshopping',
    'playtime',
    'taketime',
    'checkintime'
];
const REST_DATE_FIELDS = [
    'restdate',
    'restdateculture',
    'restdateleports',
    'restdatefood',
    'restdateshopping',
    'restdateleports'
];
const PARKING_FIELDS = [
    'parking',
    'parkingculture',
    'parkingleports',
    'parkingfood',
    'parkingshopping',
    'parkinglodging'
];
const INFOCENTER_FIELDS = [
    'infocenter',
    'infocenterculture',
    'infocenterleports',
    'infocenterfood',
    'infocentershopping',
    'infocenterlodging'
];

function nowSql() {
    const date = new Date();
    const pad = (value) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function requestDelayMs() {
    const span = MAX_REQUEST_DELAY_MS - MIN_REQUEST_DELAY_MS;
    return MIN_REQUEST_DELAY_MS + Math.floor(Math.random() * (span + 1));
}

function cleanText(value) {
    return String(value || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function limitText(value, maxLength) {
    const text = cleanText(value);
    return text.length > maxLength ? text.slice(0, maxLength) : text;
}

function firstItem(result) {
    return result.items && result.items.length ? result.items[0] : null;
}

function firstText(source, fields) {
    if (!source) return '';
    for (const field of fields) {
        const value = cleanText(source[field]);
        if (value) return value;
    }
    return '';
}

function usageTimeFor(intro) {
    const checkin = cleanText(intro?.checkintime);
    const checkout = cleanText(intro?.checkouttime);
    if (checkin || checkout) {
        return [checkin ? `체크인 ${checkin}` : '', checkout ? `체크아웃 ${checkout}` : ''].filter(Boolean).join(' / ');
    }
    return firstText(intro, USAGE_TIME_FIELDS);
}

function parseArgs(argv) {
    const options = {
        stage: '1',
        stages: [],
        region: '',
        estimateOnly: false,
        resetProgress: false,
        retryFailures: false,
        batchSize: DEFAULT_BATCH_SIZE,
        maxBatches: 0,
        logEvery: DEFAULT_LOG_EVERY,
        concurrency: DEFAULT_CONCURRENCY,
        areas: [],
        contentTypeIds: []
    };
    for (const arg of argv) {
        if (arg === '--estimate') {
            options.estimateOnly = true;
        } else if (arg === '--reset-progress') {
            options.resetProgress = true;
        } else if (arg === '--retry-failures') {
            options.retryFailures = true;
        } else if (arg.startsWith('--stage=')) {
            options.stage = arg.slice('--stage='.length);
        } else if (arg.startsWith('--stages=')) {
            options.stages = arg.slice('--stages='.length).split(',').map((value) => value.trim()).filter(Boolean);
        } else if (arg.startsWith('--region=')) {
            options.region = arg.slice('--region='.length).trim();
        } else if (arg.startsWith('--batch-size=')) {
            const value = Number(arg.slice('--batch-size='.length));
            if (Number.isFinite(value) && value > 0) options.batchSize = Math.min(Math.max(Math.floor(value), 1), 300);
        } else if (arg.startsWith('--max-batches=')) {
            options.maxBatches = Number(arg.slice('--max-batches='.length)) || 0;
        } else if (arg.startsWith('--log-every=')) {
            const value = Number(arg.slice('--log-every='.length));
            if (Number.isFinite(value) && value > 0) options.logEvery = Math.floor(value);
        } else if (arg.startsWith('--concurrency=')) {
            const value = Number(arg.slice('--concurrency='.length));
            if (Number.isFinite(value) && value > 0) options.concurrency = Math.min(Math.floor(value), 5);
        } else if (arg.startsWith('--areas=')) {
            options.areas = arg.slice('--areas='.length).split(',').map((value) => value.trim()).filter(Boolean);
        } else if (arg.startsWith('--categories=')) {
            options.contentTypeIds = arg.slice('--categories='.length).split(',').map((value) => value.trim()).filter(Boolean);
        }
    }
    return options;
}

function normalizeRegionKey(value) {
    return String(value || '').toLowerCase().replace(/\s+/g, '');
}

function resolveRegionFilter(value) {
    if (!value) return null;
    const normalized = normalizeRegionKey(value);
    for (const [key, region] of Object.entries(REGION_FILTERS)) {
        const aliases = [key, ...(region.aliases || [])].map(normalizeRegionKey);
        if (aliases.includes(normalized)) return region;
    }
    throw new Error(`Unsupported --region=${value}. Supported regions: busan`);
}

function selectedStageIds(options) {
    if (options.stages.length > 0) return options.stages;
    if (options.stage === 'all') return Object.keys(STAGES);
    if (options.stage.includes(',')) return options.stage.split(',').map((value) => value.trim()).filter(Boolean);
    return [options.stage];
}

function selectedSpec(options, stageId = options.stage) {
    const stage = STAGES[stageId];
    if (!stage && (options.areas.length === 0 || options.contentTypeIds.length === 0)) {
        throw new Error('Use --stage=1|2|3 or pass both --areas and --categories.');
    }
    if (stageId !== 'custom' && !stage) {
        throw new Error(`Unknown stage: ${stageId}`);
    }
    const region = resolveRegionFilter(options.region);
    let areas = options.areas.length ? options.areas : stage.areas;
    let skipReason = '';
    if (region && !options.areas.length && stage) {
        const stageAreas = new Set(stage.areas);
        areas = region.areas.filter((area) => stageAreas.has(area));
        if (areas.length === 0) {
            skipReason = `${region.label} is not included in stage ${stageId} area set.`;
        }
    }
    return {
        stage: stageId,
        label: stage?.label || 'custom',
        areas,
        contentTypeIds: options.contentTypeIds.length ? options.contentTypeIds : stage.contentTypeIds,
        region: region ? region.label : '',
        ldongRegnCodes: region ? region.ldongRegnCodes : [],
        skipReason
    };
}

async function ensureColumn(db, table, column, ddl) {
    const [rows] = await db.query(`SHOW COLUMNS FROM \`${table}\` LIKE ${db.escape(column)}`);
    if (rows.length > 0) return;
    await db.execute(`ALTER TABLE \`${table}\` ADD COLUMN ${ddl}`);
}

async function ensureSchema(db) {
    await ensureColumn(db, 'place', 'overview', '`overview` TEXT NULL');
    await ensureColumn(db, 'place', 'usage_time', '`usage_time` TEXT NULL');
    await ensureColumn(db, 'place', 'rest_date', '`rest_date` TEXT NULL');
    await ensureColumn(db, 'place', 'parking_info', '`parking_info` TEXT NULL');
    await ensureColumn(db, 'place', 'infocenter', "`infocenter` VARCHAR(200) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'detail_intro', '`detail_intro` LONGTEXT NULL');
    await ensureColumn(db, 'place', 'detail_hydrated_at', "`detail_hydrated_at` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'detail_hydrate_error', '`detail_hydrate_error` TEXT NULL');
}

function placeholders(values) {
    return values.map(() => '?').join(', ');
}

function baseWhere(spec) {
    const clauses = [
        "is_hidden = 0",
        "tourapi_id REGEXP '^[0-9]+$'"
    ];
    const params = [];
    if (spec.areas.length > 0) {
        clauses.push(`area IN (${placeholders(spec.areas)})`);
        params.push(...spec.areas);
    }
    if (spec.ldongRegnCodes.length > 0) {
        clauses.push(`ldong_regn_cd IN (${placeholders(spec.ldongRegnCodes)})`);
        params.push(...spec.ldongRegnCodes);
    }
    clauses.push(`content_type_id IN (${placeholders(spec.contentTypeIds)})`);
    params.push(...spec.contentTypeIds);
    return {
        sql: clauses.join('\n              AND '),
        params
    };
}

async function estimate(db, spec, retryFailures) {
    if (spec.skipReason) {
        return {
            rows: [],
            pending: 0
        };
    }
    const where = baseWhere(spec);
    const [rows] = await db.execute(
        `SELECT area, content_type_id, category,
                COUNT(*) AS total,
                SUM(CASE WHEN detail_hydrated_at <> '' THEN 1 ELSE 0 END) AS hydrated,
                SUM(CASE WHEN detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') <> '' THEN 1 ELSE 0 END) AS failed
         FROM \`place\`
         WHERE ${where.sql}
         GROUP BY area, content_type_id, category
         ORDER BY area ASC, CAST(content_type_id AS UNSIGNED) ASC`,
        where.params
    );
    const pendingCondition = retryFailures
        ? "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') <> ''"
        : "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') = ''";
    const [[pending]] = await db.execute(
        `SELECT COUNT(*) AS count
         FROM \`place\`
         WHERE ${where.sql} AND ${pendingCondition}`,
        where.params
    );
    return {
        rows: rows.map((row) => ({
            area: row.area,
            contentTypeId: String(row.content_type_id),
            category: row.category,
            total: Number(row.total || 0),
            hydrated: Number(row.hydrated || 0),
            failed: Number(row.failed || 0)
        })),
        pending: Number(pending?.count || 0)
    };
}

async function selectPending(db, spec, batchSize, retryFailures) {
    if (spec.skipReason) return [];
    const where = baseWhere(spec);
    const pendingCondition = retryFailures
        ? "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') <> ''"
        : "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') = ''";
    const [rows] = await db.execute(
        `SELECT id, tourapi_id, content_type_id, name, area, category, description, phone
         FROM \`place\`
         WHERE ${where.sql} AND ${pendingCondition}
         ORDER BY area ASC, CAST(content_type_id AS UNSIGNED) ASC, name ASC
         LIMIT ${Number(batchSize)}`,
        where.params
    );
    return rows;
}

function writeProgress(payload) {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ ...payload, updatedAt: new Date().toISOString() }, null, 2));
}

function clearProgress() {
    if (fs.existsSync(PROGRESS_FILE)) fs.unlinkSync(PROGRESS_FILE);
}

function appendFailure(row, error) {
    const payload = {
        contentId: String(row.tourapi_id),
        placeId: row.id,
        area: row.area,
        contentTypeId: String(row.content_type_id),
        name: row.name,
        message: error.message,
        failedAt: new Date().toISOString()
    };
    fs.appendFileSync(FAILURE_LOG_FILE, `${JSON.stringify(payload)}\n`);
}

async function markFailure(db, row, error) {
    const message = String(error.message || error).slice(0, 1000);
    await db.execute(
        'UPDATE `place` SET detail_hydrate_error = ?, updated = ? WHERE id = ?',
        [message, nowSql(), row.id]
    );
    appendFailure(row, error);
}

async function hydratePlace(db, client, row) {
    const contentId = String(row.tourapi_id);
    const contentTypeId = String(row.content_type_id);
    const detail = firstItem(await client.detailCommon(contentId, { numOfRows: 1, pageNo: 1 })) || {};
    const intro = firstItem(await client.detailIntro(contentId, contentTypeId, { numOfRows: 1, pageNo: 1 })) || {};
    const overview = cleanText(detail.overview);
    const usageTime = usageTimeFor(intro);
    const restDate = firstText(intro, REST_DATE_FIELDS);
    const parkingInfo = firstText(intro, PARKING_FIELDS);
    const infocenter = limitText(firstText(intro, INFOCENTER_FIELDS), 200);
    const phone = limitText(detail.tel || row.phone || infocenter, 80);
    const description = overview || row.description || '';
    const now = nowSql();

    await db.execute(
        `UPDATE \`place\`
         SET overview = ?,
             description = ?,
             phone = ?,
             usage_time = ?,
             rest_date = ?,
             parking_info = ?,
             infocenter = ?,
             detail_intro = ?,
             detail_hydrated_at = ?,
             detail_hydrate_error = '',
             updated = ?
         WHERE id = ?`,
        [
            overview,
            description,
            phone,
            usageTime,
            restDate,
            parkingInfo,
            infocenter,
            JSON.stringify(intro),
            now,
            now,
            row.id
        ]
    );
    await sleep(requestDelayMs());
    return { overview, usageTime, restDate };
}

async function runStage(db, client, spec, options) {
    const summary = {
        stage: spec.stage,
        label: spec.label,
        region: spec.region,
        areas: spec.areas,
        ldongRegnCodes: spec.ldongRegnCodes,
        contentTypeIds: spec.contentTypeIds,
        batchSize: options.batchSize,
        concurrency: options.concurrency,
        callsPerPlace: 2,
        processed: 0,
        succeeded: 0,
        failed: 0,
        batches: 0,
        failureLogFile: FAILURE_LOG_FILE
    };

    if (spec.skipReason) {
        summary.skipReason = spec.skipReason;
        summary.estimate = {
            pendingPlaces: 0,
            expectedApiCalls: 0,
            byCombination: []
        };
        summary.after = summary.estimate;
        console.log(JSON.stringify({ stage: spec.stage, skipped: spec.skipReason, estimate: summary.estimate }, null, 2));
        return summary;
    }

    const before = await estimate(db, spec, options.retryFailures);
    summary.estimate = {
        pendingPlaces: before.pending,
        expectedApiCalls: before.pending * 2,
        byCombination: before.rows
    };
    console.log(JSON.stringify({ stage: spec.stage, estimate: summary.estimate }, null, 2));
    if (options.estimateOnly || before.pending === 0) {
        summary.after = await estimate(db, spec, true);
        return summary;
    }

    let consecutiveFailures = 0;
    while (true) {
        if (options.maxBatches > 0 && summary.batches >= options.maxBatches) break;
        const rows = await selectPending(db, spec, options.batchSize, options.retryFailures);
        if (rows.length === 0) break;
        summary.batches += 1;
        writeProgress({
            stage: spec.stage,
            batch: summary.batches,
            batchSize: options.batchSize,
            remainingBeforeBatch: rows.length,
            areas: spec.areas,
            ldongRegnCodes: spec.ldongRegnCodes,
            contentTypeIds: spec.contentTypeIds
        });
        console.log(`batch ${summary.batches}: ${rows.length} places`);

        let cursor = 0;
        let stopError = null;
        const processRow = async (row) => {
            try {
                await hydratePlace(db, client, row);
                summary.processed += 1;
                summary.succeeded += 1;
                consecutiveFailures = 0;
                if (summary.processed % options.logEvery === 0) {
                    writeProgress({
                        stage: spec.stage,
                        batch: summary.batches,
                        processed: summary.processed,
                        succeeded: summary.succeeded,
                        failed: summary.failed,
                        lastContentId: String(row.tourapi_id),
                        areas: spec.areas,
                        ldongRegnCodes: spec.ldongRegnCodes,
                        contentTypeIds: spec.contentTypeIds
                    });
                    console.log(`progress: processed=${summary.processed}, succeeded=${summary.succeeded}, failed=${summary.failed}, last=${row.tourapi_id}`);
                }
            } catch (error) {
                summary.processed += 1;
                summary.failed += 1;
                consecutiveFailures += 1;
                await markFailure(db, row, error);
                console.error(`failed ${row.tourapi_id} ${row.name}: ${error.message}`);
                if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
                    stopError = new Error(`Stopped after ${MAX_CONSECUTIVE_FAILURES} consecutive failures. Last error: ${error.message}`);
                }
            }
        };
        const workers = Array.from({ length: Math.min(options.concurrency, rows.length) }, async () => {
            while (!stopError && cursor < rows.length) {
                const row = rows[cursor];
                cursor += 1;
                await processRow(row);
            }
        });
        await Promise.all(workers);
        if (stopError) throw stopError;

        const afterBatch = await estimate(db, spec, options.retryFailures);
        console.log(`batch ${summary.batches} done: succeeded=${summary.succeeded}, failed=${summary.failed}, pending=${afterBatch.pending}`);
        if (afterBatch.pending === 0) break;
        await sleep(BATCH_DELAY_MS);
    }

    summary.after = await estimate(db, spec, true);
    if (!options.maxBatches || summary.after.pending === 0) clearProgress();
    return summary;
}

function aggregateSummaries(stages) {
    return stages.reduce((total, stage) => {
        total.pendingPlaces += Number(stage.estimate?.pendingPlaces || 0);
        total.expectedApiCalls += Number(stage.estimate?.expectedApiCalls || 0);
        total.processed += Number(stage.processed || 0);
        total.succeeded += Number(stage.succeeded || 0);
        total.failed += Number(stage.failed || 0);
        return total;
    }, {
        pendingPlaces: 0,
        expectedApiCalls: 0,
        processed: 0,
        succeeded: 0,
        failed: 0
    });
}

async function run() {
    const options = parseArgs(process.argv.slice(2));
    const stageIds = selectedStageIds(options);
    const specs = stageIds.map((stageId) => selectedSpec(options, stageId));
    if (options.resetProgress && fs.existsSync(PROGRESS_FILE)) fs.unlinkSync(PROGRESS_FILE);

    const client = new TourApiClient();
    if (!client.serviceKey) {
        throw new Error(`TOUR_API_KEY is required. cwd=${process.cwd()}, checked=${client.loadedEnvFiles.join(',') || 'no env files loaded'}`);
    }

    const db = await connect();
    try {
        await ensureSchema(db);
        const summaries = [];
        for (const spec of specs) {
            summaries.push(await runStage(db, client, spec, options));
        }
        if (summaries.length === 1) return summaries[0];
        return {
            mode: 'multi-stage',
            region: specs.find((spec) => spec.region)?.region || '',
            stages: summaries,
            total: aggregateSummaries(summaries)
        };
    } finally {
        await db.end();
    }
}

run()
    .then((summary) => {
        console.log(JSON.stringify(summary, null, 2));
    })
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
