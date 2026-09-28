import { Platform } from 'react-native';
import { apiUrl } from './config';
import app from '../../app.json';

/** Send one crash report; never throws, since it runs while the app is already failing. */
export function reportError(error: unknown, fatal = false): void {
  const e = error instanceof Error ? error : new Error(String(error));
  fetch(apiUrl('/api/v1/client-errors'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: `${e.name}: ${e.message}`.slice(0, 500),
      stack: (e.stack ?? '').slice(0, 4000),
      fatal,
      platform: Platform.OS,
      version: app.expo.version,
    }),
  }).catch(() => {});
}

/** Report uncaught JS errors, then let React Native handle them as before. */
export function installCrashReporting(): void {
  if (__DEV__) return;
  const previous = ErrorUtils.getGlobalHandler();
  ErrorUtils.setGlobalHandler((error, isFatal) => {
    reportError(error, !!isFatal);
    previous(error, isFatal);
  });
}
