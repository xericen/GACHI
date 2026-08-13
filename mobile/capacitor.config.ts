import type { CapacitorConfig } from '@capacitor/cli';
import { KeyboardResize, KeyboardStyle } from '@capacitor/keyboard';

const config: CapacitorConfig = {
  appId: 'com.wizide.gachi',
  appName: 'GACHI',
  webDir: 'www',
  ios: {
    contentInset: 'always',
    scrollEnabled: true,
    allowsLinkPreview: false
  },
  plugins: {
    CapacitorCookies: {
      enabled: true
    },
    CapacitorHttp: {
      enabled: true
    },
    Keyboard: {
      resize: KeyboardResize.Native,
      style: KeyboardStyle.Light,
      resizeOnFullScreen: true
    },
    SplashScreen: {
      launchAutoHide: false,
      backgroundColor: '#FFFFFF',
      showSpinner: false
    },
    StatusBar: {
      overlaysWebView: true,
      style: 'dark',
      backgroundColor: '#FFFFFF'
    }
  }
};

export default config;
