// MOCK firebase-auth (test only): accounts come from window.__mockAccounts, the next sign-in uses window.__mockNextUser
const G = globalThis;
const ST = G.__mockAuth || (G.__mockAuth = { user: null, ls: [] });
try { const u = JSON.parse(localStorage.getItem('__mock_user') || 'null'); if (u) ST.user = u; } catch (e) {}
const accounts = () => G.__mockAccounts || JSON.parse(localStorage.getItem('__mock_accounts') || '{}');
const emit = () => ST.ls.forEach((cb) => setTimeout(() => cb(ST.user ? { ...ST.user } : null), 0));
export class GoogleAuthProvider { setCustomParameters() {} addScope() {} }
export const getAuth = (app) => ({ app, currentUser: ST.user });
export const useDeviceLanguage = () => {};
export const getRedirectResult = async () => null;
export const onAuthStateChanged = (auth, cb) => { ST.ls.push(cb); setTimeout(() => cb(ST.user ? { ...ST.user } : null), 5); return () => { ST.ls = ST.ls.filter((x) => x !== cb); }; };
export const signInWithPopup = async () => {
  const key = G.__mockNextUser || localStorage.getItem('__mock_next') || Object.keys(accounts())[0];
  if (key === '__closed') { const e = new Error('closed'); e.code = 'auth/popup-closed-by-user'; throw e; }
  const a = accounts()[key]; if (!a) throw Object.assign(new Error('no account ' + key), { code: 'auth/internal-error' });
  ST.user = { uid: a.uid, email: a.email, displayName: a.displayName, photoURL: a.photoURL || '', emailVerified: true };
  localStorage.setItem('__mock_user', JSON.stringify(ST.user)); emit(); return { user: { ...ST.user } };
};
export const signInWithRedirect = signInWithPopup;
export const signOut = async () => { ST.user = null; localStorage.removeItem('__mock_user'); emit(); };
export const browserLocalPersistence = {}; export const indexedDBLocalPersistence = {};
