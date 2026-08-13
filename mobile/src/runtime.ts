import { App } from '@capacitor/app';
import { Browser } from '@capacitor/browser';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Capacitor } from '@capacitor/core';
import { Geolocation } from '@capacitor/geolocation';
import { Haptics, NotificationType } from '@capacitor/haptics';
import { Keyboard } from '@capacitor/keyboard';
import { Network } from '@capacitor/network';
import { Preferences } from '@capacitor/preferences';
import { PushNotifications } from '@capacitor/push-notifications';
import { SplashScreen } from '@capacitor/splash-screen';
import { StatusBar, Style } from '@capacitor/status-bar';

type MobileConfig = {
  serverOrigin: string;
  allowedHosts?: string[];
  deepLinkScheme?: string;
  buildTime?: string;
};

type MobileBridge = {
  isNative: boolean;
  ready: Promise<void>;
  getCurrentPosition: (options?: PositionOptions) => Promise<any>;
  takePhoto: () => Promise<string | null>;
  enablePushNotifications: () => Promise<boolean>;
  openExternal: (url: string) => Promise<void>;
  resolveServerUrl: (url: string) => string;
};

declare global {
  interface Window {
    GACHI_MOBILE_CONFIG?: MobileConfig;
    GachiMobile?: MobileBridge;
    wiz?: any;
  }
}

const config = window.GACHI_MOBILE_CONFIG || { serverOrigin: 'https://travel.wizide.com' };
const serverOrigin = String(config.serverOrigin || '').replace(/\/$/, '');
const isNative = Capacitor.isNativePlatform();
const remotePrefixes = ['/api/', '/wiz/', '/auth/'];
const authStorageKeys = ['tour-on-jwt', 'tour-on-user', 'tour-on-token', 'tour-on-session', 'tour-on-auth'];
const nativeWatchIds = new Map<number, Promise<string>>();
let nextWatchId = 1;
let pushRegistrationStarted = false;

function resolveServerUrl(value: string): string {
  if (!value || !serverOrigin) return value;
  if (remotePrefixes.some((prefix) => value === prefix.slice(0, -1) || value.startsWith(prefix))) {
    return `${serverOrigin}${value}`;
  }
  try {
    const parsed = new URL(value, window.location.href);
    if (parsed.origin === window.location.origin && remotePrefixes.some((prefix) => parsed.pathname.startsWith(prefix))) {
      return `${serverOrigin}${parsed.pathname}${parsed.search}${parsed.hash}`;
    }
  } catch {
    return value;
  }
  return value;
}

function installRequestBridge() {
  const originalFetch = window.fetch.bind(window);
  window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
    if (typeof input === 'string') {
      input = resolveServerUrl(input);
    } else if (input instanceof URL) {
      input = new URL(resolveServerUrl(input.toString()));
    } else if (input instanceof Request) {
      const nextUrl = resolveServerUrl(input.url);
      if (nextUrl !== input.url) input = new Request(nextUrl, input);
    }
    const nextInit: RequestInit = { ...(init || {}) };
    if (!nextInit.credentials) nextInit.credentials = 'include';
    return originalFetch(input, nextInit);
  }) as typeof window.fetch;

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method: string, url: string | URL, ...args: any[]) {
    const nextUrl = resolveServerUrl(String(url));
    (this as any).__gachiRequestUrl = nextUrl;
    return (originalOpen as any).call(this, method, nextUrl, ...args);
  };
  XMLHttpRequest.prototype.send = function(body?: Document | XMLHttpRequestBodyInit | null) {
    try { this.withCredentials = true; } catch { /* native HTTP may own credentials */ }
    const requestUrl = String((this as any).__gachiRequestUrl || '');
    if (requestUrl.includes('/checkin')) {
      this.addEventListener('load', () => {
        if (this.status >= 200 && this.status < 300) {
          Haptics.notification({ type: NotificationType.Success }).catch(() => undefined);
        }
      }, { once: true });
    }
    return originalSend.call(this, body as any);
  };
}

function toBrowserPosition(position: any): any {
  const coords = position && position.coords ? position.coords : {};
  return {
    coords: {
      latitude: Number(coords.latitude),
      longitude: Number(coords.longitude),
      accuracy: Number(coords.accuracy || 0),
      altitude: coords.altitude == null ? null : Number(coords.altitude),
      altitudeAccuracy: coords.altitudeAccuracy == null ? null : Number(coords.altitudeAccuracy),
      heading: coords.heading == null ? null : Number(coords.heading),
      speed: coords.speed == null ? null : Number(coords.speed)
    },
    timestamp: Number(position && position.timestamp ? position.timestamp : Date.now())
  };
}

function positionOptions(options?: PositionOptions) {
  return {
    enableHighAccuracy: !!(options && options.enableHighAccuracy),
    timeout: options && Number.isFinite(options.timeout) ? Number(options.timeout) : 10000,
    maximumAge: options && Number.isFinite(options.maximumAge) ? Number(options.maximumAge) : 0
  };
}

function installGeolocationBridge() {
  if (!isNative || !navigator.geolocation) return;
  const geolocation = navigator.geolocation;

  geolocation.getCurrentPosition = ((success: PositionCallback, error?: PositionErrorCallback | null, options?: PositionOptions) => {
    Geolocation.getCurrentPosition(positionOptions(options))
      .then((position) => success(toBrowserPosition(position)))
      .catch((reason) => {
        if (error) error({ code: 1, message: String(reason && reason.message ? reason.message : reason), PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as any);
      });
  }) as typeof geolocation.getCurrentPosition;

  geolocation.watchPosition = ((success: PositionCallback, error?: PositionErrorCallback | null, options?: PositionOptions) => {
    const localId = nextWatchId++;
    const nativeId = Geolocation.watchPosition(positionOptions(options), (position, reason) => {
      if (reason) {
        if (error) error({ code: 2, message: String(reason.message || reason), PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as any);
        return;
      }
      if (position) success(toBrowserPosition(position));
    });
    nativeWatchIds.set(localId, nativeId);
    return localId;
  }) as typeof geolocation.watchPosition;

  geolocation.clearWatch = ((id: number) => {
    const nativeId = nativeWatchIds.get(Number(id));
    if (!nativeId) return;
    nativeWatchIds.delete(Number(id));
    nativeId.then((value) => Geolocation.clearWatch({ id: value })).catch(() => undefined);
  }) as typeof geolocation.clearWatch;
}

function rewriteLocalAsset(element: Element) {
  for (const attribute of ['src', 'href', 'poster']) {
    const value = element.getAttribute(attribute);
    if (value && value.startsWith('/assets/')) element.setAttribute(attribute, `.${value}`);
  }
}

function installAssetBridge() {
  document.querySelectorAll('[src],[href],[poster]').forEach(rewriteLocalAsset);
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'attributes' && mutation.target instanceof Element) rewriteLocalAsset(mutation.target);
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return;
        rewriteLocalAsset(node);
        node.querySelectorAll('[src],[href],[poster]').forEach(rewriteLocalAsset);
      });
    }
  });
  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ['src', 'href', 'poster']
  });
}

function installSafeAreaStyles() {
  document.documentElement.classList.add('gachi-native');
  const style = document.createElement('style');
  style.textContent = `
    :root {
      --gachi-safe-top: env(safe-area-inset-top, 0px);
      --gachi-safe-right: env(safe-area-inset-right, 0px);
      --gachi-safe-bottom: env(safe-area-inset-bottom, 0px);
      --gachi-safe-left: env(safe-area-inset-left, 0px);
    }
    html.gachi-native body {
      padding-top: var(--gachi-safe-top);
      padding-right: var(--gachi-safe-right);
      padding-bottom: var(--gachi-safe-bottom);
      padding-left: var(--gachi-safe-left);
      box-sizing: border-box;
    }
    html.gachi-keyboard-open body { padding-bottom: 0; }
    .gachi-network-banner {
      position: fixed;
      z-index: 2147483647;
      top: calc(var(--gachi-safe-top) + 10px);
      left: 50%;
      transform: translateX(-50%);
      display: none;
      align-items: center;
      gap: 10px;
      width: min(calc(100% - 32px), 420px);
      padding: 11px 14px;
      border-radius: 12px;
      color: #fff;
      background: rgba(23, 32, 51, .94);
      box-shadow: 0 10px 30px rgba(23, 32, 51, .2);
      font: 600 13px/1.4 -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif;
    }
    .gachi-network-banner[data-visible="true"] { display: flex; }
    .gachi-network-banner button {
      margin-left: auto;
      padding: 5px 9px;
      border: 0;
      border-radius: 8px;
      color: #172033;
      background: #fff;
      font: inherit;
    }
  `;
  document.head.appendChild(style);
}

function ensureNetworkBanner() {
  let banner = document.querySelector('.gachi-network-banner') as HTMLElement | null;
  if (banner) return banner;
  banner = document.createElement('div');
  banner.className = 'gachi-network-banner';
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  banner.innerHTML = '<span>인터넷 연결이 끊겼어요. 저장한 코스는 계속 볼 수 있어요.</span><button type="button">다시 시도</button>';
  banner.querySelector('button')?.addEventListener('click', () => window.location.reload());
  document.body.appendChild(banner);
  return banner;
}

async function updateNetworkState(connected: boolean) {
  const banner = ensureNetworkBanner();
  banner.dataset.visible = connected ? 'false' : 'true';
  document.documentElement.classList.toggle('gachi-offline', !connected);
  window.dispatchEvent(new CustomEvent('gachi:network', { detail: { connected } }));
}

async function installNetworkBridge() {
  const state = await Network.getStatus();
  await updateNetworkState(state.connected);
  Network.addListener('networkStatusChange', (next) => updateNetworkState(next.connected));
}

async function takePhoto(): Promise<string | null> {
  if (!isNative) return null;
  try {
    const photo = await Camera.getPhoto({
      source: CameraSource.Camera,
      resultType: CameraResultType.Uri,
      quality: 88,
      correctOrientation: true,
      saveToGallery: false
    });
    return photo.webPath || null;
  } catch {
    return null;
  }
}

async function attachPhotoToInput(input: HTMLInputElement) {
  const webPath = await takePhoto();
  if (!webPath) return;
  try {
    const response = await fetch(webPath);
    const blob = await response.blob();
    const extension = blob.type.includes('png') ? 'png' : 'jpg';
    const file = new File([blob], `gachi-${Date.now()}.${extension}`, { type: blob.type || 'image/jpeg' });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  } catch {
    input.click();
  }
}

function installCameraBridge() {
  document.addEventListener('click', (event) => {
    const input = event.target instanceof HTMLInputElement ? event.target : null;
    if (!isNative || !input || input.type !== 'file' || !input.hasAttribute('capture')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    attachPhotoToInput(input);
  }, true);
}

async function openExternal(url: string) {
  if (!url) return;
  if (isNative) {
    await Browser.open({ url, presentationStyle: 'popover' });
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}

function isAllowedInternalUrl(parsed: URL) {
  const allowedHosts = new Set([new URL(serverOrigin).host, ...(config.allowedHosts || [])]);
  return allowedHosts.has(parsed.host);
}

function installExternalLinkBridge() {
  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target.closest('a[href]') as HTMLAnchorElement | null : null;
    if (!target) return;
    const href = target.href;
    if (!/^https?:/i.test(href)) return;
    const parsed = new URL(href);
    if (isAllowedInternalUrl(parsed)) return;
    event.preventDefault();
    openExternal(href).catch(() => undefined);
  }, true);

  const nativeOpen = window.open.bind(window);
  window.open = ((url?: string | URL, target?: string, features?: string) => {
    const value = String(url || '');
    if (isNative && /^https?:/i.test(value)) {
      openExternal(value).catch(() => undefined);
      return null;
    }
    return nativeOpen(url as any, target, features);
  }) as typeof window.open;
}

function deepLinkRoute(value: string): string {
  try {
    const parsed = new URL(value);
    const scheme = config.deepLinkScheme || 'gachi';
    let parts = parsed.pathname.split('/').filter(Boolean);
    if (parsed.protocol === `${scheme}:`) parts = [parsed.hostname, ...parts].filter(Boolean);
    if (parsed.protocol.startsWith('http') && !isAllowedInternalUrl(parsed)) return '';
    if (parts[0] === 'course' || parts[0] === 'courses') {
      return `/access?tab=my&profileTab=savedCourses&course=${encodeURIComponent(parts[1] || '')}`;
    }
    if (parts[0] === 'chat') {
      return `/access?tab=chat&conversation=${encodeURIComponent(parts[1] || '')}`;
    }
    if (['signal', 'signals', 'together'].includes(parts[0])) {
      const signal = parts[1] ? `&signal=${encodeURIComponent(parts[1])}` : '';
      return `/access?tab=map&mapMode=zenly&focus=signals${signal}`;
    }
    if (parts[0] === 'meeting') {
      return '/access?tab=map&mapMode=zenly&focus=meeting';
    }
    if (parts[0] === 'access') return `/access${parsed.search}`;
    if (parsed.pathname === '/access') return `/access${parsed.search}`;
  } catch {
    return '';
  }
  return '/access';
}

function openDeepLink(value: string) {
  const route = deepLinkRoute(value);
  if (!route) return;
  sessionStorage.setItem('gachi-mobile-last-deep-link', value);
  const event = new CustomEvent('gachi:deep-link', {
    cancelable: true,
    detail: { url: value, route }
  });
  window.dispatchEvent(event);
  if (event.defaultPrevented) return;
  const current = `${window.location.pathname}${window.location.search}`;
  if (current !== route) window.location.assign(route);
}

async function registerDeviceToken(token: string) {
  await Preferences.set({ key: 'gachi-push-token', value: token });
  const jwt = localStorage.getItem('tour-on-jwt') || '';
  const body = new URLSearchParams({
    token,
    platform: Capacitor.getPlatform(),
    app_version: '0.1.0',
    locale: navigator.language || 'ko-KR'
  });
  if (jwt) body.set('token_auth', jwt);
  try {
    await fetch('/api/mobile/devices', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        ...(jwt ? { Authorization: `Bearer ${jwt}` } : {})
      },
      body: body.toString()
    });
  } catch {
    // 토큰은 Preferences에 남겨 다음 활성화 때 재전송한다.
  }
  window.dispatchEvent(new CustomEvent('gachi:push-token', { detail: { token } }));
}

async function enablePushNotifications() {
  if (!isNative) return false;
  let permission = await PushNotifications.checkPermissions();
  if (permission.receive === 'prompt') permission = await PushNotifications.requestPermissions();
  if (permission.receive !== 'granted') return false;
  await PushNotifications.register();
  return true;
}

function installPushBridge() {
  PushNotifications.addListener('registration', ({ value }) => registerDeviceToken(value));
  PushNotifications.addListener('registrationError', (error) => {
    window.dispatchEvent(new CustomEvent('gachi:push-error', { detail: error }));
  });
  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    window.dispatchEvent(new CustomEvent('gachi:push-received', { detail: notification }));
  });
  PushNotifications.addListener('pushNotificationActionPerformed', ({ notification }) => {
    const data: any = notification.data || {};
    const target = data.deep_link || data.url
      || (data.course_id ? `gachi://course/${data.course_id}` : '')
      || (data.conversation_id ? `gachi://chat/${data.conversation_id}` : '');
    if (target) openDeepLink(String(target));
  });

  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target.closest('.notification-button') : null;
    if (!target || pushRegistrationStarted) return;
    pushRegistrationStarted = true;
    enablePushNotifications().finally(() => { pushRegistrationStarted = false; });
  }, true);
}

function installBackBridge() {
  App.addListener('backButton', ({ canGoBack }) => {
    const event = new CustomEvent('gachi:back', { cancelable: true });
    window.dispatchEvent(event);
    if (event.defaultPrevented) return;
    if (canGoBack || window.history.length > 1) window.history.back();
    else App.minimizeApp();
  });
}

function installKeyboardBridge() {
  Keyboard.addListener('keyboardWillShow', (info) => {
    document.documentElement.classList.add('gachi-keyboard-open');
    document.documentElement.style.setProperty('--gachi-keyboard-height', `${info.keyboardHeight}px`);
  });
  Keyboard.addListener('keyboardWillHide', () => {
    document.documentElement.classList.remove('gachi-keyboard-open');
    document.documentElement.style.setProperty('--gachi-keyboard-height', '0px');
  });
}

async function restoreAuthPreferences() {
  for (const key of authStorageKeys) {
    const existing = localStorage.getItem(key);
    if (existing) {
      await Preferences.set({ key: `auth:${key}`, value: existing });
      continue;
    }
    const stored = await Preferences.get({ key: `auth:${key}` });
    if (stored.value) localStorage.setItem(key, stored.value);
  }
}

async function persistAuthPreferences() {
  for (const key of authStorageKeys) {
    const value = localStorage.getItem(key);
    if (value) await Preferences.set({ key: `auth:${key}`, value });
    else await Preferences.remove({ key: `auth:${key}` });
  }
}

function installAuthPersistence() {
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') persistAuthPreferences().catch(() => undefined);
  });
  App.addListener('appStateChange', ({ isActive }) => {
    if (!isActive) persistAuthPreferences().catch(() => undefined);
  });
  window.setInterval(() => persistAuthPreferences().catch(() => undefined), 5000);
}

async function initialize() {
  installRequestBridge();
  installGeolocationBridge();
  installAssetBridge();
  installSafeAreaStyles();
  installCameraBridge();
  installExternalLinkBridge();

  if (!isNative) return;

  await restoreAuthPreferences();
  installAuthPersistence();
  installBackBridge();
  installKeyboardBridge();
  installPushBridge();
  await installNetworkBridge();

  App.addListener('appUrlOpen', ({ url }) => openDeepLink(url));
  App.addListener('appStateChange', ({ isActive }) => {
    if (isActive) {
      Network.getStatus().then((state) => updateNetworkState(state.connected));
      Preferences.get({ key: 'gachi-push-token' }).then(({ value }) => {
        if (value) registerDeviceToken(value);
      });
    }
  });

  try {
    await StatusBar.setOverlaysWebView({ overlay: true });
    await StatusBar.setStyle({ style: Style.Dark });
  } catch { /* status bar unavailable */ }

  window.setTimeout(() => SplashScreen.hide().catch(() => undefined), 250);
}

const ready = initialize().catch((error) => {
  console.error('[gachi-mobile] initialization failed', error);
});

window.GachiMobile = {
  isNative,
  ready,
  getCurrentPosition: (options?: PositionOptions) => Geolocation.getCurrentPosition(positionOptions(options)),
  takePhoto,
  enablePushNotifications,
  openExternal,
  resolveServerUrl
};
