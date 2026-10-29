import { expect, test } from '@playwright/test';

test('날짜만 있는 오래된 준비 응답에서도 코스 만들기를 표시하지 않는다', async ({ page }) => {
  await page.route('**/wiz/api/page.access/chat_send**', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ code: 200, data: {
      message: '입력 조건을 정리했어요. 실제 장소와 이동 동선은 코스 만들기를 누른 뒤 확인해요.',
      stage: 'ready_to_generate', action: 'answer_only', missing_slots: [],
      travel_state: { region: '2026-10-29', destination: '2026-10-29',
        start_date: '2026-10-29', end_date: '2026-10-29', days: 1, transport: '미정' },
      suggested_replies: [{ label: '코스 만들기', prompt: '이 조건으로 코스 만들어줘' }]
    } })
  }));
  await page.goto('/');
  await page.getByTestId('open-ai-planner-home').click();
  await page.getByTestId('chat-input').fill('내일');
  await page.getByTestId('chat-send').click();
  await expect(page.getByTestId('generate-course')).toHaveCount(0);
  await expect(page.getByText('어느 지역으로 여행할 예정인가요?', { exact: true })).toBeVisible();
  await expect(page.getByText('입력 조건을 정리했어요. 실제 장소와 이동 동선은 코스 만들기를 누른 뒤 확인해요.', { exact: true })).toHaveCount(0);
});

test('핵심 조건이 충분한 준비 응답에서는 코스 만들기를 표시한다', async ({ page }) => {
  await page.route('**/wiz/api/page.access/chat_send**', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ code: 200, data: {
      message: '여행 조건을 확인했어요.', stage: 'ready_to_generate', action: 'answer_only',
      missing_slots: [], can_generate: true,
      travel_state: { region: '부산', start_location: '부산역', transport: '대중교통', days: 1,
        start_date: '2026-10-29', end_date: '2026-10-29', arrival_time: '10:00', departure_time: '18:00' }
    } })
  }));
  await page.goto('/');
  await page.getByTestId('open-ai-planner-home').click();
  await page.getByTestId('chat-input').fill('부산역에서 내일 대중교통으로 오전 10시부터 오후 6시까지');
  await page.getByTestId('chat-send').click();
  await expect(page.getByTestId('generate-course')).toBeVisible();
});
