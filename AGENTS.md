# Notes for AI coding tools — Print Shop POS v39.2

## Shape of the app
- Static PWA. `index.html` holds everything (CSS + JS in `<style>`/`<script>` blocks). No build step.
- Core block exposes `window.POS` (`P`): state `P.S`, derived `P.D`, encoder draft `P.E`, `P.render()`, `P.save()`,
  registries `P.NAV`, `P.VIEWS`, `P.ACT`, `P.HOOKS` (`start, save, fill, ledger, alerts, pins, after, beforeSave, afterSave, del`,
  plus v39.1: `cloudListen, cloudStop, sysAlerts`). `P.alertsData()` returns the core alert data (stock, deadlines, module pills).
- Modules extend the app by wrapping views (`const _v=VIEWS.x; VIEWS.x=()=>…_v()…`), pushing hooks, and adding `ACT` handlers.
  Keep this pattern; do not rewrite earlier modules.
- UI strings: `L('Tagalog','English')`. A translation layer also rewrites Tagalog text to English at render time when `S.set.lang==='en'`.
  Mark user data with `data-nt` so it is never translated. NAV labels are static English strings.
- Clicks: `data-a="action:arg1:arg2"` → `ACT.action(arg1,arg2)`. Inputs: `data-b` (state path), `data-e` (encoder), `data-f` (filters).

## Modules (near the end of index.html, in this order)
1. **UI shell** (`P.UI`: icons, `openPop(btn, html, cls, width)`, `P.modal`, command palette, account menu).
2. **CLOUD** (`P.cloud`): two doors — shop login and the Developer portal (`?portal=developer`) with a Developer PIN session
   (`shops/<shopId>/devkey`, `devsess`, checked by the rules). Gate screens, roles, realtime sync under `shops/<shopId>/d`,
   config, policy, team (invites, access requests, presence, remote sign-out), audit/error/sign-in logs, rules generator, screen lock.
   Other modules attach database listeners with `HOOKS.cloudListen.push((db, ref, A) => unsubscribe)`.
3. **Appearance** (`P.ui`, `S.set.ui`, Company Info card; cached per device and published to `pub/theme`).
4. **Google Drive backup** (`P.gdrive`).
5. **Quick Log** (`S.qlog`, view `qlog`, `P.qlogAdd`).
6. **Front-page Quick Log** (`P.frontQL`; public inbox `qlin`, desk code in `qlsec`, settings in `pub/ql`).
7. **Team & Access** (view `team`).
8. **Alerts** (`P.alerts`, view `alerts`; buckets `alerts/{all,admin,staff,dev}`, `alerts/u/<uid>`, read marks `ar/<uid>`).
9. **Billing** (`P.bill`, view `bill`, Developer Console tab; `bill`, `billproof`, `billgate`). Confirmed payments flagged `xl` become
   shop expenses `S.cash` id `bill-<paymentId>` (category `soft`), remembered in `S.set.billLogged` (`P.billExpense`).
10. **Update notes** (`P.updates`, view `upd`, Developer Console tab; `upd`).
11. **Developer Console** (view `dev`: overview, features, integrations, security, billing, updates, notice, history, data, system).
12. Stylesheets: `<style id="v39-layer">` then `<style id="v391-layer">` (last; put new component styles there).

## Rules of thumb
- Every write to app data goes through `P.save()`; realtime sync sends only changed pieces.
- Never store secrets in the shop data, `app-config.js`, or backups. The Gemini key stays in `localStorage` (`pos_ai_key`).
- Any new database path needs a rule in `P.cloud.rules()`; then the developer must copy and publish the rules again.
- Developer privileges in the rules require `devsess/<uid>/exp > now`; never add a shortcut that skips it.
- New class names: check they do not collide with v38 classes (e.g. `.kb`, `.ck`, `.tw`, `input.sm` already exist).
- Bump `VERSION` in the build, `CACHE` in `sw.js`, the release notes in the updates module, and the docs in
  `02_PROJECT_DOCS` and `03_SETUP_GUIDES` for every release.
