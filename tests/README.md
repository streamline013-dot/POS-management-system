# Automated tests (not deployed)

These open the real app in Chrome with Playwright. Firebase is replaced by a small **mock** (`mockfb/`) that keeps the
database in the browser and enforces the **same database rules the app generates** (including transactions and
server time), so the shop login, the Developer portal + Developer PIN, roles, invites, realtime sync, the front-page
Quick Log, alerts, billing, maintenance mode, and the rules can be tested without a real Firebase project.

## Run

```bash
pip install playwright        # once
python -m playwright install chromium   # once
cd 01_APP && python3 -m http.server 8039     # terminal 1
python3 tests/test_views.py http://localhost:8039 ./shots/views   # terminal 2: every page + Developer Console tab, light + dark
python3 tests/test_cloud.py http://localhost:8039 ./shots/cloud   # portals, PIN, roles, rules, front-page Quick Log, alerts, billing, appearance (~6 min)
python3 tests/test_buttons.py http://localhost:8039 index.html  # every rendered button has a working handler
```

Set `CHROME=/path/to/chrome` to use an installed Chrome instead of Playwright's Chromium.

## What the mock does not cover
- Real Google accounts, popups, and redirects.
- Real Firebase network behaviour (offline queueing, reconnects, server timestamps and server time offset from Google).
- `onDisconnect` (presence clean-up when a device drops) is only recorded, not run.
- Two browsers on different computers (the test uses two tabs that share the mock database).
- The real rules engine (the mock evaluator supports the expressions used by this app only).

Always finish with the manual checks in `03_SETUP_GUIDES/03_Firebase_Setup.md` → "How to confirm it worked".
