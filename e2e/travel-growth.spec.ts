import { test, expect, Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const course = { id: 'verified-trip', title: '여행 검증 코스', region: '서울', source: 'mine' };
const spots = [
  { place_id: 'museum', name: '서울 박물관', category: '박물관', order: 1, lat: 37.56, lng: 126.97, address: '서울시 박물관로 1', phone: '02-123-4567', day: 1, visit_time: '10:00', checked: false },
  { place_id: 'park', name: '서울 공원', category: '공원', order: 2, lat: 37.57, lng: 126.98, address: '서울시 공원로 2', day: 1, visit_time: '12:00', checked: false },
];
const execution = { course, places: spots, progress: { checked: 0, total: 2 } };
const signals = { enabled: true, followed_authors: ['bob'], executed_courses: ['verified-trip'], terms: ['문화', '카페'] };
const reviewData = { targets: [{ id: 'bob', name: '동행자' }], completion: { checked: 2, total: 2, automatic: 1 }, reviews: [], count: 0, average: null };

async function fixtureApp(page: Page, options: { failure?: boolean } = {}) {
  await page.addInitScript(() => {
    localStorage.setItem('tour-on-jwt', 'fixture-token');
    localStorage.setItem('tour-on-user', JSON.stringify({ id: 'alice', name: '테스트 여행자', email: 'fixture@example.invalid' }));
    Object.defineProperty(navigator, 'geolocation', { value: {
      getCurrentPosition: (success: any) => success({ coords: { latitude: 37.56, longitude: 126.97, accuracy: 20 }, timestamp: Date.now() }),
      watchPosition: () => 1, clearWatch: () => {},
    }, configurable: true });
  });
  await page.route('**/access?**', route => route.fulfill({ contentType: 'text/html', body: readFileSync('bundle/www/index.html', 'utf8') }));
  await page.route('**/auth/check**', route => route.fulfill({ json: { code: 200, data: { status: true, session: { id: 'alice', name: '테스트 여행자' } } } }));
  await page.route('https://api.open-meteo.com/**', route => route.fulfill({ json: {
    current: { weather_code: 61 }, daily: { precipitation_probability_max: [80] },
  } }));
  await page.route('https://**/*', route => route.abort());
  // Override the broad external block with the weather fixture.
  await page.route('https://api.open-meteo.com/**', route => route.fulfill({ json: {
    current: { weather_code: 61 }, daily: { precipitation_probability_max: [80] },
  } }));
  await page.route('**/wiz/api/**', async route => {
    const url = route.request().url();
    const params = new URLSearchParams(route.request().postData() || '');
    let data: any = { rows: [], posts: [], courses: [], notifications: [], applications: [], chats: [], rooms: [], following_authors: [], behavioral_signals: signals };
    if (url.endsWith('/saved_courses') && !params.get('community_action')) data = {
      courses: [], course_ids: [], owned_courses: [{ ...course, user_id: 'alice', is_public: true, tags: ['여행'], places: spots }],
      public_courses: [], following_authors: [], behavioral_signals: signals,
    };
    else if (url.includes('course_execution_courses')) data = { courses: [{ ...course, location: '서울', place_count: 2 }] };
    else if (url.endsWith('/course_execution')) data = { execution };
    else if (url.endsWith('/travel_growth')) {
      const action = params.get('action');
      if (action === 'replan') {
        if (options.failure) return route.fulfill({ json: { code: 503, data: { message: '재계획 서버에 연결하지 못했습니다.' } } });
        data = { token: 'preview-token', proposal: { execution, detected: ['강수 예보'],
          changes: [{ before: '서울 공원', after: '서울 미술관', reason: '강수 예보: 실내 대안' }], warnings: [] } };
      } else if (action === 'apply_replan') data = { execution: { ...execution, places: [spots[0], { ...spots[1], place_id: 'gallery', name: '서울 미술관' }] } };
      else if (action === 'reviews') data = reviewData;
      else if (action === 'review_submit') data = { ...reviewData, count: 1, average: 5,
        reviews: [{ reviewer_name: '테스트 여행자', target_name: '동행자', rating: 5, comment: params.get('comment'), automatic: 1, total: 2 }] };
      else if (action === 'trust') data = { trust: { average: null, count: 0, reviewers: 0 } };
      else data = { behavioral_signals: signals };
    }
    await route.fulfill({ json: { code: 200, data } });
  });
  await page.goto('/access?tab=map');
  await expect.poll(() => page.evaluate(() => !!localStorage.getItem('gachi-offline-saved-courses-data'))).toBe(true);
  await page.getByRole('button', { name: '코스 불러오기', exact: true }).click();
  await page.locator('.gachi-course-card').filter({ hasText: course.title }).click();
  await page.getByRole('button', { name: '현재 위치를 출발지로 사용' }).click();
  await page.locator('.gachi-course-start-button').click();
  await expect(page.getByRole('button', { name: '원터치 재계획', exact: true })).toBeVisible();
}

test('원터치 상황 감지·고정 선택·재계획 적용과 서버 실패 안내', async ({ page }) => {
  await fixtureApp(page);
  await page.getByText('고정 장소·휴무·지연 설정', { exact: true }).click();
  const fixed = page.locator('.travel-replan-panel details div').filter({ hasText: '서울 박물관' }).getByRole('checkbox').first();
  await fixed.check();
  const request = page.waitForRequest(req => req.url().endsWith('/travel_growth') && (req.postData() || '').includes('action=replan'));
  await page.getByRole('button', { name: '원터치 재계획', exact: true }).click();
  expect(new URLSearchParams((await request).postData() || '').get('fixed_ids')).toBe('["museum"]');
  await expect(page.getByText('다음 장소의 오늘 강수 확률 80%', { exact: true })).toBeVisible();
  await expect(page.getByText('서울 공원 → 서울 미술관 · 강수 예보: 실내 대안', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '남은 일정에 적용', exact: true }).click();
  await expect(page.getByText('남은 일정에 적용했습니다. 새 경로를 확인해주세요.', { exact: true })).toBeVisible();
});

test('API 장애에서 기존 코스를 보존하고 오류를 안내한다', async ({ page }) => {
  await fixtureApp(page, { failure: true });
  await page.getByRole('button', { name: '원터치 재계획', exact: true }).click();
  await expect(page.getByText('재계획 서버에 연결하지 못했습니다.', { exact: true })).toBeVisible();
  await expect(page.locator('.gachi-active-course-search')).toContainText(course.title);
  await expect(page.getByRole('button', { name: '남은 일정에 적용', exact: true })).toHaveCount(0);
});

test('검증된 후기 작성을 실제 클릭한다', async ({ page }) => {
  await fixtureApp(page);
  await page.getByRole('button', { name: '동행 후기', exact: true }).click();
  const reviews = page.getByRole('dialog', { name: '검증된 동행 후기' });
  await expect(reviews.getByText('내 방문 기록 2 / 2곳 · GPS 1곳', { exact: true })).toBeVisible();
  await reviews.getByRole('textbox', { name: '동행 후기' }).fill('약속 시간을 잘 지켰습니다.');
  await reviews.getByRole('button', { name: '후기 등록', exact: true }).click();
  await expect(reviews.getByText('약속 시간을 잘 지켰습니다.', { exact: true })).toBeVisible();
});
