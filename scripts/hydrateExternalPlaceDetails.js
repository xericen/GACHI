const fs = require('node:fs');
const path = require('node:path');
const { connect, sqlDate } = require('./db');

const DEFAULT_BATCH_SIZE = 200;
const DEFAULT_CONCURRENCY = 2;
const DEFAULT_LOG_EVERY = 25;
const MIN_DELAY_MS = 150;
const MAX_DELAY_MS = 250;
const BATCH_DELAY_MS = 2000;
const REQUEST_TIMEOUT_MS = 12000;
const MAX_RESPONSE_BYTES = 8 * 1024 * 1024;
const PROGRESS_FILE = path.join(__dirname, '.hydrateExternalPlaceDetails.progress.json');
const FAILURE_LOG_FILE = path.join(__dirname, 'hydrateExternalPlaceDetails.failures.jsonl');
const GENERIC_DESCRIPTIONS = new Set([
    '',
    'Google Places에서 확인한 실제 장소'
]);

function projectEnvValue(name) {
    if (process.env[name]) return process.env[name];
    const envPath = path.join(__dirname, '..', '.env');
    if (!fs.existsSync(envPath)) return '';
    const match = fs.readFileSync(envPath, 'utf8').match(new RegExp(`^${name}=(.*)$`, 'm'));
    return match ? match[1].trim().replace(/^['"]|['"]$/g, '') : '';
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function requestDelayMs() {
    return MIN_DELAY_MS + Math.floor(Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS + 1));
}

function cleanText(value) {
    return String(value || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/gi, ' ')
        .replace(/&amp;/gi, '&')
        .replace(/\s+/g, ' ')
        .trim();
}

function limitText(value, maxLength) {
    const text = cleanText(value);
    return text.length > maxLength ? text.slice(0, maxLength) : text;
}

function normalizeName(value) {
    return cleanText(value).replace(/[^0-9a-zA-Z가-힣]/g, '').toLowerCase();
}

function nameSimilarity(left, right) {
    const first = normalizeName(left);
    const second = normalizeName(right);
    if (!first || !second) return 0;
    if (first === second) return 1;
    const grams = (value) => {
        if (value.length < 2) return [value];
        return Array.from({ length: value.length - 1 }, (_, index) => value.slice(index, index + 2));
    };
    const remaining = grams(second);
    let matches = 0;
    for (const gram of grams(first)) {
        const index = remaining.indexOf(gram);
        if (index < 0) continue;
        matches += 1;
        remaining.splice(index, 1);
    }
    return (2 * matches) / (grams(first).length + grams(second).length);
}

function numberInRange(value, min, max) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return null;
    if (parsed >= min && parsed <= max) return parsed;
    for (const divisor of [1e7, 1e6, 1e5]) {
        const normalized = parsed / divisor;
        if (normalized >= min && normalized <= max) return normalized;
    }
    return null;
}

function haversineKm(lat1, lng1, lat2, lng2) {
    if ([lat1, lng1, lat2, lng2].some((value) => value === null)) return null;
    const toRadians = (value) => value * Math.PI / 180;
    const radius = 6371.0088;
    const deltaLat = toRadians(lat2 - lat1);
    const deltaLng = toRadians(lng2 - lng1);
    const value = Math.sin(deltaLat / 2) ** 2
        + Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(deltaLng / 2) ** 2;
    return radius * 2 * Math.atan2(Math.sqrt(value), Math.sqrt(Math.max(0, 1 - value)));
}

function parseJsonAt(source, start) {
    if (start < 0 || !['{', '['].includes(source[start])) return null;
    const pairs = { '{': '}', '[': ']' };
    const stack = [];
    let inString = false;
    let escaped = false;
    for (let index = start; index < source.length; index += 1) {
        const character = source[index];
        if (inString) {
            if (escaped) escaped = false;
            else if (character === '\\') escaped = true;
            else if (character === '"') inString = false;
            continue;
        }
        if (character === '"') {
            inString = true;
        } else if (pairs[character]) {
            stack.push(pairs[character]);
        } else if (stack.length && character === stack[stack.length - 1]) {
            stack.pop();
            if (stack.length === 0) {
                try {
                    return JSON.parse(source.slice(start, index + 1));
                } catch {
                    return null;
                }
            }
        }
    }
    return null;
}

function entities(source, prefix) {
    const results = [];
    const marker = `"${prefix}`;
    let cursor = 0;
    while (cursor < source.length) {
        const markerIndex = source.indexOf(marker, cursor);
        if (markerIndex < 0) break;
        const idStart = markerIndex + marker.length;
        const idEnd = source.indexOf('":', idStart);
        if (idEnd < 0) break;
        const objectStart = source.indexOf('{', idEnd + 2);
        if (objectStart < 0) break;
        const payload = parseJsonAt(source, objectStart);
        if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
            results.push([source.slice(idStart, idEnd), payload]);
        }
        cursor = objectStart + 1;
    }
    return results;
}

function candidateFromPayload(placeId, payload, sourceType) {
    const coordinate = payload.coordinate && typeof payload.coordinate === 'object'
        ? payload.coordinate
        : payload;
    return {
        placeId: String(payload.id || placeId || ''),
        sourceType,
        name: cleanText(payload.normalizedName || payload.name),
        category: cleanText(payload.category),
        roadAddress: cleanText(payload.roadAddress),
        address: cleanText(payload.fullAddress || payload.address || payload.commonAddress),
        phone: limitText(payload.phone || payload.virtualPhone, 80),
        lat: numberInRange(coordinate.y, 30, 44),
        lng: numberInRange(coordinate.x, 120, 135),
        image: cleanText(payload.imageUrl),
        conveniences: Array.isArray(payload.conveniences) ? payload.conveniences.map(cleanText).filter(Boolean) : [],
        microReviews: Array.isArray(payload.microReviews) ? payload.microReviews.map(cleanText).filter(Boolean) : [],
        visitorReviewsTotal: Number(payload.visitorReviewsTotal || 0) || 0,
        visitorReviewsScore: Number(payload.visitorReviewsScore) || null,
        cafeBlogReviewsTotal: Number(payload.cafeBlogReviewsTotal || 0) || 0,
        openingHours: payload.openingHours || null
    };
}

function candidatesFromSource(source) {
    const byId = new Map();
    for (const [id, payload] of entities(source, 'PlaceListBusinessesItem:')) {
        const candidate = candidateFromPayload(id, payload, 'list');
        if (candidate.name) byId.set(candidate.placeId, candidate);
    }
    for (const [id, payload] of entities(source, 'PlaceDetailBase:')) {
        const candidate = candidateFromPayload(id, payload, 'detail');
        if (!candidate.name) continue;
        byId.set(candidate.placeId, { ...(byId.get(candidate.placeId) || {}), ...candidate });
    }
    return [...byId.values()];
}

function scoreCandidate(row, candidate) {
    const target = normalizeName(row.name);
    const name = normalizeName(candidate.name);
    if (!target || !name) return null;
    const sourceLat = numberInRange(row.latitude, 30, 44);
    const sourceLng = numberInRange(row.longitude, 120, 135);
    const distanceKm = haversineKm(sourceLat, sourceLng, candidate.lat, candidate.lng);
    if (distanceKm !== null && distanceKm > 30) return null;
    const similarity = nameSimilarity(target, name);
    let nameScore;
    if (target === name) nameScore = 0;
    else if (target.includes(name) || name.includes(target)) nameScore = 12;
    else if (distanceKm !== null && distanceKm <= 1 && similarity >= 0.45) nameScore = 20 + (1 - similarity) * 10;
    else if (distanceKm !== null && distanceKm <= 0.15 && similarity >= 0.25) nameScore = 28 + (1 - similarity) * 10;
    else return null;

    const distanceScore = distanceKm === null ? 20 : Math.min(20, distanceKm);
    const detailBonus = candidate.sourceType === 'detail' ? -2 : 0;
    return { score: nameScore + distanceScore + detailBonus, distanceKm, similarity };
}

function selectCandidate(row, source) {
    const ranked = candidatesFromSource(source)
        .map((candidate) => ({ candidate, rank: scoreCandidate(row, candidate) }))
        .filter((entry) => entry.rank !== null)
        .sort((left, right) => left.rank.score - right.rank.score);
    if (!ranked.length) return null;
    return {
        ...ranked[0].candidate,
        distanceKm: ranked[0].rank.distanceKm,
        nameSimilarity: ranked[0].rank.similarity
    };
}

function businessHoursFromSource(source) {
    const marker = 'newBusinessHours(';
    const markerIndex = source.indexOf(marker);
    if (markerIndex < 0) return [];
    const arrayStart = source.indexOf('[', source.indexOf(':', markerIndex));
    const payload = parseJsonAt(source, arrayStart);
    return Array.isArray(payload) ? payload : [];
}

function businessImageFromSource(source, targetName) {
    const target = normalizeName(targetName);
    const photos = entities(source, 'PlaceDetailTopPhotoItem:')
        .map(([, payload]) => payload)
        .filter((payload) => payload.mediaSource === 'business' && normalizeName(payload.title) === target);
    return cleanText(photos[0]?.originalUrl || photos[0]?.thumbnailUrl);
}

function trustedBusinessImage(value) {
    const image = cleanText(value);
    if (!image) return '';
    try {
        const host = new URL(image).hostname.toLowerCase();
        return host === 'ldb-phinf.pstatic.net' ? image : '';
    } catch {
        return '';
    }
}

function menusFromSource(source, placeId) {
    const menus = [];
    const seen = new Set();
    for (const [entityId, payload] of entities(source, 'Menu:')) {
        if (placeId && !entityId.startsWith(`${placeId}_`)) continue;
        const name = cleanText(payload.name);
        const key = normalizeName(name);
        if (!key || seen.has(key)) continue;
        seen.add(key);
        const images = Array.isArray(payload.images) ? payload.images : [];
        menus.push({
            name,
            price: cleanText(payload.price),
            description: cleanText(payload.description),
            image: cleanText(images[0]),
            recommended: Boolean(payload.recommend)
        });
        if (menus.length >= 30) break;
    }
    return menus;
}

function formatBusinessHours(groups) {
    const group = groups.find((item) => Array.isArray(item?.businessHours)) || null;
    if (!group) return { usageTime: '', restDate: '' };
    const usageTime = group.businessHours.map((item) => {
        const day = cleanText(item.day);
        const hours = item.businessHours || {};
        if (!day || !hours.start || !hours.end) return '';
        const breakHours = item.breakHours || {};
        const breakText = breakHours.start && breakHours.end
            ? ` (휴게 ${breakHours.start}-${breakHours.end})`
            : '';
        return `${day} ${hours.start}-${hours.end}${breakText}`;
    }).filter(Boolean).join(' / ');
    const closed = [];
    if (group.comingRegularClosedDays) closed.push(cleanText(group.comingRegularClosedDays));
    if (Array.isArray(group.comingIrregularClosedDays)) {
        closed.push(...group.comingIrregularClosedDays.map((item) => cleanText(item.date || item.description || item)));
    }
    if (group.freeText) closed.push(cleanText(group.freeText));
    return {
        usageTime: limitText(usageTime, 2000),
        restDate: limitText(closed.filter(Boolean).join(' / '), 1000)
    };
}

function regionHint(row) {
    const source = `${row.address || ''} ${row.area || ''}`;
    const region = source.match(/(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(?:특별자치도|특별자치시|광역시|특별시|도)?/);
    const district = source.match(/[가-힣]+(?:시|군|구)/);
    return [region?.[1] || '', district?.[0] || ''].filter(Boolean).join(' ') || cleanText(row.area);
}

function nameVariants(value) {
    const source = cleanText(value);
    const koreanOnly = cleanText((source.match(/[0-9가-힣][0-9가-힣 .·&'-]*/g) || []).join(' '));
    const withoutParentheses = cleanText(source.replace(/\([^)]*\)/g, ' ').replace(/（[^）]*）/g, ' '));
    const firstSegment = cleanText(withoutParentheses.split(/[|ㅣ/]/)[0]);
    const parentheticalKorean = (source.match(/\(([^)]*[가-힣][^)]*)\)/g) || [])
        .map((item) => cleanText(item.slice(1, -1)))
        .filter(Boolean);
    return [...new Set([firstSegment, koreanOnly, ...parentheticalKorean, source].filter((item) => item.length >= 2))];
}

function searchQueries(row) {
    const hint = regionHint(row);
    const queries = [];
    for (const name of nameVariants(row.name)) {
        if (hint) queries.push(`${name} ${hint}`);
        queries.push(name);
    }
    return [...new Set(queries.map(cleanText).filter((value) => value.length >= 2))].slice(0, 6);
}

async function fetchSearch(query) {
    let lastError = null;
    for (let attempt = 1; attempt <= 3; attempt += 1) {
        try {
            const response = await fetch(`https://search.naver.com/search.naver?query=${encodeURIComponent(query)}`, {
                headers: {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept-Language': 'ko-KR,ko;q=0.9'
                },
                signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS)
            });
            if (!response.ok) {
                const error = new Error(`NAVER search HTTP ${response.status}`);
                error.status = response.status;
                throw error;
            }
            const source = await response.text();
            if (Buffer.byteLength(source) > MAX_RESPONSE_BYTES) {
                throw new Error(`NAVER search response exceeds ${MAX_RESPONSE_BYTES} bytes`);
            }
            await sleep(requestDelayMs());
            return source;
        } catch (error) {
            lastError = error;
            if (attempt < 3) {
                const cooldown = [403, 429].includes(error.status) ? 5000 * attempt : 500 * attempt;
                await sleep(cooldown);
            }
        }
    }
    throw lastError || new Error('NAVER search request failed');
}

function overviewFor(row, candidate) {
    if (candidate.microReviews.length) return limitText(candidate.microReviews.join(' · '), 4000);
    const address = candidate.roadAddress || candidate.address;
    const facts = [candidate.category, address].filter(Boolean).join(' · ');
    if (facts) return limitText(facts, 4000);
    const existing = cleanText(row.description);
    return GENERIC_DESCRIPTIONS.has(existing) ? '' : limitText(existing, 4000);
}

function buildHydration(row, candidate, source, query) {
    const hours = businessHoursFromSource(source);
    const formattedHours = formatBusinessHours(hours);
    const image = trustedBusinessImage(candidate.image || businessImageFromSource(source, candidate.name));
    const overview = overviewFor(row, candidate);
    const detail = {
        source: 'naver_search',
        hydrated_query: query,
        naver_place_id: candidate.placeId,
        matched_name: candidate.name,
        match_distance_km: candidate.distanceKm === null ? null : Number(candidate.distanceKm.toFixed(3)),
        match_name_similarity: Number(candidate.nameSimilarity.toFixed(3)),
        category: candidate.category,
        road_address: candidate.roadAddress,
        address: candidate.address,
        phone: candidate.phone,
        conveniences: candidate.conveniences,
        micro_reviews: candidate.microReviews,
        visitor_reviews_total: candidate.visitorReviewsTotal,
        visitor_reviews_score: candidate.visitorReviewsScore,
        cafe_blog_reviews_total: candidate.cafeBlogReviewsTotal,
        business_hours: hours,
        menus: menusFromSource(source, candidate.placeId)
    };
    return { candidate, overview, image, detail, ...formattedHours };
}

function formattedReverseAddress(result) {
    const region = result?.region || {};
    const regionText = ['area1', 'area2', 'area3', 'area4']
        .map((key) => cleanText(region[key]?.name))
        .filter(Boolean)
        .join(' ');
    const land = result?.land || {};
    const number = [cleanText(land.number1), cleanText(land.number2)].filter(Boolean).join('-');
    const landText = [cleanText(land.name), number].filter(Boolean).join(' ');
    return cleanText([regionText, landText].filter(Boolean).join(' '));
}

async function reverseGeocode(row, credentials) {
    const lat = numberInRange(row.latitude, 30, 44);
    const lng = numberInRange(row.longitude, 120, 135);
    if (lat === null || lng === null || !credentials.clientId || !credentials.clientSecret) return null;
    const params = new URLSearchParams({
        coords: `${lng},${lat}`,
        output: 'json',
        orders: 'roadaddr,addr'
    });
    const response = await fetch(`https://maps.apigw.ntruss.com/map-reversegeocode/v2/gc?${params}`, {
        headers: {
            'x-ncp-apigw-api-key-id': credentials.clientId,
            'x-ncp-apigw-api-key': credentials.clientSecret
        },
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS)
    });
    if (!response.ok) throw new Error(`NAVER reverse geocode HTTP ${response.status}`);
    const payload = await response.json();
    const results = Array.isArray(payload.results) ? payload.results : [];
    const road = results.find((item) => item.name === 'roadaddr');
    const parcel = results.find((item) => item.name === 'addr');
    const selected = road || parcel;
    const address = formattedReverseAddress(selected);
    if (!selected || !address) return null;
    await sleep(requestDelayMs());
    const overview = limitText([cleanText(row.category), address].filter(Boolean).join(' · '), 4000);
    return {
        candidate: {
            placeId: '',
            name: row.name,
            category: cleanText(row.category),
            roadAddress: address,
            address,
            phone: '',
            lat,
            lng,
            image: '',
            conveniences: [],
            microReviews: [],
            distanceKm: 0,
            nameSimilarity: 1
        },
        overview,
        image: '',
        usageTime: '',
        restDate: '',
        detail: {
            source: 'naver_reverse_geocode',
            enrichment_level: 'coordinate_address_only',
            place_match_verified: false,
            coordinate_source: row.provider_place_id ? 'google_places_seed' : 'existing_place',
            provider_place_id: row.provider_place_id || '',
            latitude: lat,
            longitude: lng,
            address,
            reverse_geocode_result: selected
        }
    };
}

function existingSeedHydration(row) {
    const lat = numberInRange(row.latitude, 30, 44);
    const lng = numberInRange(row.longitude, 120, 135);
    if (lat === null || lng === null || !row.provider_place_id) return null;
    const address = cleanText(row.address);
    const overview = limitText([
        cleanText(row.category),
        address || cleanText(row.area)
    ].filter(Boolean).join(' · '), 4000);
    return {
        candidate: {
            placeId: '',
            name: row.name,
            category: cleanText(row.category),
            roadAddress: address,
            address,
            phone: '',
            lat,
            lng,
            image: '',
            conveniences: [],
            microReviews: [],
            distanceKm: 0,
            nameSimilarity: 1
        },
        overview,
        image: '',
        usageTime: '',
        restDate: '',
        detail: {
            source: 'existing_google_places_seed',
            enrichment_level: 'identity_coordinate_only',
            place_match_verified: true,
            provider_place_id: row.provider_place_id,
            latitude: lat,
            longitude: lng,
            address,
            area: cleanText(row.area),
            category: cleanText(row.category)
        }
    };
}

async function resolvePlace(row, options, credentials) {
    let requestError = null;
    if (options.existingSeedOnly) {
        const hydration = existingSeedHydration(row);
        if (hydration) return hydration;
        throw new Error('EXISTING_GOOGLE_PLACE_SEED_NOT_USABLE');
    }
    if (!options.reverseGeocodeOnly) {
        for (const query of searchQueries(row)) {
            let source;
            try {
                source = await fetchSearch(query);
            } catch (error) {
                requestError = error;
                continue;
            }
            const candidate = selectCandidate(row, source);
            if (candidate) return buildHydration(row, candidate, source, query);
        }
    }
    if (options.reverseGeocodeFallback) {
        const hydration = await reverseGeocode(row, credentials);
        if (hydration) return hydration;
    }
    if (requestError) throw requestError;
    throw new Error(options.reverseGeocodeFallback ? 'NAVER_PLACE_AND_REVERSE_GEOCODE_NOT_FOUND' : 'NAVER_MATCH_NOT_FOUND');
}

function parseArgs(argv) {
    const options = {
        estimateOnly: false,
        retryFailures: false,
        reverseGeocodeFallback: true,
        reverseGeocodeOnly: false,
        existingSeedOnly: false,
        resetProgress: false,
        batchSize: DEFAULT_BATCH_SIZE,
        maxBatches: 0,
        concurrency: DEFAULT_CONCURRENCY,
        logEvery: DEFAULT_LOG_EVERY,
        limit: 0
    };
    for (const arg of argv) {
        if (arg === '--estimate') options.estimateOnly = true;
        else if (arg === '--retry-failures') options.retryFailures = true;
        else if (arg === '--reset-progress') options.resetProgress = true;
        else if (arg === '--no-reverse-geocode-fallback') options.reverseGeocodeFallback = false;
        else if (arg === '--reverse-geocode-only') options.reverseGeocodeOnly = true;
        else if (arg === '--existing-seed-only') options.existingSeedOnly = true;
        else if (arg.startsWith('--batch-size=')) options.batchSize = Math.min(300, Math.max(1, Number(arg.split('=')[1]) || DEFAULT_BATCH_SIZE));
        else if (arg.startsWith('--max-batches=')) options.maxBatches = Math.max(0, Number(arg.split('=')[1]) || 0);
        else if (arg.startsWith('--concurrency=')) options.concurrency = Math.min(4, Math.max(1, Number(arg.split('=')[1]) || DEFAULT_CONCURRENCY));
        else if (arg.startsWith('--log-every=')) options.logEvery = Math.max(1, Number(arg.split('=')[1]) || DEFAULT_LOG_EVERY);
        else if (arg.startsWith('--limit=')) options.limit = Math.max(0, Number(arg.split('=')[1]) || 0);
    }
    options.batchSize = Math.floor(options.batchSize);
    options.maxBatches = Math.floor(options.maxBatches);
    options.concurrency = Math.floor(options.concurrency);
    options.logEvery = Math.floor(options.logEvery);
    options.limit = Math.floor(options.limit);
    return options;
}

function pendingCondition(retryFailures) {
    return retryFailures
        ? "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') <> ''"
        : "detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') = ''";
}

async function estimate(db) {
    const [[counts]] = await db.query(
        `SELECT COUNT(*) AS total,
                SUM(CASE WHEN detail_hydrated_at <> '' THEN 1 ELSE 0 END) AS hydrated,
                SUM(CASE WHEN detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') = '' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN detail_hydrated_at = '' AND COALESCE(detail_hydrate_error, '') <> '' THEN 1 ELSE 0 END) AS failed
         FROM place
         WHERE is_hidden = 0 AND tourapi_id NOT REGEXP '^[0-9]+$'`
    );
    const [areas] = await db.query(
        `SELECT area, COUNT(*) AS total,
                SUM(CASE WHEN detail_hydrated_at <> '' THEN 1 ELSE 0 END) AS hydrated
         FROM place
         WHERE is_hidden = 0 AND tourapi_id NOT REGEXP '^[0-9]+$'
         GROUP BY area ORDER BY total DESC, area ASC`
    );
    return {
        total: Number(counts.total || 0),
        hydrated: Number(counts.hydrated || 0),
        pending: Number(counts.pending || 0),
        failed: Number(counts.failed || 0),
        byArea: areas.map((row) => ({ area: row.area, total: Number(row.total), hydrated: Number(row.hydrated) }))
    };
}

async function selectPending(db, options, remainingLimit) {
    const size = remainingLimit > 0 ? Math.min(options.batchSize, remainingLimit) : options.batchSize;
    const [rows] = await db.query(
        `SELECT id, name, category, description, overview, image, address, area, phone,
                latitude, longitude, provider_place_id, detail_hydrate_error
         FROM place
         WHERE is_hidden = 0
           AND tourapi_id NOT REGEXP '^[0-9]+$'
           AND ${pendingCondition(options.retryFailures)}
         ORDER BY (provider_place_id <> '') DESC, area ASC, name ASC
         LIMIT ${Number(size)}`
    );
    return rows;
}

function appendFailure(row, error) {
    fs.appendFileSync(FAILURE_LOG_FILE, `${JSON.stringify({
        placeId: row.id,
        providerPlaceId: row.provider_place_id,
        name: row.name,
        area: row.area,
        message: String(error.message || error),
        failedAt: new Date().toISOString()
    })}\n`);
}

async function markFailure(db, row, error) {
    const message = limitText(error.message || error, 1000);
    await db.execute(
        'UPDATE place SET detail_hydrate_error = ?, updated = ? WHERE id = ?',
        [message, sqlDate(), row.id]
    );
    appendFailure(row, error);
}

async function saveHydration(db, row, hydration) {
    const now = sqlDate();
    const candidateAddress = hydration.candidate.roadAddress || hydration.candidate.address;
    const description = GENERIC_DESCRIPTIONS.has(cleanText(row.description))
        ? hydration.overview
        : cleanText(row.description);
    const parkingInfo = hydration.candidate.conveniences.includes('주차') ? '주차 가능' : '';
    await db.execute(
        `UPDATE place
         SET overview = ?, description = ?, image = ?, address = ?, phone = ?,
             usage_time = ?, rest_date = ?, parking_info = ?, detail_intro = ?,
             latitude = ?, longitude = ?, detail_hydrated_at = ?, detail_hydrate_error = '', updated = ?
         WHERE id = ?`,
        [
            hydration.overview || cleanText(row.overview),
            description,
            hydration.image || cleanText(row.image),
            candidateAddress || cleanText(row.address),
            hydration.candidate.phone || cleanText(row.phone),
            hydration.usageTime,
            hydration.restDate,
            parkingInfo,
            JSON.stringify(hydration.detail),
            row.latitude || hydration.candidate.lat || '',
            row.longitude || hydration.candidate.lng || '',
            now,
            now,
            row.id
        ]
    );
}

function writeProgress(summary, row = null) {
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({
        ...summary,
        lastPlaceId: row?.id || '',
        lastName: row?.name || '',
        updatedAt: new Date().toISOString()
    }, null, 2));
}

async function run() {
    const options = parseArgs(process.argv.slice(2));
    if (options.resetProgress && fs.existsSync(PROGRESS_FILE)) fs.unlinkSync(PROGRESS_FILE);
    const db = await connect();
    const credentials = {
        clientId: projectEnvValue('NAVER_MAPS_CLIENT_ID') || projectEnvValue('NCP_MAPS_CLIENT_ID'),
        clientSecret: projectEnvValue('NAVER_MAPS_CLIENT_SECRET') || projectEnvValue('NCP_MAPS_CLIENT_SECRET')
    };
    const summary = {
        source: 'external_place_enrichment',
        batchSize: options.batchSize,
        concurrency: options.concurrency,
        processed: 0,
        succeeded: 0,
        failed: 0,
        batches: 0,
        failureLogFile: FAILURE_LOG_FILE
    };
    try {
        summary.before = await estimate(db);
        if (options.estimateOnly) return summary;
        while (true) {
            if (options.maxBatches > 0 && summary.batches >= options.maxBatches) break;
            const remainingLimit = options.limit > 0 ? options.limit - summary.processed : 0;
            if (options.limit > 0 && remainingLimit <= 0) break;
            const rows = await selectPending(db, options, remainingLimit);
            if (!rows.length) break;
            summary.batches += 1;
            console.log(`batch ${summary.batches}: ${rows.length} places`);
            let cursor = 0;
            const workers = Array.from({ length: Math.min(options.concurrency, rows.length) }, async () => {
                while (cursor < rows.length) {
                    const row = rows[cursor];
                    cursor += 1;
                    try {
                        const hydration = await resolvePlace(row, options, credentials);
                        await saveHydration(db, row, hydration);
                        summary.succeeded += 1;
                    } catch (error) {
                        await markFailure(db, row, error);
                        summary.failed += 1;
                        console.error(`failed ${row.id} ${row.name}: ${error.message}`);
                    }
                    summary.processed += 1;
                    if (summary.processed % options.logEvery === 0) {
                        writeProgress(summary, row);
                        console.log(`progress: processed=${summary.processed}, succeeded=${summary.succeeded}, failed=${summary.failed}, last=${row.name}`);
                    }
                }
            });
            await Promise.all(workers);
            writeProgress(summary, rows[rows.length - 1]);
            if (rows.length < options.batchSize) break;
            await sleep(BATCH_DELAY_MS);
        }
        summary.after = await estimate(db);
        if (summary.after.pending === 0 && fs.existsSync(PROGRESS_FILE)) fs.unlinkSync(PROGRESS_FILE);
        return summary;
    } finally {
        await db.end();
    }
}

if (require.main === module) {
    run()
        .then((summary) => console.log(JSON.stringify(summary, null, 2)))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = {
    businessHoursFromSource,
    candidatesFromSource,
    entities,
    formatBusinessHours,
    normalizeName,
    nameSimilarity,
    nameVariants,
    parseJsonAt,
    scoreCandidate,
    selectCandidate
};
