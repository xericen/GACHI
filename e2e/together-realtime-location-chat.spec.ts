import { expect, request as playwrightRequest, test } from '@playwright/test';
import { io, Socket } from 'socket.io-client';

type ApiResult = { code: number; data: Record<string, any> };

const namespace = '/wiz/app/main/page.access';

async function api(request: any, baseURL: string, name: string, token: string, form: Record<string, any>): Promise<ApiResult> {
  const response = await request.post(`${baseURL}/wiz/api/page.access/${name}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    form,
  });
  expect(response.ok(), `${name} HTTP status`).toBeTruthy();
  return await response.json();
}

async function register(request: any, baseURL: string, label: string) {
  const nonce = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const password = `E2e-${nonce}-A7!`;
  const result = await api(request, baseURL, 'register', '', {
    name: label,
    email: `together-${nonce}@example.com`,
    password,
    password_confirm: password,
  });
  expect(result.code).toBe(200);
  return { token: result.data.token, user: result.data.session };
}

function waitForSocketEvent(socket: Socket, event: string, predicate: (payload: any) => boolean = () => true) {
  return new Promise<any>((resolve, reject) => {
    const timer = setTimeout(() => {
      socket.off(event, handler);
      reject(new Error(`${event} event timeout`));
    }, 10_000);
    const handler = (payload: any) => {
      if (!predicate(payload)) return;
      clearTimeout(timer);
      socket.off(event, handler);
      resolve(payload);
    };
    socket.on(event, handler);
  });
}

async function connectSocket(baseURL: string, token: string) {
  const socket = io(`${baseURL}${namespace}`, {
    transports: ['polling'],
    upgrade: false,
    reconnection: true,
    timeout: 10_000,
  });
  await new Promise<void>((resolve, reject) => {
    socket.once('connect', () => {
      socket.emit('join', { token });
      resolve();
    });
    socket.once('connect_error', reject);
  });
  return socket;
}

test('두 실제 계정의 위치·채팅·종료와 소켓 재연결 복구', async ({ baseURL }) => {
  test.setTimeout(90_000);
  const origin = baseURL || 'http://127.0.0.1:3000';
  const ownerRequest = await playwrightRequest.newContext({ baseURL: origin });
  const peerRequest = await playwrightRequest.newContext({ baseURL: origin });
  const owner = await register(ownerRequest, origin, '같이지도 소유자');
  const peer = await register(peerRequest, origin, '같이지도 동행자');
  const courseId = `together-course-${Date.now()}`;
  const postId = `together-post-${Date.now()}`;
  const post = {
    id: postId,
    courseId,
    courseConfirmed: true,
    title: '같이 지도 E2E 동행',
    route: '수원 실시간 동행 코스',
    location: '수원',
    date: '2026-08-26',
    time: '10:00',
    meetingPoint: '수원역',
    intro: '위치와 채팅 통합 검증',
    host: owner.user.name,
    status: 'open',
  };

  const saved = await api(ownerRequest, origin, 'save_course', owner.token, {
    community_action: 'companion_post',
    post: JSON.stringify(post),
  });
  expect(saved.code).toBe(200);

  const applied = await api(peerRequest, origin, 'save_course', peer.token, {
    community_action: 'companion_apply',
    post_id: postId,
    application: JSON.stringify({
      safetyRecordConsent: true,
      safetyRecordConsentVersion: 'safety-record-v1-180d',
      resume: { nickname: peer.user.name, availabilityConfirmed: true },
    }),
  });
  expect(applied.code).toBe(200);
  const applicationId = applied.data.application.id;

  const accepted = await api(ownerRequest, origin, 'save_course', owner.token, {
    community_action: 'companion_accept',
    post_id: postId,
    application_id: applicationId,
  });
  expect(accepted.code).toBe(200);

  const endsAt = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();
  const ownerMeeting = await api(ownerRequest, origin, 'zenly_trip_meeting_start', owner.token, {
    post_id: postId,
    ends_at: endsAt,
  });
  const peerMeeting = await api(peerRequest, origin, 'zenly_trip_meeting_start', peer.token, {
    post_id: postId,
    ends_at: endsAt,
  });
  expect(ownerMeeting.code).toBe(200);
  expect(peerMeeting.data.meeting.id).toBe(ownerMeeting.data.meeting.id);
  const meetingId = ownerMeeting.data.meeting.id;

  const ownerSocket = await connectSocket(origin, owner.token);
  let peerSocket = await connectSocket(origin, peer.token);

  await api(ownerRequest, origin, 'zenly_location_share_start', owner.token, {
    meeting_id: meetingId,
    duration: '60',
    home_enabled: 'false',
    stay_enabled: 'false',
  });
  await api(peerRequest, origin, 'zenly_location_share_start', peer.token, {
    meeting_id: meetingId,
    duration: '60',
    home_enabled: 'false',
    stay_enabled: 'false',
  });

  const locationEvent = waitForSocketEvent(ownerSocket, 'together_location_update', payload => payload.meetingId === meetingId);
  await api(peerRequest, origin, 'zenly_location_update', peer.token, {
    meeting_id: meetingId,
    lat: '37.2664',
    lng: '127.0006',
    accuracy: '8',
  });
  await locationEvent;
  await api(ownerRequest, origin, 'zenly_location_update', owner.token, {
    meeting_id: meetingId,
    lat: '37.2651',
    lng: '127.0012',
    accuracy: '9',
  });
  const snapshot = await api(ownerRequest, origin, 'zenly_location_snapshot', owner.token, { meeting_id: meetingId });
  expect(snapshot.code).toBe(200);
  expect(snapshot.data.positions).toHaveLength(1);
  expect(snapshot.data.positions[0].precise).toBe(true);
  expect(snapshot.data.positions[0].lat).toBeCloseTo(37.2664, 4);

  const messageEvent = waitForSocketEvent(peerSocket, 'together_meeting_message', payload => payload.meetingId === meetingId);
  const sent = await api(ownerRequest, origin, 'zenly_meeting_message_send', owner.token, {
    meeting_id: meetingId,
    message: '수원역 2번 출구에서 만나요',
  });
  expect(sent.code).toBe(200);
  const receivedMessage = await messageEvent;
  expect(receivedMessage.text).toBe('수원역 2번 출구에서 만나요');

  const readEvent = waitForSocketEvent(ownerSocket, 'together_meeting_read', payload => payload.meetingId === meetingId);
  await api(peerRequest, origin, 'zenly_meeting_messages_read', peer.token, { meeting_id: meetingId });
  const readPayload = await readEvent;
  expect(readPayload.messageIds).toContain(receivedMessage.id);

  const typingEvent = waitForSocketEvent(ownerSocket, 'together_meeting_typing', payload => payload.meetingId === meetingId);
  await api(peerRequest, origin, 'zenly_meeting_typing', peer.token, { meeting_id: meetingId, typing: 'true' });
  expect((await typingEvent).typing).toBe(true);

  peerSocket.close();
  await api(ownerRequest, origin, 'zenly_meeting_message_send', owner.token, {
    meeting_id: meetingId,
    message: '연결이 끊겨도 저장되는 메시지',
  });
  peerSocket = await connectSocket(origin, peer.token);
  const recovered = await api(peerRequest, origin, 'zenly_meeting_messages', peer.token, { meeting_id: meetingId });
  expect(recovered.data.messages.some((message: any) => message.text === '연결이 끊겨도 저장되는 메시지')).toBe(true);

  const endedEvent = waitForSocketEvent(peerSocket, 'together_meeting_ended', payload => payload.meetingId === meetingId);
  const ended = await api(ownerRequest, origin, 'zenly_meeting_end', owner.token, { meeting_id: meetingId });
  expect(ended.code).toBe(200);
  await endedEvent;
  const afterEnd = await api(peerRequest, origin, 'zenly_location_snapshot', peer.token, { meeting_id: meetingId });
  expect(afterEnd.code).toBe(410);

  ownerSocket.close();
  peerSocket.close();
  await ownerRequest.dispose();
  await peerRequest.dispose();
});
