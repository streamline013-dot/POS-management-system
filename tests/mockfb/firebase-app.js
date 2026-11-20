// MOCK firebase-app (test only)
const apps = globalThis.__mockApps || (globalThis.__mockApps = []);
export const getApps = () => apps.slice();
export const initializeApp = (options, name = '[DEFAULT]') => { const a = { name, options }; apps.push(a); return a; };
export const getApp = (n) => apps.find((a) => a.name === (n || '[DEFAULT]'));
export const SDK_VERSION = 'mock';
