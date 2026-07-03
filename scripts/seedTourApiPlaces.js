const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { connect } = require('./db');
const { TourApiClient } = require('../services/tourApiClient');

const CONTENT_TYPE_CATEGORY = {
    12: '관광지',
    14: '문화시설',
    15: '축제공연행사',
    25: '여행코스',
    28: '레포츠',
    32: '숙박',
    38: '쇼핑',
    39: '음식점'
};

const CONTENT_TYPE_TARGETS = Object.entries(CONTENT_TYPE_CATEGORY).map(([contentTypeId, label]) => ({
    contentTypeId,
    label
}));

const REGION_TARGETS = [
    { name: '서울', lDongRegnCd: '11' },
    { name: '부산', lDongRegnCd: '26' },
    { name: '제주', lDongRegnCd: '50' },
    { name: '강원 강릉', lDongRegnCd: '51', lDongSignguCd: '150' },
    { name: '강원 속초', lDongRegnCd: '51', lDongSignguCd: '210' },
    { name: '전북 전주', lDongRegnCd: '52', lDongSignguCd: '111' },
    { name: '전북 전주', lDongRegnCd: '52', lDongSignguCd: '113' },
    { name: '전남 여수', lDongRegnCd: '12', lDongSignguCd: '130' },
    { name: '경북 경주', lDongRegnCd: '47', lDongSignguCd: '130' },
    { name: '대전', lDongRegnCd: '30' },
    { name: '인천', lDongRegnCd: '28' },
    { name: '경기 가평', lDongRegnCd: '41', lDongSignguCd: '820' }
];

const PAGE_SIZE = 50;
const MIN_REQUEST_DELAY_MS = 100;
const MAX_REQUEST_DELAY_MS = 200;
const PROGRESS_FILE = path.join(__dirname, '.seedTourApiPlaces.progress.json');

const DEFAULT_IMAGES = {
    카페: 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=640&q=80',
    바다: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=640&q=80',
    숙박: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=640&q=80',
    관광지: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=640&q=80'
};

function nowSql() {
    const date = new Date();
    const pad = (value) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function id() {
    return crypto.randomBytes(16).toString('hex');
}

function cleanText(value) {
    return String(value || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function firstItem(result) {
    return result.items && result.items.length ? result.items[0] : null;
}

function categoryFor(item) {
    return CONTENT_TYPE_CATEGORY[Number(item.contenttypeid)] || '관광지';
}

function fallbackImage(category) {
    return DEFAULT_IMAGES[category] || DEFAULT_IMAGES['관광지'];
}

async function ensureColumn(db, table, column, ddl) {
    const [rows] = await db.query(`SHOW COLUMNS FROM \`${table}\` LIKE ${db.escape(column)}`);
    if (rows.length > 0) return;
    await db.execute(`ALTER TABLE \`${table}\` ADD COLUMN ${ddl}`);
}

async function ensureSchema(db) {
    await ensureColumn(db, 'place', 'first_image2', "`first_image2` VARCHAR(500) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'zipcode', "`zipcode` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'cpyrht_div_cd', "`cpyrht_div_cd` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'ldong_regn_cd', "`ldong_regn_cd` VARCHAR(10) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'ldong_signgu_cd', "`ldong_signgu_cd` VARCHAR(10) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'lcls_systm1', "`lcls_systm1` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'lcls_systm2', "`lcls_systm2` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'lcls_systm3', "`lcls_systm3` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'tourapi_created_time', "`tourapi_created_time` VARCHAR(20) NOT NULL DEFAULT ''");
    await ensureColumn(db, 'place', 'tourapi_modified_time', "`tourapi_modified_time` VARCHAR(20) NOT NULL DEFAULT ''");
}

async function markDummyRows(db) {
    await db.execute(
        `UPDATE \`place\`
         SET is_hidden = 1,
             description = CASE
                 WHEN description LIKE '[더미]%' THEN description
                 ELSE CONCAT('[더미] ', description)
             END,
             updated = NOW()
         WHERE tourapi_id LIKE 'TOUR-%' OR tourapi_id LIKE 'DUMMY-%'`
    );
    await db.execute(
        `UPDATE course
         SET is_featured = 0,
             is_hidden = 1,
             tags = '[\"더미\"]',
             updated = NOW()
         WHERE title LIKE '검증용 인기 코스%'`
    );
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function requestDelayMs() {
    const span = MAX_REQUEST_DELAY_MS - MIN_REQUEST_DELAY_MS;
    return MIN_REQUEST_DELAY_MS + Math.floor(Math.random() * (span + 1));
}

async function requestWithDelay(operation) {
    const result = await operation();
    await sleep(requestDelayMs());
    return result;
}

function parseArgs(argv) {
    const options = {
        resetProgress: false,
        hydrateDetails: false,
        regionLimit: 0,
        regionNames: [],
        contentTypeIds: []
    };
    for (const arg of argv) {
        if (arg === '--reset-progress') {
            options.resetProgress = true;
        } else if (arg === '--hydrate-details') {
            options.hydrateDetails = true;
        } else if (arg.startsWith('--region-limit=')) {
            options.regionLimit = Number(arg.slice('--region-limit='.length)) || 0;
        } else if (arg.startsWith('--regions=')) {
            options.regionNames = arg.slice('--regions='.length).split(',').map((value) => value.trim()).filter(Boolean);
        } else if (arg.startsWith('--categories=')) {
            options.contentTypeIds = arg.slice('--categories='.length).split(',').map((value) => value.trim()).filter(Boolean);
        }
    }
    return options;
}

function normalizeRegionName(value) {
    return String(value || '').replace(/\s+/g, '');
}

function selectRegions(options) {
    let regions = REGION_TARGETS;
    if (options.regionNames.length > 0) {
        const selected = new Set(options.regionNames.map(normalizeRegionName));
        regions = regions.filter((region) => {
            const name = normalizeRegionName(region.name);
            const group = normalizeRegionName(region.name.split(' ')[0]);
            return selected.has(name) || selected.has(group);
        });
    }
    if (options.regionLimit > 0) {
        regions = regions.slice(0, options.regionLimit);
    }
    return regions;
}

function selectContentTypes(options) {
    if (options.contentTypeIds.length === 0) return CONTENT_TYPE_TARGETS;
    const selected = new Set(options.contentTypeIds.map(String));
    return CONTENT_TYPE_TARGETS.filter((target) => selected.has(String(target.contentTypeId)));
}

function regionCode(region) {
    return `${region.lDongRegnCd}:${region.lDongSignguCd || '*'}`;
}

function jobKey(region, contentType) {
    return `${regionCode(region)}:${contentType.contentTypeId}`;
}

function makeJobs(regions, contentTypes) {
    const jobs = [];
    for (const region of regions) {
        for (const contentType of contentTypes) {
            jobs.push({
                key: jobKey(region, contentType),
                region,
                contentType
            });
        }
    }
    return jobs;
}

function runIdFor(jobs) {
    const source = jobs.map((job) => job.key).join('|');
    return crypto.createHash('sha1').update(source).digest('hex').slice(0, 16);
}

function readProgress(runId, resetProgress) {
    if (resetProgress && fs.existsSync(PROGRESS_FILE)) {
        fs.unlinkSync(PROGRESS_FILE);
    }
    if (!fs.existsSync(PROGRESS_FILE)) return null;
    try {
        const progress = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
        if (progress.runId !== runId) return null;
        return progress;
    } catch (error) {
        return null;
    }
}

function writeProgress(progress) {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({
        ...progress,
        updatedAt: new Date().toISOString()
    }, null, 2));
}

function clearProgress() {
    if (fs.existsSync(PROGRESS_FILE)) {
        fs.unlinkSync(PROGRESS_FILE);
    }
}

function totalCountOf(result) {
    const value = result?.json?.response?.body?.totalCount;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : result.items.length;
}

function emptyCombinationSummary(region, contentType) {
    return {
        region: region.name,
        category: contentType.label,
        contentTypeId: String(contentType.contentTypeId),
        fetched: 0,
        processed: 0,
        inserted: 0,
        updated: 0,
        skipped: 0
    };
}

function normalizeAreaItem(item) {
    const category = categoryFor(item);
    return {
        ...item,
        image: item.firstimage || item.firstimage2 || fallbackImage(category),
        first_image2: item.firstimage2 || '',
        category,
        description: cleanText(item.overview || item.title || ''),
        address: cleanText(`${item.addr1 || ''} ${item.addr2 || ''}`),
        area: ''
    };
}

async function hydrateItem(client, item) {
    let detail = null;
    try {
        detail = firstItem(await requestWithDelay(() => client.detailCommon(item.contentid, { numOfRows: 1, pageNo: 1 })));
    } catch (error) {
        detail = null;
    }
    const merged = { ...item, ...(detail || {}) };
    let image = merged.firstimage || merged.firstimage2 || '';
    let firstImage2 = merged.firstimage2 || '';
    if (!image) {
        try {
            const imageDetail = firstItem(await requestWithDelay(() => client.detailImage(item.contentid, { numOfRows: 5, pageNo: 1 })));
            image = imageDetail?.originimgurl || imageDetail?.smallimageurl || '';
            firstImage2 = imageDetail?.smallimageurl || firstImage2;
            if (!merged.cpyrhtDivCd && imageDetail?.cpyrhtDivCd) merged.cpyrhtDivCd = imageDetail.cpyrhtDivCd;
        } catch (error) {
            // Keep category fallback below.
        }
    }
    const category = categoryFor(merged);
    return {
        ...merged,
        image: image || fallbackImage(category),
        first_image2: firstImage2,
        category,
        description: cleanText(merged.overview || merged.title || ''),
        address: cleanText(`${merged.addr1 || ''} ${merged.addr2 || ''}`),
        area: ''
    };
}

async function prepareItem(client, item, hydrateDetails) {
    if (hydrateDetails) return hydrateItem(client, item);
    return normalizeAreaItem(item);
}

async function upsertPlace(db, item, region) {
    const now = nowSql();
    const [[existing]] = await db.execute('SELECT id FROM `place` WHERE tourapi_id = ? LIMIT 1', [String(item.contentid)]);
    const placeId = existing?.id || id();
    const payload = [
        String(item.contentid || ''),
        String(item.contenttypeid || ''),
        cleanText(item.title),
        item.category,
        item.description,
        item.image,
        item.first_image2 || '',
        item.address,
        region || '',
        cleanText(item.tel || ''),
        String(item.mapy || ''),
        String(item.mapx || ''),
        String(item.zipcode || ''),
        String(item.cpyrhtDivCd || ''),
        String(item.lDongRegnCd || ''),
        String(item.lDongSignguCd || ''),
        String(item.lclsSystm1 || ''),
        String(item.lclsSystm2 || ''),
        String(item.lclsSystm3 || ''),
        String(item.createdtime || ''),
        String(item.modifiedtime || ''),
        0,
        now
    ];

    if (existing) {
        await db.execute(
            `UPDATE \`place\`
             SET tourapi_id = ?, content_type_id = ?, name = ?, category = ?, description = ?,
                 image = ?, first_image2 = ?, address = ?, area = ?, phone = ?, latitude = ?, longitude = ?,
                 zipcode = ?, cpyrht_div_cd = ?, ldong_regn_cd = ?, ldong_signgu_cd = ?,
                 lcls_systm1 = ?, lcls_systm2 = ?, lcls_systm3 = ?,
                 tourapi_created_time = ?, tourapi_modified_time = ?, is_hidden = ?, updated = ?
             WHERE id = ?`,
            [...payload, placeId]
        );
    } else {
        await db.execute(
            `INSERT INTO \`place\` (
                id, tourapi_id, content_type_id, name, category, description,
                image, first_image2, address, area, phone, latitude, longitude,
                zipcode, cpyrht_div_cd, ldong_regn_cd, ldong_signgu_cd,
                lcls_systm1, lcls_systm2, lcls_systm3,
                tourapi_created_time, tourapi_modified_time, is_hidden, created, updated
             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [placeId, ...payload, now]
        );
    }
    return { placeId, action: existing ? 'updated' : 'inserted' };
}

async function fetchAreaPage(client, region, contentType, pageNo) {
    return requestWithDelay(() => client.areaBasedList({
        numOfRows: PAGE_SIZE,
        pageNo,
        arrange: 'Q',
        contentTypeId: String(contentType.contentTypeId),
        lDongRegnCd: region.lDongRegnCd,
        lDongSignguCd: region.lDongSignguCd || ''
    }));
}

async function loadPlaceCounts(db) {
    const [rows] = await db.execute(
        `SELECT area, content_type_id, category, COUNT(*) AS count
         FROM \`place\`
         WHERE is_hidden = 0
         GROUP BY area, content_type_id, category
         ORDER BY area ASC, CAST(content_type_id AS UNSIGNED) ASC, category ASC`
    );
    const [[visible]] = await db.execute('SELECT COUNT(*) AS count FROM `place` WHERE is_hidden = 0');
    return {
        visiblePlaces: Number(visible?.count || 0),
        areaCategoryCounts: rows.map((row) => ({
            area: row.area || '(지역 없음)',
            contentTypeId: String(row.content_type_id || ''),
            category: row.category || '',
            count: Number(row.count || 0)
        }))
    };
}

function logCombination(prefix, combo) {
    console.log(`${prefix} ${combo.region} / ${combo.category}: fetched=${combo.fetched}, processed=${combo.processed}, inserted=${combo.inserted}, updated=${combo.updated}, skipped=${combo.skipped}`);
}

async function processJob(db, client, job, jobIndex, totalJobs, startPageNo, runId, options) {
    const { region, contentType } = job;
    const combo = emptyCombinationSummary(region, contentType);
    let pageNo = startPageNo;

    while (true) {
        writeProgress({
            runId,
            jobKey: job.key,
            region: region.name,
            contentTypeId: String(contentType.contentTypeId),
            pageNo
        });

        const result = await fetchAreaPage(client, region, contentType, pageNo);
        const totalCount = totalCountOf(result);
        combo.fetched += result.items.length;
        console.log(`[${jobIndex + 1}/${totalJobs}] ${region.name} / ${contentType.label} page=${pageNo} rows=${result.items.length} total=${totalCount}`);

        for (const item of result.items) {
            if (!item.contentid) {
                combo.skipped += 1;
                continue;
            }
            const prepared = await prepareItem(client, item, options.hydrateDetails);
            const { action } = await upsertPlace(db, prepared, region.name);
            combo.processed += 1;
            combo[action] += 1;
        }

        writeProgress({
            runId,
            jobKey: job.key,
            region: region.name,
            contentTypeId: String(contentType.contentTypeId),
            pageNo: pageNo + 1,
            lastCompletedPage: pageNo
        });

        if (result.items.length === 0 || pageNo * PAGE_SIZE >= totalCount) break;
        pageNo += 1;
    }

    logCombination('done', combo);
    return combo;
}

async function main() {
    const options = parseArgs(process.argv.slice(2));
    const regions = selectRegions(options);
    const contentTypes = selectContentTypes(options);
    const jobs = makeJobs(regions, contentTypes);
    if (jobs.length === 0) {
        throw new Error('No seed jobs selected. Check --regions or --categories values.');
    }

    const client = new TourApiClient();
    if (!client.serviceKey) {
        throw new Error(`TOUR_API_KEY is required. cwd=${process.cwd()}, checked=${client.loadedEnvFiles.join(',') || 'no env files loaded'}`);
    }

    const runId = runIdFor(jobs);
    const progress = readProgress(runId, options.resetProgress);
    let startJobIndex = 0;
    let startPageNo = 1;
    if (progress) {
        const progressJobIndex = jobs.findIndex((job) => job.key === progress.jobKey);
        if (progressJobIndex >= 0) {
            startJobIndex = progressJobIndex;
            startPageNo = Number(progress.pageNo || 1) || 1;
            console.log(`resume run=${runId} job=${progress.region}/${progress.contentTypeId} page=${startPageNo}`);
        }
    }

    const db = await connect();
    const summary = {
        runId,
        progressFile: PROGRESS_FILE,
        pageSize: PAGE_SIZE,
        hydrateDetails: options.hydrateDetails,
        regions: regions.map((region) => region.name),
        categories: contentTypes.map((contentType) => `${contentType.contentTypeId}:${contentType.label}`),
        fetched: 0,
        processed: 0,
        inserted: 0,
        updated: 0,
        skipped: 0,
        combinations: []
    };
    try {
        await ensureSchema(db);
        await markDummyRows(db);

        console.log(`seed jobs=${jobs.length}, regions=${regions.length}, categories=${contentTypes.length}, pageSize=${PAGE_SIZE}, hydrateDetails=${options.hydrateDetails}`);
        for (let index = startJobIndex; index < jobs.length; index += 1) {
            const combo = await processJob(db, client, jobs[index], index, jobs.length, index === startJobIndex ? startPageNo : 1, runId, options);
            summary.fetched += combo.fetched;
            summary.processed += combo.processed;
            summary.inserted += combo.inserted;
            summary.updated += combo.updated;
            summary.skipped += combo.skipped;
            summary.combinations.push(combo);

            const nextJob = jobs[index + 1];
            if (nextJob) {
                writeProgress({
                    runId,
                    jobKey: nextJob.key,
                    region: nextJob.region.name,
                    contentTypeId: String(nextJob.contentType.contentTypeId),
                    pageNo: 1,
                    lastCompletedJobKey: jobs[index].key
                });
            }
        }
        clearProgress();
        summary.counts = await loadPlaceCounts(db);
    } finally {
        await db.end();
    }
    console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
