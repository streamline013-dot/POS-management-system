<p align="center">
  <img src="logo.png" alt="Print Shop POS logo" width="120">
</p>

<h1 align="center">Print Shop POS</h1>

<p align="center">
  <b>Version 39.2.0</b> · POS for a printing and souvenir business: orders, pre-orders, Quick Log, inventory, costing, cash flow, reports, and an AI assistant.<br>
  Taglish / English · Light and dark mode · Phone, tablet, and desktop · Installable · Works offline
</p>

---

## What is new in v39.2

- When the developer **confirms** a subscription payment, it is **logged automatically in Expenses** (category *Software / Subscription*, from the wallet that matches the payment method). Each payment is logged once on every device; deleting the payment record also removes its automatic expense.
- Removed the large empty space at the end of every page (desktop: small margin; phones: just enough room above the bottom tab bar).

## What was new in v39.1

- **Separate Developer portal** (`/?portal=developer`, or `/developer` on Vercel). Developers sign in there with Google **and a Developer PIN**; the database rules check the PIN session, and the session expires (default 8 hours). Admins and staff use the normal shop login.
- **Front-page Quick Log**: anyone at the shop can log a job on the login page without signing in (protected by a desk code). Signed-in devices move each entry into the Quick Log.
- **Alerts** (🔔) for developers, admins and staff: system reminders from the shop data plus messages you send to everyone, a role, or one person. Urgent alerts pop up; optional desktop notifications and sound.
- **App appearance** (Company Info): colour palette or custom colours, sidebar style, icons-only menu, page width, density, corners, card style, font (7 choices) and size — for the whole shop.
- **Subscription billing** (developer ↔ shop): plan, due date, manual payment methods (GCash, Maya, bank, QR), payment reports, confirmation with receipt numbers, alerts, optional soft lock after the grace period.
- **Update notes / What’s new**, **History** (activity, sign-ins, errors with filters and CSV), **Security** (PIN, session length, who is online, remote sign-out), **access requests** in Team, and a rules check.

## What was new in v39.0

- **Premium redesign**: new design system from the shop logo (sage, terracotta, mustard), Inter font, SVG icons, cleaner cards, tables, and forms, refined dark mode.
- **Sign in with Google (Firebase)** with three roles: **Developer**, **Admin**, **Staff**. Only invited Google accounts can open the shop.
- **Realtime sync** on every device through Firebase Realtime Database (one shared shop, not one copy per account).
- **Developer Console**: feature switches, integrations, database rules generator, announcements, maintenance mode, audit log, error log, data health check, danger zone, system tools.
- **Team & Access** (admin): invite or remove people, and choose which pages Staff can open.
- **Quick Log**: write down jobs to make or that customers want made; they stay pending until you start them, then one tap turns them into an Order, Pre-order, or Quote.
- **Google Drive backup** (replaces Drive sync): manual and daily automatic backups, restore, and restore of the old v37 sync file.
- **Supabase removed.**
- Search / command palette (**Ctrl K** or **/**), Quick Log shortcut (**Q**), screen lock with PIN, deep links (`/#qlog`, `/#enc`) and install shortcuts.
- Bug fixes: see `02_PROJECT_DOCS/REVISION_REPORTS/REVISION_v39.0.0_*.md`.

## Features

| Area | What it does |
|---|---|
| **Encoder** | Multi-item orders with supplies used and waste, extras/discounts, bulk discount, down payment or credit, invoice/receipt (print, PDF, PNG, share) |
| **Quick Log** | Fast capture of jobs (customer requests or own projects), priority and target date, convert to Order / Pre-order / Quote |
| **Pre-orders** | Several products, down payment and extra payments, invoice with progress history, reminders, convert to order |
| **History** | Edit or delete orders (stock is corrected automatically), payments, refunds, status, CSV export (one row per order) |
| **Production board** | New → In progress → Ready → Delivered |
| **Inventory** | Live stock, real-count correction, restock, low-stock alerts, shopping list, forecast |
| **Products** | Cost-based pricing, recipes, designs, pictures, catalog page and PDF |
| **Money** | Wallets and transfers, cash flow ledger, expenses, funds, capital, payroll (optional), tax/BIR (optional) |
| **Reports** | Daily and monthly reports, Daily Closing with cash count, analytics |
| **AI Assistant** | Gemini chat that can read and (with your approval) change data |
| **Team & roles** | Google sign-in, Developer / Admin / Staff, invites, staff page access |
| **Developer Console** | Features, integrations, rules check, security (PIN, sessions, online, remote sign-out), billing, update notes, notices, maintenance, history (activity / sign-ins / errors), data tools, system |
| **Alerts** | Bell with system reminders and team messages, urgent pop-ups, read marks synced per person |
| **Subscription** | Admin page with plan, how to pay, payment reports and history |
| **Front-page Quick Log** | Log a job on the login page without signing in (desk code) |
| **Appearance** | Palette, custom colours, sidebar, menu, width, density, corners, cards, font, size |
| **Backups** | JSON download/share, automatic copies on the device, Google Drive backups |

## Project structure

```
01_APP/
├── index.html              # the whole app (HTML + CSS + JS, no build step)
├── app-config.js           # YOUR settings: Firebase config, developer emails, shop ID (edit this)
├── app-config.example.js   # documented example of app-config.js
├── sw.js                   # service worker (offline, install, caches the Firebase SDK)
├── manifest.webmanifest    # PWA manifest (name, colors, icons, shortcuts)
├── vercel.json             # Vercel headers / caching, /developer redirect
├── .vercelignore           # files that are not deployed
├── fonts/                  # Inter + optional Appearance fonts (SIL Open Font License, see the OFL files)
├── firebase/
│   └── database.rules.json # rules TEMPLATE (the Developer Console makes the exact rules for you)
├── tests/                  # automated browser tests (not deployed)
├── logo.png, favicon.ico, favicon-32.png, icon-*.png, apple-touch-icon.png
├── README.md
└── AGENTS.md               # notes for AI coding tools
```

There is **no build step and no npm dependencies** — it is a static site.

## Two modes

| | Local mode | Cloud mode |
|---|---|---|
| When | `app-config.js` has no Firebase config | Firebase config filled in |
| Login | none | Shop login (Google) for admin/staff · Developer portal (Google + Developer PIN) |
| Roles | one user (full access) | Developer / Admin / Staff |
| Data | this browser only | shared, realtime on every device, works offline |

## Setup (short version)

Full beginner guides are in `03_SETUP_GUIDES/` — start with `00_START_HERE.md`.

1. Create a Firebase project, a web app, a **Realtime Database**, and turn on **Google** sign-in.
2. Put the Firebase config and your Gmail (as developer) in `app-config.js`.
3. Upload to GitHub and deploy on Vercel.
4. Add the Vercel domain to Firebase **Authentication → Settings → Authorized domains**.
5. Open `/?portal=developer`, sign in with your Gmail, create your **Developer PIN**, then copy the database rules (Developer Console → Integrations, or the rules screen) and **Publish** them in Firebase.
6. Invite the admin and staff from **Team & Access**.
7. Optional: turn on the front-page Quick Log (Quick Log page → Front-page Quick Log) and set a desk code; set up Subscription billing in Developer Console → Billing.

**Upgrading from v39.0.0:** deploy, then open the Developer portal. It shows “Publish the database rules” — copy, publish in Firebase, tap “Try again”, and create your Developer PIN. Admins and staff keep working with the old rules until then, but the new features need the new rules.

## Deploy (GitHub → Vercel)

- **Framework preset:** Other · **Build command:** empty · **Output directory:** empty (root of `01_APP`).
- Push to `main` to redeploy. The page, `app-config.js`, and `sw.js` are always fetched fresh.
- If you change icons, fonts, or the manifest, also change `CACHE` in `sw.js`.

## Where the data lives

- **Cloud mode:** in your Firebase Realtime Database under `shops/<shopId>`, plus a working copy in each browser (so it works offline).
- **Local mode:** only in the browser of that device.
- The Gemini API key always stays on the device that uses it (never synced, never in backups).
- Keep backups: **Setup → Backup** (JSON) and **Google Drive Backup**.

## Security notes

- The Firebase web config in `app-config.js` is not a secret; access is controlled by Google sign-in **and the database rules**. Publish the rules from the app.
- Roles are enforced by the database rules for membership, invites, configuration, policy, logs, alerts, billing and the developer session. Inside the shop data, every member can write (staff restrictions on pages are enforced in the app). See `02_PROJECT_DOCS/PROJECT_MANAGEMENT/RISKS.md`.
- Developer access needs Google sign-in **plus** an unexpired Developer PIN session that the database rules check. The PIN hash cannot be read by anyone; use 6–12 characters with letters and numbers.
- The front-page Quick Log is write-only for people who are not signed in: the rules check the desk code and the allowed fields; nobody signed out can read shop data.
- The subscription soft lock is app-level (the shop data stays readable and writable by the rules).
- Never commit backups (`*-backup-*.json`), `.env` files, service-account keys, or API keys.

## Tests

See `tests/README.md`. They run the app in Chrome with a mock Firebase (sign-in + database + the generated rules).
