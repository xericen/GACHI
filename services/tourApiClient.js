const fs = require('node:fs');
const path = require('node:path');

const BASE_URL = 'https://apis.data.go.kr/B551011/KorService2';

const PARAM_SPECS = {
    ldongCode2: [
        ['serviceKey', 'string', true, '공공데이터포털에서 받은 인증키'],
        ['numOfRows', 'number', false, '한 페이지 결과 수'],
        ['pageNo', 'number', false, '페이지 번호'],
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은 XML)'],
        ['lDongRegnCd', 'string', false, '법정동 시도코드 ( lDongRegnCd 해당되는 법정동 시군구코드 조회 , 입력이 없을시 전체 시도목록 호출  )'],
        ['lDongListYn', 'string', false, '법정동 목록조회 여부(N:코드조회 , Y:전체목록조회)']
    ],
    lclsSystmCode2: [
        ['serviceKey', 'string', true, '공공데이터포털에서 받은 인증키'],
        ['numOfRows', 'number', false, '한 페이지 결과 수'],
        ['pageNo', 'number', false, '페이지 번호'],
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은 XML)'],
        ['lclsSystm1', 'string', false, '분류체계 1Depth 코드'],
        ['lclsSystm2', 'string', false, '분류체계 2Depth 코드(lclsSystm1 필수)'],
        ['lclsSystm3', 'string', false, '분류체계 3Depth 코드(lclsSystm1,lclsSystm2 필수)'],
        ['lclsSystmListYn', 'string', false, '분류체계 목록조회 여부(N:코드조회 , Y:전체목록조회)']
    ],
    areaBasedList2: [
        ['numOfRows', 'number', false, '한페이지결과수'],
        ['pageNo', 'number', false, '페이지번호'],
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은XML)'],
        ['arrange', 'string', false, '정렬구분 (A=제목순, C=수정일순, D=생성일순) 대표이미지가반드시있는정렬(O=제목순, Q=수정일순, R=생성일순)'],
        ['contentTypeId', 'string', false, '관광타입(12:관광지, 14:문화시설, 15:축제공연행사, 25:여행코스, 28:레포츠, 32:숙박, 38:쇼핑, 39:음식점) ID'],
        ['areaCode', 'string', false, '미사용항목(삭제예정-법정동 시도코드 대체)'],
        ['sigunguCode', 'string', false, '미사용항목(삭제예정-법정동 시군구 코드 대체)'],
        ['cat1', 'string', false, '미사용항목(삭제예정-분류체계 1Deth 코드로 대체)'],
        ['cat2', 'string', false, '미사용항목(삭제예정-분류체계 2Deth 코드로 대체)'],
        ['cat3', 'string', false, '미사용항목(삭제예정-분류체계 3Deth 코드로 대체)'],
        ['modifiedtime', 'string', false, '수정일(형식 :YYYYMMDD)'],
        ['serviceKey', 'string', true, '인증키(서비스키)'],
        ['lDongRegnCd', 'string', false, '법정동 시도 코드(법정동코드조회 참고)'],
        ['lDongSignguCd', 'string', false, '법정동 시군구 코드(법정동코드조회 참고, lDongRegnCd 필수입력)'],
        ['lclsSystm1', 'string', false, '분류체계 1Deth(분류체계코드조회 참고)'],
        ['lclsSystm2', 'string', false, '분류체계 2Deth(분류체계코드조회 참고, lclsSystm1 필수입력)'],
        ['lclsSystm3', 'string', false, '분류체계 3Deth(분류체계코드조회 참고, lclsSystm1/lclsSystm2 필수입력)']
    ],
    searchKeyword2: [
        ['numOfRows', 'number', false, '한페이지결과수'],
        ['pageNo', 'number', false, '페이지번호'],
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은XML)'],
        ['arrange', 'string', false, '정렬구분 (A=제목순, C=수정일순, D=생성일순) 대표이미지가반드시있는정렬(O=제목순, Q=수정일순, R=생성일순)'],
        ['keyword', 'string', true, '검색요청할키워드 : (국문=인코딩필요)'],
        ['serviceKey', 'string', true, '인증키(서비스키)'],
        ['areaCode', 'string', false, '미사용항목(삭제예정-법정동 시도코드 대체)'],
        ['sigunguCode', 'string', false, '미사용항목(삭제예정-법정동 시군구 코드 대체)'],
        ['cat1', 'string', false, '미사용항목(삭제예정-분류체계 1Deth 코드로 대체)'],
        ['cat2', 'string', false, '미사용항목(삭제예정-분류체계 2Deth 코드로 대체)'],
        ['cat3', 'string', false, '미사용항목(삭제예정-분류체계 3Deth 코드로 대체)'],
        ['lDongRegnCd', 'string', false, '법정동 시도코드(법정동코드조회 참고)'],
        ['lDongSignguCd', 'string', false, '법정동 시군구코드(법정동코드조회 참고, lDongRegnCd 필수입력)'],
        ['lclsSystm1', 'string', false, '분류체계 1Deth(분류체계코드조회 참고)'],
        ['lclsSystm2', 'string', false, '분류체계 2Deth(분류체계코드조회 참고, lclsSystm1 필수입력)'],
        ['lclsSystm3', 'string', false, '분류체계 3Deth(분류체계코드조회 참고, lclsSystm1/lclsSystm2 필수입력)']
    ],
    detailCommon2: [
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은XML)'],
        ['contentId', 'string', true, '콘텐츠ID'],
        ['numOfRows', 'number', false, '한페이지결과수'],
        ['pageNo', 'number', false, '페이지번호'],
        ['serviceKey', 'string', true, '인증키(서비스키)']
    ],
    detailIntro2: [
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은XML)'],
        ['contentId', 'string', true, '콘텐츠ID'],
        ['contentTypeId', 'string', true, '관광타입 ID'],
        ['numOfRows', 'number', false, '한페이지결과수'],
        ['pageNo', 'number', false, '페이지번호'],
        ['serviceKey', 'string', true, '인증키(서비스키)']
    ],
    detailImage2: [
        ['MobileOS', 'string', true, 'OS 구분 : IOS (아이폰), AND (안드로이드), WEB (웹), ETC(기타)'],
        ['MobileApp', 'string', true, '서비스명(어플명)'],
        ['_type', 'string', false, '응답메세지 형식 : REST방식의 URL호출 시 json값 추가(디폴트 응답메세지 형식은XML)'],
        ['contentId', 'string', true, '콘텐츠ID'],
        ['imageYN', 'string', false, '이미지조회1 : Y=콘텐츠이미지조회 N=”음식점”타입의음식메뉴이미지'],
        ['numOfRows', 'number', false, '한페이지결과수'],
        ['pageNo', 'number', false, '페이지번호'],
        ['serviceKey', 'string', true, '인증키(서비스키)']
    ]
};

function envCandidates() {
    const roots = new Set();
    roots.add(process.cwd());
    try {
        roots.add(fs.realpathSync(process.cwd()));
    } catch (error) {
        // ignore
    }
    roots.add(path.resolve(__dirname, '..'));
    roots.add(path.resolve(__dirname, '..', '..'));

    const files = [];
    for (const root of roots) {
        files.push(path.join(root, '.env'));
        files.push(path.join(root, '.env.local'));
    }
    return [...new Set(files)];
}

function loadEnvFiles() {
    const loaded = [];
    for (const file of envCandidates()) {
        if (!fs.existsSync(file)) continue;
        const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) continue;
            const index = trimmed.indexOf('=');
            if (index < 1) continue;
            const key = trimmed.slice(0, index).trim();
            let value = trimmed.slice(index + 1).trim();
            if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            if (process.env[key] === undefined) process.env[key] = value;
        }
        loaded.push(file);
    }
    return loaded;
}

function normalizeItems(body) {
    const item = body?.items?.item;
    if (!item) return [];
    return Array.isArray(item) ? item : [item];
}

class TourApiClient {
    constructor(options = {}) {
        this.loadedEnvFiles = loadEnvFiles();
        this.serviceKey = options.serviceKey || process.env.TOUR_API_KEY || process.env.TOUR_SERVICE_KEY || '';
        this.mobileOS = options.mobileOS || process.env.TOUR_API_MOBILE_OS || 'ETC';
        this.mobileApp = options.mobileApp || process.env.TOUR_API_MOBILE_APP || 'GACHI';
        this.timeoutMs = Number(options.timeoutMs || process.env.TOUR_API_TIMEOUT_MS || 15000);
    }

    validate(operation, params) {
        const spec = PARAM_SPECS[operation];
        if (!spec) throw new Error(`Unsupported TourAPI operation: ${operation}`);
        for (const [name, type, required] of spec) {
            if (!required) continue;
            const value = params[name];
            if (value === undefined || value === null || value === '') {
                throw new Error(`${operation} requires ${name} (${type})`);
            }
        }
    }

    async request(operation, params = {}) {
        const merged = {
            MobileOS: this.mobileOS,
            MobileApp: this.mobileApp,
            _type: 'json',
            serviceKey: this.serviceKey,
            ...params
        };
        this.validate(operation, merged);

        const url = new URL(`${BASE_URL}/${operation}`);
        for (const [key, value] of Object.entries(merged)) {
            if (value === undefined || value === null || value === '') continue;
            url.searchParams.set(key, String(value));
        }

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        let response;
        let raw;
        try {
            response = await fetch(url, { signal: controller.signal });
            raw = await response.text();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error(`${operation} timeout after ${this.timeoutMs}ms`);
            }
            throw error;
        } finally {
            clearTimeout(timeout);
        }
        let json = null;
        try {
            json = JSON.parse(raw);
        } catch (error) {
            // XML error bodies are kept as raw text.
        }
        if (!response.ok) {
            throw new Error(`${operation} HTTP ${response.status}: ${raw.slice(0, 300)}`);
        }
        if (json?.response?.header?.resultCode && json.response.header.resultCode !== '0000') {
            throw new Error(`${operation} ${json.response.header.resultCode}: ${json.response.header.resultMsg}`);
        }
        return { raw, json, items: normalizeItems(json?.response?.body), url };
    }

    ldongCode(params = {}) {
        return this.request('ldongCode2', params);
    }

    lclsSystmCode(params = {}) {
        return this.request('lclsSystmCode2', params);
    }

    areaBasedList(params = {}) {
        return this.request('areaBasedList2', params);
    }

    searchKeyword(params = {}) {
        return this.request('searchKeyword2', params);
    }

    detailCommon(contentId, params = {}) {
        return this.request('detailCommon2', { contentId, ...params });
    }

    detailIntro(contentId, contentTypeId, params = {}) {
        return this.request('detailIntro2', { contentId, contentTypeId, ...params });
    }

    detailImage(contentId, params = {}) {
        return this.request('detailImage2', { contentId, imageYN: 'Y', ...params });
    }
}

module.exports = { TourApiClient, PARAM_SPECS, loadEnvFiles, envCandidates };
