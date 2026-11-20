// MOCK firebase-database (test only) with a small Realtime Database rules evaluator.
// The tree lives in localStorage.__mock_db; rules in localStorage.__mock_rules (JSON text).
const G = globalThis;
const auth = () => (G.__mockAuth && G.__mockAuth.user) ? { uid: G.__mockAuth.user.uid, token: { email: G.__mockAuth.user.email, email_verified: true } } : null;
const load = () => { try { return JSON.parse(localStorage.getItem('__mock_db') || '{}') || {}; } catch (e) { return {}; } };
const save = (t) => localStorage.setItem('__mock_db', JSON.stringify(t));
const rulesTree = () => { try { return JSON.parse(localStorage.getItem('__mock_rules') || 'null'); } catch (e) { return null; } };
const segs = (p) => String(p || '').split('/').filter(Boolean);
const clone = (v) => v === undefined ? null : JSON.parse(JSON.stringify(v));
const getAt = (t, a) => { let n = t; for (const k of a) { if (n == null || typeof n !== 'object') return null; n = n[k]; } return n === undefined ? null : n; };
const prune = (v) => { if (v && typeof v === 'object') { for (const k of Object.keys(v)) { v[k] = prune(v[k]); if (v[k] == null) delete v[k]; } return Object.keys(v).length ? v : null; } return v === undefined ? null : v; };
const TS = { '.sv': 'timestamp' };
const fixTs = (v) => { if (v && typeof v === 'object') { if (v['.sv'] === 'timestamp') return Date.now(); const o = Array.isArray(v) ? [] : {}; Object.keys(v).forEach((k) => { o[k] = fixTs(v[k]); }); return o; } return v; };
const setAt = (t, a, v) => { if (!a.length) return prune(clone(v)) || {}; const root = t || {}; let n = root; for (let i = 0; i < a.length - 1; i++) { if (n[a[i]] == null || typeof n[a[i]] !== 'object') n[a[i]] = {}; n = n[a[i]]; } if (v == null) delete n[a[a.length - 1]]; else n[a[a.length - 1]] = clone(v); return prune(root) || {}; };
class RS { constructor(t, a) { this.t = t; this.a = a; }
  child(p) { return new RS(this.t, this.a.concat(segs(p))); }
  val() { const v = getAt(this.t, this.a); if (v && typeof v === 'object') throw new Error('val() on object'); return v; }
  exists() { return getAt(this.t, this.a) != null; }
  hasChildren(ks) { const v = getAt(this.t, this.a); if (!v || typeof v !== 'object') return false; return (ks || Object.keys(v)).every((k) => v[k] != null); }
  hasChild(k) { return this.child(k).exists(); }
  isString() { return typeof getAt(this.t, this.a) === 'string'; }
  isNumber() { return typeof getAt(this.t, this.a) === 'number'; }
  isBoolean() { return typeof getAt(this.t, this.a) === 'boolean'; } }
const ev = (expr, ctx) => { if (expr === true || expr === false) return expr; try { const f = new Function('auth', 'root', 'data', 'newData', 'now', 'V', 'with(V){return (' + String(expr).replace(/\.replace\(/g, '.replaceAll(') + ')}'); return !!f(ctx.auth, ctx.root, ctx.data, ctx.newData, Date.now(), ctx.V); } catch (e) { return false; } };
// walk the rule tree along path a; returns list of {node, depth, V}
const walk = (a) => { const R = rulesTree(); if (!R) return null; let n = R.rules; const out = [{ node: n, depth: 0, V: {} }]; let V = {};
  for (let i = 0; i < a.length; i++) { if (!n) break; let nx = n[a[i]]; if (nx === undefined) { const w = Object.keys(n).find((k) => k[0] === '$'); if (w) { V = { ...V, [w]: a[i] }; nx = n[w]; } } n = nx; if (n) out.push({ node: n, depth: i + 1, V: { ...V } }); else break; }
  return out; };
const canRead = (a) => { const W = walk(a); if (!W) return true; const before = load(); for (const w of W) { if (w.node['.read'] !== undefined && ev(w.node['.read'], { auth: auth(), root: new RS(before, []), data: new RS(before, a.slice(0, w.depth)), newData: null, V: w.V })) return true; } return false; };
const validateAll = (before, after, a) => { // validate at ancestors on the rule path and every written node below
  const W = walk(a) || []; for (const w of W) { const p = a.slice(0, w.depth); if (w.node['.validate'] !== undefined && getAt(after, p) != null && !ev(w.node['.validate'], { auth: auth(), root: new RS(before, []), data: new RS(before, p), newData: new RS(after, p), V: w.V })) return false; }
  const below = (node, p, V) => { const v = getAt(after, p); if (v == null || typeof v !== 'object' || !node) return true; for (const k of Object.keys(v)) { let rn = node[k], V2 = V; if (rn === undefined) { const w = Object.keys(node).find((x) => x[0] === '$'); if (w) { rn = node[w]; V2 = { ...V, [w]: k }; } } if (rn) { const cp = p.concat(k); if (rn['.validate'] !== undefined && getAt(after, cp) != null && !ev(rn['.validate'], { auth: auth(), root: new RS(before, []), data: new RS(before, cp), newData: new RS(after, cp), V: V2 })) return false; if (!below(rn, cp, V2)) return false; } } return true; };
  const last = W[W.length - 1]; return last && last.depth === a.length ? below(last.node, a, last.V) : true; };
const canWrite = (before, after, a) => { const W = walk(a); if (!W) return true; let ok = false; for (const w of W) { if (w.node['.write'] !== undefined && ev(w.node['.write'], { auth: auth(), root: new RS(before, []), data: new RS(before, a.slice(0, w.depth)), newData: new RS(after, a.slice(0, w.depth)), V: w.V })) { ok = true; break; } } return ok && validateAll(before, after, a); };
const deny = (p) => Object.assign(new Error('PERMISSION_DENIED: Permission denied at ' + p), { code: 'PERMISSION_DENIED' });
const LS = G.__mockDbL || (G.__mockDbL = []);
const notify = () => { const t = load(); LS.slice().forEach((l) => { if (!canRead(l.a)) { LS.splice(LS.indexOf(l), 1); if (l.err) l.err(deny(l.a.join('/'))); return; } const v = JSON.stringify(getAt(t, l.a)); if (v !== l.last) { l.last = v; l.cb(snap(t, l.a)); } }); };
window.addEventListener('storage', (e) => { if (e.key === '__mock_db') notify(); });
const snap = (t, a, lim) => { let v = clone(getAt(t, a)); if (lim && v && typeof v === 'object') { const ks = Object.keys(v).sort().slice(-lim); const o = {}; ks.forEach((k) => { o[k] = v[k]; }); v = o; } return { val: () => v, exists: () => v != null, key: a[a.length - 1] || null }; };
export const getDatabase = (app, url) => ({ app, url });
export const ref = (db, p) => ({ db, path: segs(p) });
export const child = (r, p) => ({ db: r.db, path: r.path.concat(segs(p)) });
export const limitToLast = (n) => ({ lim: n });
export const query = (r, ...c) => ({ ...r, lim: (c.find((x) => x && x.lim) || {}).lim });
export const serverTimestamp = () => ({ ...TS });
export const get = async (r) => { await 0; if (r.path.join('/') === '.info/connected') return snap({ '.info': { connected: true } }, ['.info', 'connected']); if (!canRead(r.path)) throw deny(r.path.join('/')); return snap(load(), r.path, r.lim); };
const writeMany = async (pairs) => { await 0; const before = load(); let after = clone(before); for (const [a, v] of pairs) after = setAt(after, a, v == null ? null : fixTs(v)); for (const [a] of pairs) if (!canWrite(before, after, a)) throw deny(a.join('/')); save(after); notify(); };
export const set = (r, v) => writeMany([[r.path, v]]);
export const remove = (r) => writeMany([[r.path, null]]);
export const update = (r, obj) => writeMany(Object.keys(obj).map((k) => [r.path.concat(segs(k)), obj[k]]));
let pc = 0; export const push = (r, v) => { const k = '-M' + Date.now().toString(36) + (pc++).toString(36).padStart(4, '0'); const p = writeMany([[r.path.concat(k), v]]); p.key = k; return p; };
export const onValue = (r, cb, err) => { const a = r.path; if (a.join('/') === '.info/connected') { setTimeout(() => cb(snap({ '.info': { connected: true } }, ['.info', 'connected'])), 0); return () => {}; }
  if (a.join('/') === '.info/serverTimeOffset') { setTimeout(() => cb(snap({ '.info': { serverTimeOffset: 0 } }, ['.info', 'serverTimeOffset'])), 0); return () => {}; }
  if (!canRead(a)) { setTimeout(() => err && err(deny(a.join('/'))), 0); return () => {}; }
  const l = { a, cb, err, last: undefined }; LS.push(l); setTimeout(() => { const t = load(); l.last = JSON.stringify(getAt(t, a)); cb(snap(t, a)); }, 0); return () => { const i = LS.indexOf(l); if (i >= 0) LS.splice(i, 1); }; };

// transactions run atomically here (single thread): read, call the update function, write if it returned a value
export const runTransaction = async (r, fn) => { await 0; if (!canRead(r.path)) throw deny(r.path.join('/')); const before = load(); const cur = clone(getAt(before, r.path)); const res = fn(cur);
  if (res === undefined) return { committed: false, snapshot: snap(before, r.path) }; await writeMany([[r.path, res]]); return { committed: true, snapshot: snap(load(), r.path) }; };
// onDisconnect: remembered so a test can see it was registered
export const onDisconnect = (r) => { const rec = G.__mockOD || (G.__mockOD = []); return { remove: () => { rec.push(['remove', r.path.join('/')]); return Promise.resolve(); }, set: (v) => { rec.push(['set', r.path.join('/'), v]); return Promise.resolve(); }, cancel: () => Promise.resolve() }; };
