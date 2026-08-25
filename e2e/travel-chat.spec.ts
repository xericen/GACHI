import { expect, Page, test } from '@playwright/test';

type Reply = Record<string, unknown>;

const baseState = {
  region: '제주', destination: '제주', start_location: '제주공항', accommodation_area: '제주시청',
  start_date: '2026-08-29', end_date: '2026-08-31', days: 3,
  arrival_time: '17:00', departure_time: '11:00', companions: ['부모님'],
  transport: '대중교통', schedule_pace: '보통', walking_tolerance: '10분 이내',
  rest_preference: '자주 쉬기', preferences: ['자연', '맛집', '카페'],
};

const draft = {
  title: '제주 3일 코스', region: '제주', transport: '대중교통',
  quality: { checks: { simple_route_ok: true } },
  days: [{
    day: 1, label: '1일차', date: '2026-08-29', start_time: '17:00', end_time: '20:00',
    total_move_minutes: 20, total_distance_meters: 3000, expected_move_time: '약 20분',
    return_plan: { time: '20:00', label: '숙소' },
    places: [{
      place_id: 'fixture-1', name: '제주 산책로', category: '자연', address: '제주특별자치도 제주시',
      time: '17:30', time_period: '오후', duration_minutes: 60,
      move_from_previous: { mode: 'transit', duration_minutes: 20, distance_meters: 3000 },
    }],
  }],
};

async function openPlanner(page: Page) {
  await page.goto('/');
  await page.getByTestId('open-ai-planner-home').click();
  await expect(page.getByTestId('chat-input')).toBeVisible();
}

async function submit(page: Page, prompt: string) {
  await page.getByTestId('chat-input').fill(prompt);
  await page.getByTestId('chat-send').click();
}

async function mockChat(page: Page, resolver: (prompt: string) => Reply) {
  await page.route('**/wiz/api/page.access/chat_send**', async route => {
    const request = route.request();
    const body = request.postData() || '';
    const prompt = new URLSearchParams(body).get('prompt') || '';
    const payload = resolver(prompt);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, data: payload }),
    });
  });
}

test('모바일 여행 조건을 마우스 드래그로 가로 탐색한다', async ({ page }) => {
  await mockChat(page, () => ({
    message: '조건을 확인했어요. 시작 위치를 조정할 수 있어요.', stage: 'collecting',
    action: 'ask_clarification', travel_state: baseState, suggested_replies: [],
  }));
  await openPlanner(page);
  await submit(page, '제주 여행 조건을 확인해줘');
  const scroller = page.getByTestId('travel-condition-scroller');
  await expect(scroller).toBeVisible();
  const before = await scroller.evaluate(node => ({ left: node.scrollLeft, width: node.scrollWidth, client: node.clientWidth }));
  expect(before.width).toBeGreaterThan(before.client);
  const box = await scroller.boundingBox();
  if (!box) throw new Error('condition scroller bounding box missing');
  await page.mouse.move(box.x + box.width - 15, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + 25, box.y + box.height / 2, { steps: 8 });
  await page.mouse.up();
  await expect.poll(() => scroller.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
});

test('상황별 선택 버튼과 조건 수정 흐름을 실제 클릭한다', async ({ page }) => {
  await mockChat(page, prompt => {
    if (prompt === '조건 수정') return {
      message: '어떤 여행 조건을 수정할까요?', stage: 'editing_conditions', action: 'ask_clarification',
      travel_state: { ...baseState, conversation_stage: 'editing_conditions' },
      suggested_replies: [{ label: '출발 위치', prompt: '출발 위치 수정' }, { label: '교통', prompt: '교통 수정' }],
    };
    if (prompt === '교통 수정') return {
      message: '주로 어떻게 이동할까요?', stage: 'collecting', action: 'ask_clarification',
      travel_state: { ...baseState, transport: '', pending_slot: 'transport' },
      suggested_replies: ['도보', '대중교통', '자동차'],
    };
    return {
      message: '조건을 확인한 뒤 코스를 만들어주세요.', stage: 'ready_to_generate', action: 'answer_only',
      travel_state: baseState, suggested_replies: [{ label: '코스 만들기', prompt: '이 조건으로 코스 만들어줘' }],
    };
  });
  await openPlanner(page);
  await submit(page, '제주 일정 조건');
  await page.getByTestId('edit-conditions').click();
  await page.getByTestId('suggested-reply').filter({ hasText: '교통' }).click();
  await expect(page.getByTestId('suggested-reply').filter({ hasText: '도보' })).toBeVisible();
});

test('생성 실패 후 장소 수 줄이기를 눌러 즉시 재생성한다', async ({ page }) => {
  await mockChat(page, prompt => {
    if (prompt === '이 조건으로 코스 만들어줘') return {
      message: '현재 조건으로 동선을 끝까지 연결하지 못했어요.', stage: 'error', action: 'ask_clarification',
      failure_stage: 'place_search', failure_reason: { code: 'insufficient_route_candidates' },
      travel_state: { ...baseState, pending_slot: 'recovery_action' },
      suggested_replies: [{ label: '장소 수 줄이기', prompt: '장소 수 줄여서 다시 만들어줘' }],
    };
    if (prompt === '장소 수 줄여서 다시 만들어줘') return {
      message: '이동시간에 맞춰 코스를 다시 만들었어요.', stage: 'draft_ready', action: 'generate_itinerary',
      travel_state: { ...baseState, itinerary_draft: draft }, itinerary_draft: draft,
      suggested_replies: [{ label: '덜 걷기', prompt: '덜 걷게 바꿔줘' }],
    };
    return { message: '조건을 확인해주세요.', stage: 'ready_to_generate', action: 'answer_only', travel_state: baseState };
  });
  await openPlanner(page);
  await submit(page, '제주 일정 조건');
  await page.getByTestId('generate-course').click();
  await expect(page.getByTestId('planner-failure')).toBeVisible();
  await page.getByTestId('suggested-reply').filter({ hasText: '장소 수 줄이기' }).click();
  await expect(page.getByRole('heading', { name: '제주 1일차' })).toBeVisible();
});
