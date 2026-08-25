import { expect, test } from '@playwright/test';

const room = {
  id: 'dm-read-indicator-fixture',
  companionPostId: 'read-indicator-fixture',
  name: '테스트 동행',
  handle: '제주 사진 동행',
  avatar: '테',
  status: '동행 준비방',
  preview: '확인 전 메시지',
  time: '07:10',
  unread: 0,
  category: 'companion',
  messages: [
    {
      id: 'outgoing-read',
      postId: 'read-indicator-fixture',
      senderKey: 'indicator-user',
      role: 'me',
      text: '확인한 메시지',
      time: '07:09',
      read: true,
      readAt: '2026-08-24T07:09:30',
    },
    {
      id: 'outgoing-unread',
      postId: 'read-indicator-fixture',
      senderKey: 'indicator-user',
      role: 'me',
      text: '확인 전 메시지',
      time: '07:10',
      read: false,
      readAt: '',
    },
  ],
};

const companionPost = {
  id: 'read-indicator-fixture',
  courseId: 'confirmed-course-fixture',
  courseConfirmed: true,
  status: 'matched',
  title: '제주 사진 동행',
  route: '제주 사진 코스',
  routeStops: ['제주공항', '용두암', '도두봉'],
  date: '2026-08-30',
  time: '10:00',
  meetingPoint: '제주공항 1번 출구',
  estimatedCost: '3만원',
  pace: 'balanced',
  moodTags: ['사진', '산책'],
  flexibility: ['시간 조율'],
  packingItems: ['보조 배터리'],
};

test('동행 준비방 상세를 유지하고 읽음 숫자를 갱신한다', async ({ page }) => {
  const socketTransportErrors: string[] = [];
  page.on('console', message => {
    if (message.type() === 'error' && /WebSocket connection|Invalid frame header/.test(message.text())) {
      socketTransportErrors.push(message.text());
    }
  });
  await page.addInitScript(() => {
    window.localStorage.setItem('tour-on-jwt', 'fixture.payload.signature');
    window.localStorage.setItem('tour-on-user', JSON.stringify({
      id: 'indicator-user',
      email: 'indicator@example.com',
      name: '표시 테스트',
      role: 'user',
    }));
  });

  await page.route('**/auth/check**', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ code: 200, data: { status: false, session: {} } }),
  }));

  await page.route('**/wiz/api/page.access/saved_courses**', async route => {
    const action = new URLSearchParams(route.request().postData() || '').get('community_action');
    let data: Record<string, unknown> = { courses: [], posts: [] };
    if (action === 'direct_chat_rooms') data = { rooms: [room] };
    if (action === 'companions') data = { posts: [companionPost] };
    if (action === 'companion_applications') data = { applications: [], matched: true };
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, data }),
    });
  });

  await page.goto('/access?tab=chat');
  await page.getByRole('button', { name: '1:1 채팅' }).click();
  await page.getByRole('button', { name: /테스트 동행/ }).click();

  const preparationToggle = page.getByRole('button', { name: '동행 준비방 펼치기' });
  await preparationToggle.click();
  await expect(page.getByText('코스와 이동 동선')).toBeVisible();
  await page.waitForTimeout(2_600);
  await expect(page.getByRole('button', { name: '동행 준비방 접기' })).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByText('코스와 이동 동선')).toBeVisible();

  const unread = page.getByTestId('direct-message-unread');
  await expect(unread).toBeVisible();
  await expect(unread).toHaveCount(1);
  await expect(unread).toHaveText('1');
  await expect(unread).toHaveAttribute('aria-label', '상대방이 아직 읽지 않음');

  room.messages[1].read = true;
  room.messages[1].readAt = '2026-08-24T07:10:30';
  await page.reload();
  await page.getByRole('button', { name: '1:1 채팅' }).click();
  const refreshedRoom = page.getByRole('button', { name: /테스트 동행/ });
  await expect(refreshedRoom).toBeVisible();
  await refreshedRoom.click();
  await expect(unread).toHaveCount(0);
  expect(socketTransportErrors).toEqual([]);
});
